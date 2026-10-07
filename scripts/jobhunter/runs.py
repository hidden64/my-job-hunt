"""Cycle de vie d'un passage : démarrage, résultats par source, fin (journal, état, alerte)."""
import json
import os
import shutil
from datetime import datetime, timedelta

from .sources import SOURCES

STATUSES = ("ok", "blocked", "error", "unavailable", "skipped")


def _now():
    return datetime.now().astimezone().replace(microsecond=0)


def _load_json(path, default):
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def work_dir(paths, run_id):
    return paths.p("data", "runs", "work", run_id)


def run_file(paths, run_id):
    return os.path.join(work_dir(paths, run_id), "run.json")


def load_state(paths):
    return _load_json(paths.state, {"sources": {}, "keywords": {}, "runs": []})


def save_state(paths, state):
    _save_json(paths.state, state)


# --------------------------------------------------------------------------------------------

def plan(kit, candidate, browser_available=None):
    """Liste ordonnée des sources à appeler (http d'abord, puis navigateur)."""
    mode = kit["execution"]["mode"]
    enabled = list(kit["sources"].get("enabled") or [])
    limits = kit["sources"].get("limits") or {}
    out = []
    for name in enabled:
        meta = SOURCES.get(name)
        if not meta:
            out.append({"name": name, "label": name, "mode": "?", "available": False,
                        "reason": "source inconnue du kit", "limit": 0})
            continue
        entry = {"name": name, "label": meta["label"], "mode": meta["mode"],
                 "limit": int(limits.get(name, meta["default_limit"])), "available": True, "reason": ""}
        if mode not in meta["available_in"]:
            entry.update(available=False, reason="source navigateur, indisponible en mode cloud")
        elif meta["mode"] == "browser" and browser_available is False:
            entry.update(available=False, reason="navigateur Claude in Chrome non connecté")
        out.append(entry)
    out.sort(key=lambda e: (0 if e["mode"] == "http" else 1))
    return out


def start(paths, kit, candidate, browser_available=None):
    started = _now()
    run_id = started.strftime("%Y-%m-%d-%H%M")
    base = run_id
    n = 1
    while os.path.exists(work_dir(paths, run_id)) or os.path.exists(paths.p("data", "runs", run_id + ".md")):
        n += 1
        run_id = "%s-%d" % (base, n)
    state = load_state(paths)
    steps = plan(kit, candidate, browser_available)
    for s in steps:
        s["since"] = (state["sources"].get(s["name"]) or {}).get("last_success_at")
    record = {"run_id": run_id, "started_at": started.isoformat(), "mode": kit["execution"]["mode"],
              "backend": kit["storage"]["backend"], "plan": steps, "results": {}, "created": [],
              "finished_at": None}
    _save_json(run_file(paths, run_id), record)
    return record


def load_run(paths, run_id):
    rec = _load_json(run_file(paths, run_id), None)
    if rec is None:
        raise FileNotFoundError("passage %s introuvable (lance d'abord `jh run start`)" % run_id)
    return rec


def save_run(paths, rec):
    _save_json(run_file(paths, rec["run_id"]), rec)


def record_source(paths, run_id, source, status, requests_used=0, message="", received=0, rejected=0,
                  created=None, updated=0, duplicates=0, duration=None, queries=None):
    if status not in STATUSES:
        raise ValueError("statut inconnu : %s" % status)
    rec = load_run(paths, run_id)
    prev = rec["results"].get(source) or {}
    res = {
        "status": status,
        "requests_used": int(requests_used) + int(prev.get("requests_used", 0)),
        "received": int(received) + int(prev.get("received", 0)),
        "rejected": int(rejected) + int(prev.get("rejected", 0)),
        "created": int(len(created or [])) + int(prev.get("created", 0)),
        "updated": int(updated) + int(prev.get("updated", 0)),
        "duplicates": int(duplicates) + int(prev.get("duplicates", 0)),
        "message": message or prev.get("message", ""),
        "duration_s": round(float(duration or 0) + float(prev.get("duration_s", 0)), 1),
        "queries": (prev.get("queries") or []) + (queries or []),
    }
    # Un statut d'échec n'est jamais masqué par un ok ultérieur dans le même passage.
    if prev.get("status") in ("blocked", "error") and status == "ok":
        res["status"] = prev["status"]
    rec["results"][source] = res
    rec["created"] = list(dict.fromkeys(rec["created"] + list(created or [])))
    save_run(paths, rec)
    return res


# --------------------------------------------------------------------------------------------

