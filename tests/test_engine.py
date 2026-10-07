"""Tests du moteur Job Hunter. Lancer depuis la racine : python3 -m unittest discover -s tests -v

Aucun réseau : les sources sont testées sur des pages HTML fictives (tests/fixtures/html/).
Le test de bout en bout réseau est tests/live_smoke.py (manuel).
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from jobhunter import cli, config, normalize as N, scoring, storage, yamlmini  # noqa: E402
from jobhunter.sources import base, france_travail, hellowork, linkedin, test as test_source  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")


def read(*p):
    with open(os.path.join(FIX, *p), encoding="utf-8") as f:
        return f.read()


class TestYaml(unittest.TestCase):
    def test_kit_example_same_as_pyyaml(self):
        mini = yamlmini.load_file(os.path.join(ROOT, "config", "kit.example.yml"), force_mini=True)
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML absent")
        with open(os.path.join(ROOT, "config", "kit.example.yml"), encoding="utf-8") as f:
            self.assertEqual(mini, yaml.safe_load(f))

    def test_candidate_example(self):
        d = yamlmini.load_file(os.path.join(ROOT, "config", "candidate.example.yml"), force_mini=True)
        self.assertIn("keywords", d)
        self.assertIsInstance(d["education"]["degrees"], list)
        self.assertEqual(d["criteria"]["remote"]["priority"], "required")
        try:
            import yaml
            with open(os.path.join(ROOT, "config", "candidate.example.yml"), encoding="utf-8") as f:
                self.assertEqual(d, yaml.safe_load(f))
        except ImportError:
            pass

    def test_subset(self):
        d = yamlmini.load("a:\n  - x: 1\n    y: [a, 'b c']\n  - z\nb: {m: 2}\nc: \"t # x\" # com\n", force_mini=True)
        self.assertEqual(d, {"a": [{"x": 1, "y": ["a", "b c"]}, "z"], "b": {"m": 2}, "c": "t # x"})


class TestNormalize(unittest.TestCase):
    def test_contract(self):
        cases = {"CDI": "cdi", "Contrat à durée déterminée": "cdd", "Apprentissage": "alternance",
                 "Stage de fin d'études": "stage", "Indépendant": "freelance", "Intérim": "interim",
                 "Profession libérale": "freelance", "": "autre", "Bénévolat": "autre"}
        for raw, want in cases.items():
            self.assertEqual(N.normalize_contract(raw), want, raw)

    def test_remote(self):
        cases = {"Télétravail partiel": "hybrid", "2 jours de télétravail": "hybrid", "Full remote": "full",
                 "Télétravail total": "full", "Pas de télétravail": "none", "": "unknown"}
        for raw, want in cases.items():
            self.assertEqual(N.normalize_remote(raw), want, raw)

    def test_url_tracking_removed(self):
        u = N.normalize_url("https://Example.org/job/1?utm_source=x&id=3&trk=y&refId=z")
        self.assertEqual(u, "https://example.org/job/1?id=3")

    def test_invalid(self):
        with self.assertRaises(N.InvalidOffer):
            N.normalize_offer({"title": "x"}, "test")
        with self.assertRaises(N.InvalidOffer):
            N.normalize_offer({"url": "https://a.b"}, "test")

    def test_description_truncated(self):
        long = "Phrase. " * 400
        self.assertLessEqual(len(N.truncate_description(long)), N.DESCRIPTION_MAX)


class TestDedup(unittest.TestCase):
    def test_pairs(self):
        pairs = json.loads(read("dedup-pairs.json"))
        self.assertGreaterEqual(len(pairs), 20)
        for p in pairs:
            a, b = p["a"], p["b"]
            same = N.offer_id(a["company"], a["title"], a["location"]) == N.offer_id(b["company"], b["title"], b["location"])
            self.assertEqual(same, p["same"], "%s : %s / %s" % (p["why"], a, b))


class StoreCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "offers.csv")
        self.store = storage.Store(storage.CsvBackend(self.path))
        self.store.init()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def offer(self, **kw):
        base_ = {"title": "Data Analyst (H/F)", "company": "Acme", "location": "Lyon (69)", "contract": "CDI",
                 "url": "https://example.org/1", "description": ""}
        base_.update(kw)
        return N.normalize_offer(base_, kw.pop("source", "france_travail") if "source" in kw else "france_travail")


class TestCsvStore(StoreCase):
    def test_bom_and_header(self):
        with open(self.path, "rb") as f:
            self.assertTrue(f.read().startswith(b"\xef\xbb\xbf" + ",".join(N.FIELDS).encode()))

    def test_upsert_and_dedup(self):
        k, oid = self.store.upsert(self.offer())
        self.assertEqual(k, "created")
        k2, oid2 = self.store.upsert(N.normalize_offer({"title": "data analyst", "company": "ACME",
                                                         "location": "Lyon", "url": "https://other.org/9",
                                                         "salary": "40k"}, "hellowork"))
        self.assertEqual((k2, oid2), ("updated", oid))
        row = self.store.get(oid)
        self.assertIn("hellowork:https://other.org/9", row["secondary_sources"])
        self.assertEqual(row["salary"], "40k")
        # même URL, titre modifié : doublon par URL
        k3, oid3 = self.store.upsert(self.offer(title="Data Analyst confirmé"))
        self.assertEqual(oid3, oid)
        self.store.save()
        again = storage.Store(storage.CsvBackend(self.path)).load()
        self.assertEqual(len(again.rows), 1)

    def test_status_and_detected_preserved(self):
        _, oid = self.store.upsert(self.offer(), detected_at="2026-01-01T08:00:00+01:00")
        self.store.update_status(oid, "applied")
        self.store.upsert(N.normalize_offer({"title": "Data Analyst", "company": "Acme", "location": "Lyon",
                                             "url": "https://x.org/2"}, "linkedin"), detected_at="2026-02-01T08:00:00+01:00")
        row = self.store.get(oid)
        self.assertEqual(row["status"], "applied")
        self.assertEqual(row["detected_at"], "2026-01-01T08:00:00+01:00")
        with self.assertRaises(storage.StorageError):
            self.store.update_status(oid, "pas-un-statut")

    def test_atomic_write_keeps_file_on_error(self):
        self.store.upsert(self.offer())
        self.store.save()
        before = open(self.path, encoding="utf-8-sig").read()
        orig = os.replace

        def boom(*a):
            raise OSError("disque plein simulé")
        os.replace = boom
        try:
            self.store.upsert(self.offer(title="Autre poste", url="https://example.org/2"))
            with self.assertRaises(OSError):
                self.store.save()
        finally:
            os.replace = orig
        self.assertEqual(open(self.path, encoding="utf-8-sig").read(), before)
        self.assertEqual([f for f in os.listdir(self.tmp) if f.startswith(".offers-")], [])

    def test_bad_header_refused(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("a,b\n")
        with self.assertRaises(storage.StorageError):
            storage.Store(storage.CsvBackend(self.path)).load()

    def test_performance_500(self):
        import time
        t = time.time()
        for i in range(500):
            self.store.upsert(self.offer(title="Poste %d" % i, url="https://example.org/p/%d" % i))
        self.store.save()
        self.assertLess(time.time() - t, 5)


class FakeAirtable:
    """Imite l'API Airtable en mémoire pour tester le backend sans réseau."""

    def __init__(self):
        self.records = {}
        self.n = 0
        self.calls = []

    def __call__(self, req, timeout=30):
        method, url = req.get_method(), req.full_url
        body = json.loads(req.data.decode()) if req.data else None
        self.calls.append((method, url.split("?")[0]))
        if method == "GET" and "/meta/" in url:
            res = {"tables": [{"name": "Offres", "fields": storage.AIRTABLE_FIELDS}]}
        elif method == "GET":
            res = {"records": [{"id": k, "fields": v} for k, v in self.records.items()]}
        elif method == "POST":
            out = []
            for r in body["records"]:
                self.n += 1
                rid = "rec%03d" % self.n
                self.records[rid] = dict(r["fields"])
                out.append({"id": rid, "fields": self.records[rid]})
            res = {"records": out}
        elif method == "PATCH":
            for r in body["records"]:
                self.records[r["id"]].update(r["fields"])
            res = {"records": body["records"]}
        return _Resp(res)


