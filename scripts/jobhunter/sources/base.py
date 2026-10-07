"""Outils communs aux sources HTTP : file de requêtes intitulé × zone, dates relatives, résultat."""
import re
import time
from datetime import datetime, timedelta

from ..http import Blocked, FetchError
from ..normalize import strip_accents


def result(offers, client, status="ok", message="", queries=None, started=None):
    return {"offers": offers, "requests_used": client.requests, "status": status, "message": message,
            "queries": queries or [], "duration_s": round(time.time() - (started or time.time()), 1)}


def locations(keywords):
    """Zones validées : liste de dicts {label, city, department}. Accepte aussi des chaînes."""
    out = []
    for loc in (keywords or {}).get("locations") or []:
        if isinstance(loc, dict):
            out.append({"label": str(loc.get("label") or loc.get("city") or ""),
                        "city": str(loc.get("city") or loc.get("label") or ""),
                        "department": str(loc.get("department") or "").strip()})
        elif loc:
            out.append({"label": str(loc), "city": str(loc), "department": ""})
    return out or [{"label": "France", "city": "", "department": ""}]


def titles(keywords):
    return [str(t) for t in ((keywords or {}).get("titles") or []) if str(t).strip()]


def negatives(keywords):
    return [strip_accents(str(n)).lower() for n in ((keywords or {}).get("negative") or []) if str(n).strip()]


def excluded(title, negs):
    t = strip_accents(title or "").lower()
    return any(re.search(r"\b%s\b" % re.escape(n), t) for n in negs)


def days_since(since, now=None):
    if not since:
        return None
    try:
        then = datetime.fromisoformat(since)
    except ValueError:
        return None
    now = now or datetime.now(then.tzinfo)
    return max(0.0, (now - then).total_seconds() / 86400.0)


def relative_date(text, today=None):
    """« il y a 3 jours », « Publié hier », « 15 hours ago » -> AAAA-MM-JJ (ou '')."""
    if not text:
        return ""
    t = strip_accents(text).lower()
    today = today or datetime.now()
    if re.search(r"aujourd|today|heure|hour|minute|instant|just now", t):
        return today.strftime("%Y-%m-%d")
    if re.search(r"hier|yesterday", t):
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    m = re.search(r"(\d+)\s*(jour|day|semaine|week|mois|month)", t)
    if not m or "plus de" in t:
        return ""
    n, unit = int(m.group(1)), m.group(2)
    days = n * (7 if unit in ("semaine", "week") else 30 if unit in ("mois", "month") else 1)
    return (today - timedelta(days=days)).strftime("%Y-%m-%d")


def run_queries(client, pairs, limit, fetch_page, max_pages=3):
    """Parcours en largeur : première page de chaque (intitulé, zone), puis pages suivantes tant que
    le plafond le permet. fetch_page(title, loc, page) -> (offres, page_pleine)."""
    queue = [(t, loc, 0) for t, loc in pairs]
    offers, queries, status, message = [], [], "ok", ""
    while queue and client.requests < limit:
        title, loc, page = queue.pop(0)
        try:
            found, full = fetch_page(title, loc, page)
        except Blocked as e:
            status, message = "blocked", str(e)
            break
        except FetchError as e:
            status, message = "error", str(e)
            break
        offers.extend(found)
        queries.append({"title": title, "location": loc.get("label", ""), "page": page, "count": len(found)})
        if full and page + 1 < max_pages:
            queue.append((title, loc, page + 1))
    return offers, queries, status, message
