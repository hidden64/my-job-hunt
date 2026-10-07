"""Contrat de stockage (docs/STORAGE.md) et ses deux backends : CSV et Airtable.

Toute la logique métier (dédoublonnage, fusion, règles d'upsert) vit dans `Store`. Les backends
ne font que charger et persister des lignes. Ainsi les deux backends se comportent exactement de
la même façon.
"""
import csv
import io
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from . import normalize as N

BOM = "﻿"


def now_iso():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


class StorageError(RuntimeError):
    pass


# --------------------------------------------------------------------------------------------
# Logique commune
# --------------------------------------------------------------------------------------------

class Store:
    """Opérations du contrat. `self.rows` : dict id -> offre (toutes les valeurs en str)."""

    def __init__(self, backend):
        self.backend = backend
        self.rows = None
        self._dirty = set()
        self._created = set()

    # -- cycle de vie --
    def init(self):
        return self.backend.init()

    def load(self):
        if self.rows is None:
            self.rows = {r["id"]: r for r in self.backend.load_all()}
            self._urls = {}
            for r in self.rows.values():
                self._index_urls(r)
        return self

    def save(self):
        if self._dirty:
            changed = [self.rows[i] for i in self._dirty]
            self.backend.persist(self.rows, changed, created_ids=set(self._created))
        self._dirty.clear()
        self._created.clear()

    def _index_urls(self, row):
        self._urls[N.url_key(row["url"])] = row["id"]
        for part in (row.get("secondary_sources") or "").split(";"):
            if ":" in part:
                _, u = part.split(":", 1)
                if u.strip():
                    self._urls[N.url_key(u.strip())] = row["id"]

    # -- lecture --
    def exists(self, offer_id):
        self.load()
        return offer_id in self.rows

    def exists_url(self, url):
        self.load()
        return self._urls.get(N.url_key(url))

    def get(self, offer_id):
        self.load()
        return self.rows.get(offer_id)

    def list(self, status=None, source=None, min_score=None, detected_since=None, limit=None,
             unscored=False, order_by="score"):
        self.load()
        out = list(self.rows.values())
        if status:
            wanted = set(status) if isinstance(status, (list, tuple, set)) else {status}
            out = [r for r in out if r.get("status") in wanted]
        if source:
            out = [r for r in out if r.get("source") == source
                   or ("%s:" % source) in (r.get("secondary_sources") or "")]
        if min_score is not None:
            out = [r for r in out if _int(r.get("score")) is not None and _int(r["score"]) >= min_score]
        if detected_since:
            out = [r for r in out if (r.get("detected_at") or "") >= detected_since]
        if unscored:
            out = [r for r in out if _int(r.get("score")) is None]
        if order_by == "score":
            out.sort(key=lambda r: (_int(r.get("score")) if _int(r.get("score")) is not None else -1,
                                    r.get("detected_at") or ""), reverse=True)
        elif order_by == "detected":
            out.sort(key=lambda r: r.get("detected_at") or "", reverse=True)
        if limit:
            out = out[:limit]
        return out

    def count_new_since(self, since):
        self.load()
        return sum(1 for r in self.rows.values() if (r.get("detected_at") or "") > since)

    # -- écriture --
    def upsert(self, offer, detected_at=None):
        """offer : offre normalisée (normalize_offer). Renvoie ('created'|'updated'|'duplicate', id)."""
        self.load()
        oid = N.offer_id(offer["company"], offer["title"], offer["location"])
        existing_id = oid if oid in self.rows else self.exists_url(offer["url"])
        if existing_id:
            row = self.rows[existing_id]
            changed = False
            if offer["source"] != row["source"]:
                tag = "%s:%s" % (offer["source"], offer["url"])
                current = [p for p in (row.get("secondary_sources") or "").split(";") if p]
                if not any(p.startswith(offer["source"] + ":") for p in current):
                    current.append(tag)
                    row["secondary_sources"] = ";".join(current)
                    changed = True
            # Complète les champs vides sans écraser ce qui est déjà connu.
            for f in ("salary", "published_at", "description"):
                if not row.get(f) and offer.get(f):
                    row[f] = offer[f]
                    changed = True
            for f, unknown in (("remote", "unknown"), ("contract", "autre")):
                if row.get(f) in ("", unknown) and offer.get(f) not in ("", unknown, None):
                    row[f] = offer[f]
                    changed = True
            if changed:
                self._dirty.add(existing_id)
                self._index_urls(row)
                return "updated", existing_id
            return "duplicate", existing_id
        row = {f: "" for f in N.FIELDS}
        row.update({k: ("" if v is None else str(v)) for k, v in offer.items() if k in N.FIELDS})
        row["id"] = oid
        row["detected_at"] = detected_at or now_iso()
        row["status"] = "new"
        row["score"] = ""
        row["score_rationale"] = ""
        self.rows[oid] = row
        self._index_urls(row)
        self._dirty.add(oid)
        self._created.add(oid)
        return "created", oid

    def update_status(self, offer_id, status):
        if status not in N.STATUSES:
            raise StorageError("statut inconnu : %s (valeurs : %s)" % (status, ", ".join(sorted(N.STATUSES))))
        self.load()
        if offer_id not in self.rows:
            return "not_found"
        self.rows[offer_id]["status"] = status
        self._dirty.add(offer_id)
        return "ok"

    def update_score(self, offer_id, score, rationale):
        self.load()
        if offer_id not in self.rows:
            return "not_found"
        score = int(score)
        if not 0 <= score <= 100:
            raise StorageError("score hors bornes : %s" % score)
        self.rows[offer_id]["score"] = str(score)
        self.rows[offer_id]["score_rationale"] = N.clean_text(rationale)
        self._dirty.add(offer_id)
        return "ok"

    def clear_scores(self, statuses=None):
        self.load()
        n = 0
        for oid, r in self.rows.items():
            if statuses and r.get("status") not in statuses:
                continue
            if r.get("score") or r.get("score_rationale"):
                r["score"] = ""
                r["score_rationale"] = ""
                self._dirty.add(oid)
                n += 1
        return n