class _Resp:
    def __init__(self, obj):
        self.data = json.dumps(obj).encode()

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestAirtableStore(unittest.TestCase):
    def test_same_behaviour_as_csv(self):
        tmp = tempfile.mkdtemp()
        try:
            fake = FakeAirtable()
            st = storage.Store(storage.AirtableBackend("tok", "appXXXXXXXXXXXXXX", "Offres", os.path.join(tmp, "p"), opener=fake))
            self.assertEqual(st.init(), "exists")
            st.upsert(N.normalize_offer({"title": "Data Analyst", "company": "Acme", "location": "Lyon",
                                         "url": "https://a.org/1"}, "france_travail"))
            st.save()
            self.assertEqual(len(fake.records), 1)
            st2 = storage.Store(storage.AirtableBackend("tok", "appXXXXXXXXXXXXXX", "Offres", os.path.join(tmp, "p"), opener=fake))
            k, oid = st2.upsert(N.normalize_offer({"title": "data analyst (H/F)", "company": "ACME", "location": "Lyon",
                                                   "url": "https://b.org/2"}, "hellowork"))
            self.assertEqual(k, "updated")
            st2.update_score(oid, 77, "ok")
            st2.save()
            self.assertEqual(len(fake.records), 1)
            rec = list(fake.records.values())[0]
            self.assertEqual(rec["score"], 77)
            self.assertIn("hellowork:", rec["secondary_sources"])
            self.assertIn(("PATCH", storage.AIRTABLE_API + "/appXXXXXXXXXXXXXX/Offres"), fake.calls)
        finally:
            shutil.rmtree(tmp)

    def test_missing_token(self):
        with self.assertRaises(storage.StorageError):
            storage.AirtableBackend("", "app1", "Offres", "/tmp/x")


