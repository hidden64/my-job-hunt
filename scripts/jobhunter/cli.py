"""Interface en ligne de commande du moteur. Chaque commande imprime un objet JSON.

Utilisée par les skills Claude Code (voir .claude/skills/*/SKILL.md). Lancer via `scripts/jh`.
"""
import argparse
import json
import os
import sys
import time

from . import __version__, config, normalize as N, runs, scoring, storage, summary as summ
from .http import Client
from .notify import send_system
from .sources import REGISTRY, SOURCES


def out(obj, code=0):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
    return code


def fail(error, message, **extra):
    d = {"ok": False, "error": error, "message": message}
    d.update(extra)
    return out(d, 1)


class Ctx:
    def __init__(self, require_kit=True):
        self.paths = config.Paths(config.find_root())
        self.kit = config.load_kit(self.paths, required=require_kit)
        self.secrets = config.load_secrets(self.paths)
        self._store = None

    @property
    def store(self):
        if self._store is None:
            self._store = storage.open_store(self.paths, self.kit, self.secrets)
        return self._store

    def candidate(self, required=True):
        return config.load_candidate(self.paths, required=required)


def _brief(r, with_desc=False):
    d = {k: r.get(k, "") for k in ("id", "score", "title", "company", "location", "contract", "remote",
                                   "salary", "status", "source", "published_at", "detected_at", "url",
                                   "score_rationale")}
    if with_desc:
        d["description"] = r.get("description", "")
    return d


# --------------------------------------------------------------------------------------------
# Commandes
# --------------------------------------------------------------------------------------------

def cmd_check(a):
    paths = config.Paths(config.find_root())
    res = {"ok": True, "version": __version__, "python": sys.version.split()[0], "root": paths.root,
           "kit": os.path.isfile(paths.kit), "candidate": os.path.isfile(paths.candidate)}
    problems = []
    if not res["kit"]:
        problems.append("config/kit.yml absent : le kit n'est pas installé")
    try:
        kit = config.load_kit(paths, required=False)
        res["mode"] = kit["execution"]["mode"]
        res["backend"] = kit["storage"]["backend"]
    except Exception as e:  # kit.yml illisible
        problems.append("config/kit.yml illisible : %s" % e)
        kit = None
    if res["candidate"]:
        try:
            cand = config.load_candidate(paths)
            res["keywords_validated"] = config.keywords_validated(cand)
            if not res["keywords_validated"]:
                problems.append("mots-clés non validés (skill keywords)")
        except Exception as e:
            problems.append("config/candidate.yml illisible : %s" % e)
    else:
        res["keywords_validated"] = False
        problems.append("profil absent (skill onboarding)")
    if kit and res["kit"]:
        try:
            st = storage.open_store(paths, kit, config.load_secrets(paths))
            st.load()
            res["offers"] = len(st.rows)
        except Exception as e:
            problems.append("stockage : %s" % e)
    secrets = config.load_secrets(paths)
    res["secrets_present"] = sorted(k for k, v in secrets.items() if v)
    res["problems"] = problems
    res["ready_to_collect"] = not problems
    return out(res)


def cmd_init_storage(a):
    c = Ctx()
    try:
        state = c.store.init()
    except storage.StorageError as e:
        return fail("storage", str(e))
    return out({"ok": True, "backend": c.kit["storage"]["backend"], "result": state})


def cmd_sources(a):
    c = Ctx(require_kit=False)
    browser = None if a.browser == "unknown" else a.browser == "yes"
    return out({"ok": True, "mode": c.kit["execution"]["mode"],
                "sources": runs.plan(c.kit, None, browser)})


def cmd_run_start(a):
    c = Ctx()
    cand = c.candidate()
    if not config.keywords_validated(cand):
        return fail("keywords_not_validated",
                    "Les mots-clés ne sont pas validés : dis « revois mes mots-clés » avant de lancer une collecte.")
    try:
        c.store.load()
    except storage.StorageError as e:
        return fail("storage", str(e))
    browser = None if a.browser == "unknown" else a.browser == "yes"
    rec = runs.start(c.paths, c.kit, cand, browser)
    runs.cleanup_work(c.paths)
    return out({"ok": True, "run_id": rec["run_id"], "mode": rec["mode"], "plan": rec["plan"],
                "work_dir": os.path.relpath(runs.work_dir(c.paths, rec["run_id"]), c.paths.root)})


