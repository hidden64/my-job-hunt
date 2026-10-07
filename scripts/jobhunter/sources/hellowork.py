"""HelloWork : recherche publique www.hellowork.com (rendu côté serveur, aucune clé)."""
import re
import time
import urllib.parse

from .. import normalize as N
from ..http import FetchError
from . import base

SITE = "https://www.hellowork.com"


def search_url(title, loc, page, since_days):
    q = {"k": title}
    if loc.get("city"):
        q["l"] = loc["city"]
    if since_days is not None:
        q["d"] = "d" if since_days <= 0.5 else "w"
    if page:
        q["p"] = str(page + 1)
    return SITE + "/fr-fr/emploi/recherche.html?" + urllib.parse.urlencode(q)


def _txt(pattern, block):
    m = re.search(pattern, block, re.S)
    return N.clean_text(m.group(1)) if m else ""


def parse_list(html_text, today=None):
    offers = []
    for block in html_text.split('data-cy="serpCard"')[1:]:
        block = block[:12000]
        href = re.search(r'href="(/fr-fr/emplois/\d+\.html)"', block)
        if not href:
            continue
        aria = _txt(r'aria-label="(Voir offre de [^"]*)"', block)
        salary = ""
        for m in re.finditer(r'<div class="readonly tag-secondary-s typo-s-bold[^"]*">(.*?)</div>', block, re.S):
            t = N.clean_text(m.group(1))
            if "€" in t or "eur" in t.lower():
                salary = t
                break
        remote = _txt(r'data-cy="contractTag"\s*>(.*?)</div>', block)
        if not remote and "télétravail" in aria.lower():
            remote = aria
        date = _txt(r'<div class="typo-s text-grey-500[^"]*">(.*?)</div>', block)
        offers.append({
            "title": _txt(r'<p class="typo-l[^"]*">(.*?)</p>', block),
            "company": _txt(r'<p class="typo-s inline">(.*?)</p>', block),
            "location": _txt(r'data-cy="localisationCard"\s*>(.*?)</div>', block),
            "contract": _txt(r'data-cy="contractCard"\s*>(.*?)</div>', block),
            "remote": remote,
            "salary": salary,
            "url": SITE + href.group(1),
            "published_at": base.relative_date(date, today),
            "description": aria.replace("Voir offre de ", "", 1),
        })
    return offers


def search(client, keywords, criteria, limit, since=None, secrets=None):
    started = time.time()
    since_days = base.days_since(since)
    if since_days is not None and since_days > 7:
        since_days = None
    negs = base.negatives(keywords)
    pairs = [(t, loc) for t in base.titles(keywords) for loc in base.locations(keywords)]

    def fetch_page(title, loc, page):
        body, _ = client.get(search_url(title, loc, page, since_days))
        if 'data-cy="serpCard"' not in body and "serpFilters" not in body:
            raise FetchError("format de page inattendu sur HelloWork (le site a peut-être changé)")
        raw = parse_list(body)
        return [o for o in raw if not base.excluded(o["title"], negs)], len(raw) >= 20

    offers, queries, status, message = base.run_queries(client, pairs, limit, fetch_page)
    return base.result(offers, client, status, message, queries, started)
