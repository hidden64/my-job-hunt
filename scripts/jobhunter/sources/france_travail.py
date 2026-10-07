"""France Travail.

Par défaut : le site public candidat.francetravail.fr (rendu côté serveur, aucune clé).
En option : l'API officielle « Offres d'emploi v2 » si FRANCE_TRAVAIL_CLIENT_ID et
FRANCE_TRAVAIL_CLIENT_SECRET sont renseignés dans config/secrets.env (plus de champs : salaire,
description complète, télétravail).
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from .. import normalize as N
from ..http import Blocked, FetchError
from . import base

SITE = "https://candidat.francetravail.fr"
PAGE_SIZE = 20
EMISSIONS = [1, 3, 7, 14, 31]


def _emission(since):
    d = base.days_since(since)
    if d is None:
        return 14
    for e in EMISSIONS:
        if d + 0.5 <= e:          # marge de 12 heures
            return e
    return 31


def search_url(title, loc, page, emission):
    q = {"motsCles": title, "emission": str(emission), "range": "%d-%d" % (page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE - 1)}
    dep = (loc.get("department") or "").upper()
    if dep:
        q["lieux"] = dep if dep.endswith(("D", "R")) else dep + "D"
    return SITE + "/offres/recherche?" + urllib.parse.urlencode(q)


_LI = re.compile(r'<li data-id-offre="([^"]+)" class="result">(.*?)</li>', re.S)


def parse_list(html_text, today=None):
    offers = []
    for oid, block in _LI.findall(html_text):
        title = re.search(r'class="media-heading-title">(.*?)</span>', block, re.S)
        sub = re.search(r'<p translate="no" class="subtext">(.*?)</p>', block, re.S)
        desc = re.search(r'<p class="description">(.*?)</p>', block, re.S)
        contract = re.search(r'<p class="contrat visible-xs">(.*?)</p>', block, re.S)
        date = re.search(r'<p class="date">(.*?)</p>', block, re.S)
        company, location = "", ""
        if sub:
            loc = re.search(r"<span>(.*?)</span>", sub.group(1), re.S)
            location = N.clean_text(loc.group(1)) if loc else ""
            company = N.clean_text(re.sub(r"<span>.*?</span>", "", sub.group(1), flags=re.S)).rstrip(" -").strip()
        offers.append({
            "title": N.clean_text(title.group(1)) if title else "",
            "company": company,
            "location": _pretty_location(location),
            "contract": N.clean_text(contract.group(1)).split(" - ")[0] if contract else "",
            "remote": "",
            "salary": "",
            "url": "%s/offres/recherche/detail/%s" % (SITE, oid),
            "published_at": base.relative_date(N.clean_text(date.group(1)) if date else "", today),
            "description": N.clean_text(desc.group(1)) if desc else "",
        })
    return offers


def _pretty_location(loc):
    # « 69 - Villeurbanne » -> « Villeurbanne (69) »
    m = re.match(r"^\s*(\d{2,3}|2A|2B)\s*-\s*(.+)$", loc or "")
    return "%s (%s)" % (m.group(2).strip().title() if m.group(2).isupper() else m.group(2).strip(), m.group(1)) if m else loc


def search(client, keywords, criteria, limit, since=None, secrets=None):
    started = time.time()
    secrets = secrets or {}
    if secrets.get("FRANCE_TRAVAIL_CLIENT_ID") and secrets.get("FRANCE_TRAVAIL_CLIENT_SECRET"):
        return search_api(client, keywords, criteria, limit, since, secrets, started)
    emission = _emission(since)
    negs = base.negatives(keywords)
    pairs = [(t, loc) for t in base.titles(keywords) for loc in base.locations(keywords)]

    def fetch_page(title, loc, page):
        body, _final = client.get(search_url(title, loc, page, emission))
        if "<li data-id-offre" not in body and not re.search(r"\d+\s*offres?\s|aucune offre", N.strip_accents(body).lower()):
            raise FetchError("format de page inattendu sur France Travail (le site a peut-être changé)")
        found = [o for o in parse_list(body) if not base.excluded(o["title"], negs)]
        return found, len(_LI.findall(body)) >= PAGE_SIZE

    offers, queries, status, message = base.run_queries(client, pairs, limit, fetch_page)
    return base.result(offers, client, status, message, queries, started)


# --------------------------------------------------------------------------------------------
# API officielle (optionnelle)
# --------------------------------------------------------------------------------------------

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
API_PAGE = 50
_token_cache = {}


def _token(secrets, opener=urllib.request.urlopen):
    cached = _token_cache.get("token")
    if cached and cached[1] > time.time() + 60:
        return cached[0]
    data = urllib.parse.urlencode({"grant_type": "client_credentials",
                                   "client_id": secrets["FRANCE_TRAVAIL_CLIENT_ID"],
                                   "client_secret": secrets["FRANCE_TRAVAIL_CLIENT_SECRET"],
                                   "scope": "api_offresdemploiv2 o2dsoffre"}).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with opener(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise FetchError("authentification France Travail refusée (HTTP %s) : vérifie les identifiants" % e.code)
    except urllib.error.URLError as e:
        raise FetchError("France Travail injoignable : %s" % e.reason)
    _token_cache["token"] = (payload["access_token"], time.time() + int(payload.get("expires_in", 1400)))
    return payload["access_token"]


def map_api_offer(o):
    lieu = (o.get("lieuTravail") or {}).get("libelle", "")
    origin = (o.get("origineOffre") or {}).get("urlOrigine") or "%s/offres/recherche/detail/%s" % (SITE, o.get("id"))
    remote_hint = " ".join([o.get("description") or "", " ".join(c.get("libelle", "") for c in o.get("complements") or [])])
    return {
        "title": o.get("intitule", ""),
        "company": (o.get("entreprise") or {}).get("nom", ""),
        "location": _pretty_location(lieu),
        "contract": {"CDI": "cdi", "CDD": "cdd", "MIS": "interim", "SAI": "cdd", "LIB": "freelance",
                     "FRA": "freelance", "TTI": "interim", "DDI": "cdd", "DIN": "cdi"}.get(o.get("typeContrat", ""),
                                                                                         o.get("typeContratLibelle", "")),
        "remote": N.normalize_remote("", remote_hint),
        "salary": (o.get("salaire") or {}).get("libelle", ""),
        "url": origin,
        "published_at": (o.get("dateCreation") or "")[:10],
        "description": o.get("description", ""),
    }


def search_api(client, keywords, criteria, limit, since, secrets, started):
    try:
        token = _token(secrets)
    except FetchError as e:
        return base.result([], client, "error", str(e), [], started)
    emission = _emission(since)
    negs = base.negatives(keywords)
    pairs = [(t, loc) for t in base.titles(keywords) for loc in base.locations(keywords)]

    def fetch_page(title, loc, page):
        q = {"motsCles": title, "publieeDepuis": str(emission),
             "range": "%d-%d" % (page * API_PAGE, page * API_PAGE + API_PAGE - 1)}
        dep = (loc.get("department") or "").upper().rstrip("D")
        if dep:
            q["departement"] = dep
        body, _ = client.get(API_URL + "?" + urllib.parse.urlencode(q),
                             headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
        if not body.strip():
            return [], False               # 204 : aucun résultat
        try:
            data = json.loads(body)
        except ValueError:
            raise FetchError("réponse de l'API France Travail illisible")
        raw = data.get("resultats") or []
        found = [map_api_offer(o) for o in raw]
        found = [o for o in found if not base.excluded(o["title"], negs)]
        return found, len(raw) >= API_PAGE

    offers, queries, status, message = base.run_queries(client, pairs, limit, fetch_page)
    return base.result(offers, client, status, message or "via l'API officielle", queries, started)