def _ingest(c, run_id, source, raw_offers, status, requests_used, message, duration, queries):
    received = len(raw_offers)
    rejected, created, updated, dups = 0, [], 0, 0
    reasons = {}
    detected = storage.now_iso()
    for raw in raw_offers:
        try:
            offer = N.normalize_offer(raw, source)
        except N.InvalidOffer as e:
            rejected += 1
            reasons[str(e)] = reasons.get(str(e), 0) + 1
            continue
        kind, oid = c.store.upsert(offer, detected_at=detected)
        if kind == "created":
            created.append(oid)
        elif kind == "updated":
            updated += 1
        else:
            dups += 1
    save_error = None
    try:
        c.store.save()
    except storage.StorageError as e:
        save_error = str(e)
        status = "error"
        message = (message + " ; " if message else "") + save_error
    if reasons:
        message = (message + " ; " if message else "") + "rejetées : " + ", ".join("%s (%d)" % kv for kv in reasons.items())
    res = runs.record_source(c.paths, run_id, source, status, requests_used, message, received, rejected,
                             created, updated, dups, duration, queries)
    res.update({"ok": save_error is None, "source": source, "new_ids": created})
    return res


def cmd_source(a):
    c = Ctx()
    if a.name not in SOURCES:
        return fail("unknown_source", "source inconnue : %s" % a.name)
    meta = SOURCES[a.name]
    if meta["mode"] != "http":
        return fail("browser_source", "%s est une source navigateur : suis sa fiche puis utilise `jh ingest`." % meta["label"])
    if c.kit["execution"]["mode"] not in meta["available_in"]:
        runs.record_source(c.paths, a.run, a.name, "unavailable", message="indisponible en mode %s" % c.kit["execution"]["mode"])
        return out({"ok": True, "source": a.name, "status": "unavailable"})
    cand = c.candidate()
    rec = runs.load_run(c.paths, a.run)
    step = next((s for s in rec["plan"] if s["name"] == a.name), {})
    limit = int(a.limit or step.get("limit") or (c.kit["sources"].get("limits") or {}).get(a.name, meta["default_limit"]))
    d = c.kit["sources"].get("http_delay_seconds") or {"min": 1, "max": 3}
    client = Client(d.get("min", 1), d.get("max", 3))
    mod = REGISTRY[a.name]
    started = time.time()
    try:
        r = mod.search(client, cand.get("keywords") or {}, cand.get("criteria") or {}, limit,
                       step.get("since"), c.secrets)
    except Exception as e:  # une source ne fait jamais échouer le passage
        r = {"offers": [], "requests_used": client.requests, "status": "error",
             "message": "erreur inattendue : %s" % e, "queries": [], "duration_s": round(time.time() - started, 1)}
    raw_path = os.path.join(runs.work_dir(c.paths, a.run), "%s.json" % a.name)
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(r["offers"], f, ensure_ascii=False, indent=1)
    res = _ingest(c, a.run, a.name, r["offers"], r["status"], r["requests_used"], r["message"],
                  r.get("duration_s"), r.get("queries"))
    return out(res)


def cmd_ingest(a):
    c = Ctx()
    if a.name not in SOURCES:
        return fail("unknown_source", "source inconnue : %s" % a.name)
    offers = []
    if a.file:
        try:
            with open(a.file, encoding="utf-8-sig") as f:
                offers = json.load(f)
        except (OSError, ValueError) as e:
            return fail("bad_file", "fichier d'offres illisible : %s" % e)
        if isinstance(offers, dict):
            offers = offers.get("offers") or []
    queries = None
    if a.queries:
        try:
            queries = json.loads(a.queries)
        except ValueError:
            queries = None
    return out(_ingest(c, a.run, a.name, offers, a.status, a.requests, a.message or "", a.duration, queries))


def cmd_source_result(a):
    c = Ctx()
    res = runs.record_source(c.paths, a.run, a.name, a.status, a.requests, a.message or "")
    res["ok"] = True
    return out(res)


