"""Résumé quotidien lisible (data/summaries/AAAA-MM-JJ.md) et message d'ouverture de session."""
import os
from datetime import datetime, timedelta

from .sources import SOURCES


def _date(d=None):
    return d or datetime.now().strftime("%Y-%m-%d")


def warnings(kit, state, now=None):
    now = now or datetime.now().astimezone()
    out = []
    enabled = kit["sources"].get("enabled") or []
    mode = kit["execution"]["mode"]
    for name in enabled:
        meta = SOURCES.get(name) or {}
        st = (state.get("sources") or {}).get(name) or {}
        label = meta.get("label", name)
        if int(st.get("consecutive_failures", 0)) >= 3:
            out.append("%s est en échec depuis %s passages (%s). Dis « désactive %s » si ça continue."
                       % (label, st["consecutive_failures"], st.get("last_message") or st.get("last_status"), label))
        if mode in meta.get("available_in", []) and st.get("last_run"):
            last = st.get("last_offer_at")
            if last:
                try:
                    age = now - datetime.fromisoformat(last)
                    if age > timedelta(days=7):
                        out.append("%s n'a ramené aucune offre depuis %d jours." % (label, age.days))
                except ValueError:
                    pass
    for title, kw in (state.get("keywords") or {}).items():
        ref = kw.get("last_hit_at") or kw.get("first_seen_at")
        if not ref or not title:
            continue
        try:
            age = now - datetime.fromisoformat(ref)
        except ValueError:
            continue
        if age > timedelta(days=7):
            out.append("L'intitulé « %s » ne ramène rien depuis %d jours : pense à le revoir (« revois mes mots-clés »)."
                       % (title, age.days))
    return out


def build(paths, kit, store, state, day=None):
    day = _date(day)
    threshold = int(kit["scoring"]["alert_threshold"])
    today = [r for r in store.list(order_by="score") if (r.get("detected_at") or "").startswith(day)]
    above = [r for r in today if str(r.get("score", "")).strip() and int(r["score"]) >= threshold]
    runs = [r for r in (state.get("runs") or []) if (r.get("started_at") or "").startswith(day)]
    lines = ["# Résumé du %s" % day, ""]
    if not today:
        lines += ["Aucune nouvelle offre aujourd'hui%s." % (
            " (%d passage(s) effectué(s))" % len(runs) if runs else " pour l'instant")]
    else:
        lines += ["**Aujourd'hui : %d nouvelle%s offre%s, dont %d au-dessus de ton seuil de %d %%.**"
                  % (len(today), "s" if len(today) > 1 else "", "s" if len(today) > 1 else "", len(above), threshold),
                  "", "Passages : %s." % (", ".join(r["run_id"][11:13] + "h" + r["run_id"][13:15] for r in runs) or "–"), "",
                  "## Les 10 meilleures nouvelles offres", "",
                  "| Score | Offre | Entreprise | Lieu | Contrat | Pourquoi |", "|---|---|---|---|---|---|"]
        for r in today[:10]:
            lines.append("| %s | [%s](%s) | %s | %s | %s | %s |" % (
                (r.get("score") or "–") + (" ✅" if r in above else ""), r["title"].replace("|", "/"), r["url"],
                r["company"].replace("|", "/"), r["location"], r["contract"],
                (r.get("score_rationale") or "pas encore noté").replace("|", "/")))
    warn = warnings(kit, state)
    if warn:
        lines += ["", "## À surveiller", ""] + ["- " + w for w in warn]
    lines += ["", "Pour voir toutes tes offres : « montre mes offres au-dessus de %d » ou ouvre `data/offers.csv`." % threshold]
    os.makedirs(paths.summaries, exist_ok=True)
    path = os.path.join(paths.summaries, day + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path, {"date": day, "new": len(today), "above": len(above), "warnings": warn,
                  "top": [{"score": r.get("score"), "title": r["title"], "company": r["company"],
                           "location": r["location"], "url": r["url"]} for r in today[:5]]}


def session_message(paths, kit, store, state):
    day = _date()
    path, info = build(paths, kit, store, state, day)
    if info["new"] == 0:
        last = (state.get("runs") or [{}])[-1].get("started_at", "")
        msg = "Job Hunter : pas de nouvelle offre aujourd'hui%s." % (
            " (dernier passage %s)" % last[:16].replace("T", " à ") if last else ", aucun passage encore")
    else:
        msg = ("Job Hunter : %d nouvelle(s) offre(s) aujourd'hui, %d au-dessus de %s %%. "
               "Dis « montre-moi le résumé du jour »." % (info["new"], info["above"], kit["scoring"]["alert_threshold"]))
    if info["warnings"]:
        msg += " ⚠️ %d point(s) à surveiller." % len(info["warnings"])
    return msg, info, path