def finish(paths, kit, store, run_id):
    rec = load_run(paths, run_id)
    finished = _now()
    rec["finished_at"] = finished.isoformat()
    state = load_state(paths)
    threshold = int(kit["scoring"]["alert_threshold"])

    # Sources planifiées mais jamais signalées : on les note « skipped ».
    for step in rec["plan"]:
        if step["name"] not in rec["results"]:
            rec["results"][step["name"]] = {"status": "unavailable" if not step["available"] else "skipped",
                                            "requests_used": 0, "received": 0, "rejected": 0, "created": 0,
                                            "updated": 0, "duplicates": 0, "duration_s": 0, "queries": [],
                                            "message": step.get("reason") or "non exécutée pendant ce passage"}

    # État par source.
    for name, res in rec["results"].items():
        st = state["sources"].setdefault(name, {"consecutive_failures": 0})
        st["last_status"] = res["status"]
        st["last_message"] = res.get("message", "")
        st["last_run"] = run_id
        if res["status"] == "ok":
            st["last_success_at"] = rec["started_at"]
            st["consecutive_failures"] = 0
            if res.get("received"):
                st["last_offer_at"] = rec["started_at"]
        elif res["status"] in ("blocked", "error"):
            st["consecutive_failures"] = int(st.get("consecutive_failures", 0)) + 1
        for q in res.get("queries") or []:
            kw = state["keywords"].setdefault(q.get("title", ""), {})
            kw.setdefault("first_seen_at", rec["started_at"])
            if q.get("count", 0) > 0:
                kw["last_hit_at"] = rec["started_at"]

    created = [store.get(i) for i in rec["created"] if store.get(i)]
    scored = [r for r in created if str(r.get("score", "")).strip()]
    unscored = [r for r in created if not str(r.get("score", "")).strip()]
    above = sorted([r for r in scored if int(r["score"]) >= threshold], key=lambda r: -int(r["score"]))
    rec["stats"] = {"new": len(created), "scored": len(scored), "unscored": len(unscored),
                    "above_threshold": len(above)}
    state["runs"] = (state.get("runs") or [])[-49:] + [{"run_id": run_id, "started_at": rec["started_at"],
                                                         "new": len(created), "above": len(above)}]
    save_state(paths, state)
    save_run(paths, rec)
    write_run_log(paths, kit, rec, created)

    alert = None
    channel = kit["notifications"].get("channel", "system")
    if above and channel != "none":
        n_named = int(kit["notifications"].get("max_offers_in_alert", 3))
        names = ", ".join("%s chez %s (%s, %s %%)" % (r["title"], r["company"], r["location"], r["score"])
                          for r in above[:n_named])
        plural = "s" if len(above) > 1 else ""
        alert = {"channel": channel,
                 "title": "Job Hunter : %d nouvelle%s offre%s ≥ %d %%" % (len(above), plural, plural, threshold),
                 "message": names + (" …" if len(above) > n_named else ""),
                 "summary_path": "data/summaries/%s.md" % rec["started_at"][:10]}
    return rec, alert


def write_run_log(paths, kit, rec, created):
    lines = ["# Passage %s" % rec["run_id"], "",
             "- Mode : %s" % rec["mode"],
             "- Stockage : %s" % rec["backend"],
             "- Début : %s" % rec["started_at"],
             "- Fin : %s" % rec["finished_at"], ""]
    s = rec.get("stats") or {}
    lines += ["**%d nouvelle(s) offre(s)**, %d notée(s), %d au-dessus du seuil de %s %%."
              % (s.get("new", 0), s.get("scored", 0), s.get("above_threshold", 0), kit["scoring"]["alert_threshold"]),
              ""]
    if s.get("unscored"):
        lines += ["⚠️ %d offre(s) nouvelle(s) sans score : relancer « note les offres en attente »." % s["unscored"], ""]
    lines += ["## Sources", "",
              "| Source | Statut | Requêtes | Reçues | Rejetées | Nouvelles | Doublons | Durée (s) | Message |",
              "|---|---|---|---|---|---|---|---|---|"]
    labels = {k: v["label"] for k, v in SOURCES.items()}
    for name, r in rec["results"].items():
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            labels.get(name, name), r["status"], r["requests_used"], r["received"], r["rejected"], r["created"],
            r["duplicates"] + r["updated"], r["duration_s"], (r.get("message") or "").replace("|", "/")))
    unavailable = [labels.get(n, n) for n, r in rec["results"].items() if r["status"] == "unavailable"]
    if unavailable:
        lines += ["", "Sources non disponibles dans ce mode : %s." % ", ".join(unavailable)]
    if created:
        lines += ["", "## Nouvelles offres", "", "| Score | Titre | Entreprise | Lieu | Contrat | Source |",
                  "|---|---|---|---|---|---|"]
        for r in sorted(created, key=lambda r: -(int(r["score"]) if str(r.get("score", "")).strip() else -1)):
            lines.append("| %s | [%s](%s) | %s | %s | %s | %s |" % (
                r.get("score") or "–", r["title"].replace("|", "/"), r["url"], r["company"].replace("|", "/"),
                r["location"], r["contract"], r["source"]))
    errors = [(n, r) for n, r in rec["results"].items() if r["status"] in ("blocked", "error")]
    if errors:
        lines += ["", "## Erreurs", ""]
        for n, r in errors:
            lines.append("- **%s** (%s) : %s" % (labels.get(n, n), r["status"], r.get("message") or "sans détail"))
    path = paths.p("data", "runs", rec["run_id"] + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def cleanup_work(paths, keep_days=2):
    base = paths.p("data", "runs", "work")
    if not os.path.isdir(base):
        return 0
    limit = (datetime.now() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
    n = 0
    for name in os.listdir(base):
        if name[:10] < limit:
            shutil.rmtree(os.path.join(base, name), ignore_errors=True)
            n += 1
    return n


def archive(paths, days):
    base = paths.runs
    arch = os.path.join(base, "archive")
    limit = (datetime.now() - timedelta(days=int(days))).strftime("%Y-%m-%d")
    moved = 0
    if not os.path.isdir(base):
        return 0
    for name in os.listdir(base):
        if name.endswith(".md") and name[:4].isdigit() and name[:10] < limit:
            os.makedirs(arch, exist_ok=True)
            shutil.move(os.path.join(base, name), os.path.join(arch, name))
            moved += 1
    return moved