def cmd_to_score(a):
    c = Ctx()
    if a.run:
        rec = runs.load_run(c.paths, a.run)
        rows = [c.store.get(i) for i in rec["created"]]
        rows = [r for r in rows if r and not str(r.get("score", "")).strip()]
    else:
        rows = c.store.list(unscored=True, order_by="detected")
    total = len(rows)
    rows = rows[: a.limit]
    return out({"ok": True, "remaining": total, "batch": [_brief(r, with_desc=True) for r in rows],
                "components": scoring.COMPONENTS, "weights": c.kit["scoring"]["weights"],
                "hard_filter_cap": c.kit["scoring"]["hard_filter_cap"]})


def cmd_apply_scores(a):
    c = Ctx()
    try:
        with open(a.file, encoding="utf-8-sig") as f:
            items = json.load(f)
    except (OSError, ValueError) as e:
        return fail("bad_file", "fichier de scores illisible : %s" % e)
    if isinstance(items, dict):
        items = items.get("scores") or []
    w = c.kit["scoring"]["weights"]
    cap = int(c.kit["scoring"]["hard_filter_cap"])
    done, errors = [], []
    for item in items:
        try:
            comps, viol, rationale = scoring.validate_item(item)
            score = scoring.compute(comps, viol, w, cap)
            if c.store.update_score(item["id"], score, rationale) == "not_found":
                errors.append({"id": item["id"], "error": "offre introuvable"})
                continue
            done.append({"id": item["id"], "score": score})
        except (scoring.ScoreError, storage.StorageError, ValueError) as e:
            errors.append({"id": (item or {}).get("id"), "error": str(e)})
    try:
        c.store.save()
    except storage.StorageError as e:
        return fail("storage", str(e), scored=done)
    remaining = len(c.store.list(unscored=True))
    return out({"ok": not errors, "scored": done, "errors": errors, "remaining_unscored": remaining})


def cmd_reset_scores(a):
    c = Ctx()
    statuses = None if a.all else {"new", "seen"}
    n = c.store.clear_scores(statuses)
    c.store.save()
    return out({"ok": True, "cleared": n, "message": "%d offre(s) à renoter (« note les offres en attente »)." % n})


def cmd_run_finish(a):
    c = Ctx()
    rec, alert = runs.finish(c.paths, c.kit, c.store, a.run)
    path, info = summ.build(c.paths, c.kit, c.store, runs.load_state(c.paths), rec["started_at"][:10])
    moved = runs.archive(c.paths, c.kit["logging"].get("archive_after_days", 30))
    notified = None
    if alert and alert["channel"] == "system" and not a.no_notify:
        notified = send_system(alert["title"], alert["message"])
    return out({"ok": True, "run_id": rec["run_id"], "stats": rec["stats"],
                "results": {k: {kk: v[kk] for kk in ("status", "requests_used", "received", "created", "message")}
                            for k, v in rec["results"].items()},
                "log": "data/runs/%s.md" % rec["run_id"], "summary": os.path.relpath(path, c.paths.root),
                "alert": alert, "system_notification": notified,
                "push_needed": bool(alert and alert["channel"] == "push"), "archived_logs": moved,
                "warnings": info["warnings"]})


def cmd_list(a):
    c = Ctx()
    rows = c.store.list(status=a.status.split(",") if a.status else None, source=a.source,
                        min_score=a.min_score, detected_since=a.since, limit=a.limit,
                        order_by="detected" if a.order == "recent" else "score")
    return out({"ok": True, "count": len(rows), "offers": [_brief(r) for r in rows]})


def cmd_find(a):
    c = Ctx()
    q = N.strip_accents(a.text).lower()
    hits = []
    for r in c.store.list(order_by="detected"):
        hay = N.strip_accents(" ".join([r["id"], r["title"], r["company"], r["location"], r["url"]])).lower()
        if all(part in hay for part in q.split()):
            hits.append(_brief(r))
    return out({"ok": True, "count": len(hits), "offers": hits[:20]})


def cmd_set_status(a):
    c = Ctx()
    try:
        res = c.store.update_status(a.id, a.status)
    except storage.StorageError as e:
        return fail("bad_status", str(e))
    if res == "not_found":
        return fail("not_found", "aucune offre avec l'identifiant %s (utilise `jh find`)" % a.id)
    c.store.save()
    return out({"ok": True, "id": a.id, "status": a.status})