def _int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------------------------
# Backend CSV
# --------------------------------------------------------------------------------------------

class CsvBackend:
    name = "csv"

    def __init__(self, path):
        self.path = path

    def init(self):
        if os.path.isfile(self.path):
            with open(self.path, encoding="utf-8-sig", newline="") as f:
                header = next(csv.reader(f), [])
            if header != N.FIELDS:
                raise StorageError("en-tête de %s différent du schéma de docs/STORAGE.md" % self.path)
            return "exists"
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._write([])
        return "created"

    def load_all(self):
        if not os.path.isfile(self.path):
            raise StorageError("%s absent : lance l'installation (setup) pour le créer" % self.path)
        with open(self.path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != N.FIELDS:
                raise StorageError("en-tête de %s différent du schéma de docs/STORAGE.md" % self.path)
            return [{k: (v or "") for k, v in row.items() if k in N.FIELDS} for row in reader]

    def persist(self, rows, changed, created_ids=None):
        ordered = sorted(rows.values(), key=lambda r: (r.get("detected_at") or "", r["id"]))
        self._write(ordered)

    def _write(self, rows):
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=N.FIELDS, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in N.FIELDS})
        directory = os.path.dirname(os.path.abspath(self.path))
        fd, tmp = tempfile.mkstemp(prefix=".offers-", suffix=".csv", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(BOM + buf.getvalue())
            os.replace(tmp, self.path)  # écriture atomique
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise


# --------------------------------------------------------------------------------------------
# Backend Airtable
# --------------------------------------------------------------------------------------------

AIRTABLE_API = "https://api.airtable.com/v0"

AIRTABLE_FIELDS = [
    {"name": "id", "type": "singleLineText"},
    {"name": "title", "type": "singleLineText"},
    {"name": "company", "type": "singleLineText"},
    {"name": "location", "type": "singleLineText"},
    {"name": "contract", "type": "singleSelect",
     "options": {"choices": [{"name": c} for c in ["cdi", "cdd", "alternance", "stage", "freelance", "interim", "autre"]]}},
    {"name": "remote", "type": "singleSelect",
     "options": {"choices": [{"name": c} for c in ["none", "hybrid", "full", "unknown"]]}},
    {"name": "salary", "type": "singleLineText"},
    {"name": "url", "type": "url"},
    {"name": "source", "type": "singleSelect",
     "options": {"choices": [{"name": c} for c in ["france_travail", "hellowork", "linkedin", "wttj", "apec",
                                                    "jobteaser", "indeed", "glassdoor", "test"]]}},
    {"name": "secondary_sources", "type": "multilineText"},
    {"name": "published_at", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "detected_at", "type": "dateTime",
     "options": {"dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "client"}},
    {"name": "status", "type": "singleSelect",
     "options": {"choices": [{"name": c} for c in ["new", "seen", "applied", "rejected", "ignored"]]}},
    {"name": "score", "type": "number", "options": {"precision": 0}},
    {"name": "score_rationale", "type": "multilineText"},
    {"name": "description", "type": "multilineText"},
]


class AirtableBackend:
    name = "airtable"

    def __init__(self, token, base_id, table, pending_dir, opener=None):
        if not token:
            raise StorageError("AIRTABLE_API_KEY absent de config/secrets.env (dis « utilise Airtable » pour le configurer)")
        if not base_id:
            raise StorageError("storage.airtable.base_id vide dans config/kit.yml (dis « utilise Airtable » pour créer la base)")
        self.token, self.base_id, self.table = token, base_id, table
        self.pending_dir = pending_dir
        self._open = opener or urllib.request.urlopen
        self._record_ids = {}
        self._last_call = 0.0

    # -- HTTP --
    def _req(self, method, url, body=None):
        wait = 0.22 - (time.time() - self._last_call)   # 5 requêtes / seconde maximum
        if wait > 0:
            time.sleep(wait)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with self._open(req, timeout=30) as resp:
                self._last_call = time.time()
                return json.loads(resp.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as e:
            self._last_call = time.time()
            detail = e.read().decode("utf-8", "ignore")[:300]
            raise StorageError("Airtable %s %s : HTTP %s %s" % (method, url.split("?")[0], e.code, detail))
        except urllib.error.URLError as e:
            raise StorageError("Airtable injoignable : %s" % e.reason)

    def _table_url(self):
        return "%s/%s/%s" % (AIRTABLE_API, self.base_id, urllib.parse.quote(self.table))

    # -- contrat backend --
    def init(self):
        meta = self._req("GET", "%s/meta/bases/%s/tables" % (AIRTABLE_API, self.base_id))
        for t in meta.get("tables", []):
            if t.get("name") == self.table:
                names = {f["name"] for f in t.get("fields", [])}
                missing = [f["name"] for f in AIRTABLE_FIELDS if f["name"] not in names]
                if missing:
                    raise StorageError("table %s : champs manquants %s" % (self.table, ", ".join(missing)))
                return "exists"
        self._req("POST", "%s/meta/bases/%s/tables" % (AIRTABLE_API, self.base_id),
                  {"name": self.table, "fields": AIRTABLE_FIELDS})
        return "created"

    def load_all(self):
        self.replay_pending()
        rows, offset = [], None
        while True:
            q = {"pageSize": "100"}
            if offset:
                q["offset"] = offset
            page = self._req("GET", self._table_url() + "?" + urllib.parse.urlencode(q))
            for rec in page.get("records", []):
                f = rec.get("fields", {})
                if not f.get("id"):
                    continue
                row = {k: ("" if f.get(k) is None else str(f.get(k))) for k in N.FIELDS}
                if row["score"].endswith(".0"):
                    row["score"] = row["score"][:-2]
                self._record_ids[row["id"]] = rec["id"]
                rows.append(row)
            offset = page.get("offset")
            if not offset:
                return rows

    def _fields(self, row):
        out = {}
        for k in N.FIELDS:
            v = row.get(k, "")
            if k == "score":
                out[k] = int(v) if str(v).strip() else None
            elif k in ("published_at", "detected_at", "contract", "remote", "source", "status", "url"):
                out[k] = v or None
            else:
                out[k] = v
        return out

    def persist(self, rows, changed, created_ids=None):
        creates = [r for r in changed if r["id"] not in self._record_ids]
        updates = [r for r in changed if r["id"] in self._record_ids]
        failed = []
        for i in range(0, len(creates), 10):
            batch = creates[i:i + 10]
            try:
                res = self._req("POST", self._table_url(),
                                {"records": [{"fields": self._fields(r)} for r in batch], "typecast": True})
                for rec in res.get("records", []):
                    self._record_ids[rec["fields"]["id"]] = rec["id"]
            except StorageError as e:
                failed.append(("create", batch, str(e)))
        for i in range(0, len(updates), 10):
            batch = updates[i:i + 10]
            try:
                self._req("PATCH", self._table_url(), {"records": [
                    {"id": self._record_ids[r["id"]], "fields": self._fields(r)} for r in batch], "typecast": True})
            except StorageError as e:
                failed.append(("update", batch, str(e)))
        if failed:
            self._queue(failed)
            raise StorageError("%d lot(s) Airtable en échec, mis en file dans data/pending/ : %s"
                               % (len(failed), failed[0][2]))

    # -- file d'attente --
    def _queue(self, failed):
        os.makedirs(self.pending_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        for n, (kind, batch, err) in enumerate(failed):
            with open(os.path.join(self.pending_dir, "%s-%02d.json" % (stamp, n)), "w", encoding="utf-8") as f:
                json.dump({"kind": kind, "rows": batch, "error": err}, f, ensure_ascii=False, indent=1)

    def replay_pending(self):
        if not os.path.isdir(self.pending_dir):
            return 0
        files = sorted(p for p in os.listdir(self.pending_dir) if p.endswith(".json"))
        if not files:
            return 0
        # Il faut connaître les record ids existants pour rejouer des mises à jour.
        existing = {}
        offset = None
        while True:
            q = {"pageSize": "100", "fields[]": "id"}
            if offset:
                q["offset"] = offset
            page = self._req("GET", self._table_url() + "?" + urllib.parse.urlencode(q))
            for rec in page.get("records", []):
                if rec.get("fields", {}).get("id"):
                    existing[rec["fields"]["id"]] = rec["id"]
            offset = page.get("offset")
            if not offset:
                break
        self._record_ids.update(existing)
        done = 0
        for name in files:
            path = os.path.join(self.pending_dir, name)
            with open(path, encoding="utf-8") as f:
                item = json.load(f)
            try:
                self.persist({}, item["rows"])
                os.unlink(path)
                done += 1
            except StorageError:
                break  # on réessaiera au passage suivant
        return done


# --------------------------------------------------------------------------------------------
# Création d'une base Airtable (setup / skill connect)
# --------------------------------------------------------------------------------------------

def airtable_create_base(token, workspace_id, name="Job Hunter", table="Offres", opener=None):
    open_ = opener or urllib.request.urlopen
    body = {"name": name, "workspaceId": workspace_id, "tables": [{"name": table, "fields": AIRTABLE_FIELDS}]}
    req = urllib.request.Request(AIRTABLE_API + "/meta/bases", data=json.dumps(body).encode("utf-8"),
                                 method="POST", headers={"Authorization": "Bearer " + token,
                                                         "Content-Type": "application/json"})
    try:
        with open_(req, timeout=30) as resp:
            res = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise StorageError("création de base refusée : HTTP %s %s" % (e.code, e.read().decode("utf-8", "ignore")[:300]))
    return res.get("id")


def open_store(paths, kit, secrets):
    backend = (kit.get("storage") or {}).get("backend", "csv")
    if backend == "csv":
        rel = kit["storage"]["csv"].get("path") or "data/offers.csv"
        return Store(CsvBackend(paths.p(*rel.split("/"))))
    if backend == "airtable":
        at = kit["storage"]["airtable"]
        return Store(AirtableBackend(secrets.get("AIRTABLE_API_KEY", ""), at.get("base_id", ""),
                                     at.get("table") or "Offres", paths.pending))
    raise StorageError("storage.backend inconnu : %s (csv ou airtable)" % backend)