class TestScoring(unittest.TestCase):
    W = {"title_match": 5, "skills_match": 5, "experience_level": 3, "location_remote": 3, "contract": 3,
         "salary": 2, "education": 2}

    def test_full(self):
        self.assertEqual(scoring.compute({k: 10 for k in self.W}, [], self.W, 30), 100)
        self.assertEqual(scoring.compute({k: 0 for k in self.W}, [], self.W, 30), 0)

    def test_unknown_component_is_neutral(self):
        a = scoring.compute({"title_match": 8, "skills_match": 8, "experience_level": 8, "location_remote": 8},
                            [], self.W, 30)
        self.assertEqual(a, 80)

    def test_sparse_information_pulled_to_50(self):
        # titre et lieu seuls : 8/23 des poids connus -> score ramené vers 50
        self.assertEqual(scoring.compute({"title_match": 10, "location_remote": 8}, [], self.W, 30), 80)
        self.assertEqual(scoring.compute({"title_match": 10}, [], self.W, 30), 72)

    def test_hard_cap(self):
        self.assertEqual(scoring.compute({k: 10 for k in self.W}, ["contract"], self.W, 30), 30)

    def test_bounds(self):
        with self.assertRaises(scoring.ScoreError):
            scoring.compute({"title_match": 11}, [], self.W, 30)
        with self.assertRaises(scoring.ScoreError):
            scoring.compute({}, [], self.W, 30)