def cmd_summary(a):
    c = Ctx()
    path, info = summ.build(c.paths, c.kit, c.store, runs.load_state(c.paths), a.date)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    info.update({"ok": True, "path": os.path.relpath(path, c.paths.root), "markdown": text})
    return out(info)


def cmd_export(a):
    from . import export_xlsx
    c = Ctx()
    rows = c.store.list(order_by="score")
    os.makedirs(c.paths.exports, exist_ok=True)
    path = a.path or os.path.join(c.paths.exports, "offres-%s.xlsx" % time.strftime("%Y-%m-%d"))
    export_xlsx.export(rows, path, int(c.kit["scoring"]["alert_threshold"]))
    return out({"ok": True, "path": os.path.relpath(path, c.paths.root), "offers": len(rows)})


def cmd_notify(a):
    return out(send_system(a.title, a.message))


def cmd_session_start(a):
    """Sortie au format hook SessionStart de Claude Code (systemMessage + additionalContext)."""
    try:
        paths = config.Paths(config.find_root())
        if not os.path.isfile(paths.kit):
            print(json.dumps({"systemMessage": "Job Hunter n'est pas encore installé : dis « installe Job Hunter »."},
                             ensure_ascii=False))
            return 0
        c = Ctx()
        if not c.kit["logging"].get("show_summary_on_session_start", True):
            return 0
        msg, info, path = summ.session_message(c.paths, c.kit, c.store, runs.load_state(c.paths))
        ctx = "Résumé Job Hunter du %s : %d nouvelle(s) offre(s), %d au-dessus du seuil. Fichier : %s." % (
            info["date"], info["new"], info["above"], os.path.relpath(path, c.paths.root))
        print(json.dumps({"systemMessage": msg, "hookSpecificOutput": {"hookEventName": "SessionStart",
                                                                         "additionalContext": ctx}}, ensure_ascii=False))
    except Exception as e:  # un hook ne doit jamais bloquer l'ouverture de session
        print(json.dumps({"systemMessage": "Job Hunter : résumé indisponible (%s)." % e}, ensure_ascii=False))
    return 0


def cmd_archive(a):
    c = Ctx()
    return out({"ok": True, "archived": runs.archive(c.paths, c.kit["logging"].get("archive_after_days", 30))})


def cmd_state(a):
    c = Ctx()
    return out({"ok": True, "state": runs.load_state(c.paths)})


def cmd_secrets(a):
    paths = config.Paths(config.find_root())
    s = config.load_secrets(paths)
    return out({"ok": True, "file_exists": os.path.isfile(paths.secrets),
                "present": sorted(k for k, v in s.items() if v)})


def cmd_airtable_create_base(a):
    c = Ctx()
    token = c.secrets.get("AIRTABLE_API_KEY")
    if not token:
        return fail("missing_secret", "AIRTABLE_API_KEY absent de config/secrets.env")
    try:
        base_id = storage.airtable_create_base(token, a.workspace, a.name, c.kit["storage"]["airtable"].get("table") or "Offres")
    except storage.StorageError as e:
        return fail("airtable", str(e))
    return out({"ok": True, "base_id": base_id,
                "message": "Base créée. Écris storage.airtable.base_id: %s dans config/kit.yml." % base_id})