class TestSources(unittest.TestCase):
    def test_france_travail(self):
        offers = france_travail.parse_list(read("html", "france_travail.html"))
        self.assertEqual(len(offers), 3)
        o = offers[0]
        self.assertEqual((o["title"], o["company"], o["location"], o["contract"]),
                         ("Data analyst (H/F)", "ENTREPRISE FICTIVE", "Villeurbanne (69)", "CDI"))
        self.assertTrue(o["url"].endswith("/offres/recherche/detail/TEST001"))
        self.assertRegex(o["published_at"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(offers[1]["location"], "Lyon 03 (69)")
        self.assertEqual(offers[2]["company"], "")
        self.assertEqual(offers[2]["title"], "Analyste de données & BI")

    def test_france_travail_url(self):
        u = france_travail.search_url("Data Analyst", {"department": "69"}, 1, 7)
        self.assertIn("lieux=69D", u)
        self.assertIn("range=20-39", u)
        self.assertIn("emission=7", u)

    def test_hellowork(self):
        offers = hellowork.parse_list(read("html", "hellowork.html"))
        self.assertEqual(len(offers), 2)
        o = offers[0]
        self.assertEqual((o["title"], o["company"], o["location"], o["contract"]),
                         ("Data Analyst H/F", "Entreprise Fictive", "Lyon 3e - 69", "CDI"))
        self.assertIn("€", o["salary"])
        self.assertEqual(N.normalize_remote(o["remote"]), "hybrid")
        self.assertEqual(offers[1]["salary"], "")

    def test_linkedin(self):
        offers = linkedin.parse_list(read("html", "linkedin.html"))
        self.assertEqual(len(offers), 2)
        o = offers[0]
        self.assertEqual((o["title"], o["company"], o["published_at"]), ("Data Analyst (F/H)", "Entreprise Fictive", "2026-10-07"))
        self.assertNotIn("?", o["url"])

    def test_negatives_and_relative_dates(self):
        self.assertTrue(base.excluded("Lead Data Analyst", ["lead"]))
        self.assertFalse(base.excluded("Leader Price analyste", ["lead"]))
        from datetime import datetime
        d = datetime(2026, 10, 8)
        self.assertEqual(base.relative_date("Publié hier", d), "2026-10-07")
        self.assertEqual(base.relative_date("il y a 2 semaines", d), "2026-09-24")
        self.assertEqual(base.relative_date("Publié il y a plus de 30 jours", d), "")

    def test_test_source_expectations(self):
        kw = {"titles": ["Data Analyst"], "negative": ["senior"],
              "locations": [{"label": "Lyon"}, {"label": "Villeurbanne"}]}
        r = test_source.search(None, kw, {}, 10, root=ROOT)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["requests_used"], 2)
        self.assertEqual(len(r["offers"]), 4)
        valid, ids = [], set()
        for o in r["offers"]:
            try:
                n = N.normalize_offer(o, "test")
            except N.InvalidOffer:
                continue
            valid.append(n)
            ids.add(N.offer_id(n["company"], n["title"], n["location"]))
        self.assertEqual(len(valid), 3)
        self.assertEqual(len(ids), 2)


class TestCliEndToEnd(unittest.TestCase):
    """Un passage complet avec la source de test, dans un dépôt temporaire."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for d in ("config", "data", "tests"):
            os.makedirs(os.path.join(self.tmp, d), exist_ok=True)
        shutil.copytree(os.path.join(FIX), os.path.join(self.tmp, "tests", "fixtures"))
        open(os.path.join(self.tmp, "CLAUDE.md"), "w").close()
        kit = open(os.path.join(ROOT, "config", "kit.example.yml"), encoding="utf-8").read()
        kit = kit.replace("    - france_travail   #", "    - test\n    - france_travail   #")
        kit = kit.replace("  channel: system", "  channel: none")
        with open(os.path.join(self.tmp, "config", "kit.yml"), "w", encoding="utf-8") as f:
            f.write(kit)
        with open(os.path.join(self.tmp, "config", "candidate.yml"), "w", encoding="utf-8") as f:
            f.write("keywords:\n  validated_at: '2026-10-08T10:00:00+02:00'\n  titles: [Data Analyst]\n"
                    "  negative: [senior]\n  locations:\n    - label: Lyon\n    - label: Villeurbanne\n")
        os.environ["JH_ROOT"] = self.tmp

    def tearDown(self):
        os.environ.pop("JH_ROOT", None)
        shutil.rmtree(self.tmp)

    def jh(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.main(list(args))
        return json.loads(buf.getvalue())

    def test_pass(self):
        self.assertEqual(self.jh("init-storage")["result"], "created")
        start = self.jh("run", "start", "--browser", "no")
        run = start["run_id"]
        names = [p["name"] for p in start["plan"] if p["available"]]
        self.assertEqual(names[:1], ["test"])
        res = self.jh("source", "test", "--run", run)
        self.assertEqual((res["received"], res["rejected"], res["created"]), (4, 1, 2))
        batch = self.jh("to-score", "--run", run)["batch"]
        self.assertEqual(len(batch), 2)
        scores = [{"id": o["id"], "components": {"title_match": 10, "skills_match": 9, "contract": 10},
                   "violations": [], "rationale": "Correspond au profil."} for o in batch]
        path = os.path.join(self.tmp, "s.json")
        json.dump(scores, open(path, "w"))
        self.assertTrue(self.jh("apply-scores", "--file", path)["ok"])
        self.jh("source-result", "indeed", "--run", run, "--status", "blocked", "--message", "captcha")
        fin = self.jh("run", "finish", "--run", run)
        self.assertEqual(fin["stats"]["new"], 2)
        self.assertEqual(fin["stats"]["above_threshold"], 2)
        self.assertIsNone(fin["alert"])          # canal « none »
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, fin["log"])))
        summary = open(os.path.join(self.tmp, fin["summary"]), encoding="utf-8").read()
        self.assertIn("2 nouvelles offres", summary)
        # second passage : aucun doublon
        run2 = self.jh("run", "start", "--browser", "no")["run_id"]
        self.assertEqual(self.jh("source", "test", "--run", run2)["created"], 0)
        self.jh("run", "finish", "--run", run2)
        self.assertEqual(self.jh("list", "--limit", "50")["count"], 2)
        # export Excel
        exp = self.jh("export")
        with zipfile.ZipFile(os.path.join(self.tmp, exp["path"])) as z:
            self.assertIn("xl/worksheets/sheet1.xml", z.namelist())
        # statut
        oid = batch[0]["id"]
        self.assertTrue(self.jh("set-status", oid, "applied")["ok"])
        self.assertEqual(self.jh("list", "--status", "applied")["count"], 1)

    def test_refuses_without_keywords(self):
        with open(os.path.join(self.tmp, "config", "candidate.yml"), "w", encoding="utf-8") as f:
            f.write("keywords:\n  titles: [Data Analyst]\n")
        self.jh("init-storage")
        res = self.jh("run", "start")
        self.assertEqual(res["error"], "keywords_not_validated")

    def test_cloud_mode_marks_browser_unavailable(self):
        p = os.path.join(self.tmp, "config", "kit.yml")
        s = open(p, encoding="utf-8").read().replace("  mode: local", "  mode: cloud")
        open(p, "w", encoding="utf-8").write(s)
        plan = self.jh("sources")["sources"]
        by = {x["name"]: x for x in plan}
        self.assertTrue(by["france_travail"]["available"])
        self.assertFalse(by["indeed"]["available"])


if __name__ == "__main__":
    unittest.main()