# --------------------------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(prog="jh", description="Moteur Job Hunter (sortie JSON).")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("check", help="état de l'installation").set_defaults(fn=cmd_check)
    sub.add_parser("init-storage", help="crée le CSV ou la table Airtable").set_defaults(fn=cmd_init_storage)
    s = sub.add_parser("sources", help="sources et disponibilité dans le mode courant")
    s.add_argument("--browser", choices=["yes", "no", "unknown"], default="unknown")
    s.set_defaults(fn=cmd_sources)

    r = sub.add_parser("run", help="cycle d'un passage")
    rs = r.add_subparsers(dest="run_cmd")
    x = rs.add_parser("start")
    x.add_argument("--browser", choices=["yes", "no", "unknown"], default="unknown")
    x.set_defaults(fn=cmd_run_start)
    x = rs.add_parser("finish")
    x.add_argument("--run", required=True)
    x.add_argument("--no-notify", action="store_true")
    x.set_defaults(fn=cmd_run_finish)

    x = sub.add_parser("source", help="exécute une source HTTP et enregistre ses offres")
    x.add_argument("name")
    x.add_argument("--run", required=True)
    x.add_argument("--limit", type=int)
    x.set_defaults(fn=cmd_source)

    x = sub.add_parser("ingest", help="enregistre les offres d'une source navigateur (fichier JSON)")
    x.add_argument("name")
    x.add_argument("--run", required=True)
    x.add_argument("--file")
    x.add_argument("--status", default="ok", choices=list(runs.STATUSES))
    x.add_argument("--requests", type=int, default=0)
    x.add_argument("--message", default="")
    x.add_argument("--duration", type=float, default=0)
    x.add_argument("--queries", help="JSON : [{title, location, count}]")
    x.set_defaults(fn=cmd_ingest)

    x = sub.add_parser("source-result", help="note le statut d'une source sans offre (bloquée, indisponible)")
    x.add_argument("name")
    x.add_argument("--run", required=True)
    x.add_argument("--status", required=True, choices=list(runs.STATUSES))
    x.add_argument("--requests", type=int, default=0)
    x.add_argument("--message", default="")
    x.set_defaults(fn=cmd_source_result)

    x = sub.add_parser("to-score", help="prochain lot d'offres à noter")
    x.add_argument("--run")
    x.add_argument("--limit", type=int, default=10)
    x.set_defaults(fn=cmd_to_score)
    x = sub.add_parser("apply-scores", help="calcule et enregistre les scores d'un lot")
    x.add_argument("--file", required=True)
    x.set_defaults(fn=cmd_apply_scores)
    x = sub.add_parser("reset-scores", help="efface les scores pour renoter")
    x.add_argument("--all", action="store_true", help="aussi les offres candidatées, refusées, ignorées")
    x.set_defaults(fn=cmd_reset_scores)

    x = sub.add_parser("list", help="liste les offres")
    x.add_argument("--status")
    x.add_argument("--source")
    x.add_argument("--min-score", type=int)
    x.add_argument("--since")
    x.add_argument("--limit", type=int, default=20)
    x.add_argument("--order", choices=["score", "recent"], default="score")
    x.set_defaults(fn=cmd_list)
    x = sub.add_parser("find", help="cherche une offre par mots")
    x.add_argument("text")
    x.set_defaults(fn=cmd_find)
    x = sub.add_parser("set-status", help="change le statut d'une offre")
    x.add_argument("id")
    x.add_argument("status", choices=sorted(N.STATUSES))
    x.set_defaults(fn=cmd_set_status)

    x = sub.add_parser("summary", help="(ré)écrit et affiche le résumé d'un jour")
    x.add_argument("--date")
    x.set_defaults(fn=cmd_summary)
    x = sub.add_parser("export", help="export Excel")
    x.add_argument("--path")
    x.set_defaults(fn=cmd_export)
    x = sub.add_parser("notify", help="notification système")
    x.add_argument("--title", required=True)
    x.add_argument("--message", required=True)
    x.set_defaults(fn=cmd_notify)
    sub.add_parser("session-start", help="message d'ouverture de session (hook)").set_defaults(fn=cmd_session_start)
    sub.add_parser("archive", help="archive les vieux journaux").set_defaults(fn=cmd_archive)
    sub.add_parser("state", help="état des sources").set_defaults(fn=cmd_state)
    sub.add_parser("secrets", help="clés présentes (noms seulement)").set_defaults(fn=cmd_secrets)
    x = sub.add_parser("airtable-create-base", help="crée la base Airtable du candidat")
    x.add_argument("--workspace", required=True)
    x.add_argument("--name", default="Job Hunter")
    x.set_defaults(fn=cmd_airtable_create_base)
    return p


def main(argv=None):
    parser = build_parser()
    a = parser.parse_args(argv)
    if not getattr(a, "fn", None):
        parser.print_help()
        return 0
    try:
        return a.fn(a)
    except FileNotFoundError as e:
        return fail("not_found", str(e))
    except storage.StorageError as e:
        return fail("storage", str(e))
    except Exception as e:  # pragma: no cover - filet de sécurité, message lisible
        return fail("unexpected", "%s: %s" % (type(e).__name__, e))
