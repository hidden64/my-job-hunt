"""LinkedIn : recherche d'emplois publique, sans connexion (pages « jobs-guest »).

Le kit ne se connecte JAMAIS au compte LinkedIn du candidat. Si LinkedIn renvoie une page de
connexion ou un code 429/999, la source s'arrête pour ce passage.
"""
import re
import time
import urllib.parse

from .. import normalize as N
from ..http import FetchError
from . import base

ENDPOINT = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
PAGE_SIZE = 25


def search_url(title, loc, page, since_days):
    q = {"keywords": title, "start": str(page * PAGE_SIZE)}
    if loc.get("city"):
        q["location"] = "%s, France" % loc["city"]
    else:
        q["location"] = "France"
    seconds = 86400 * (1 if since_days is not None and since_days <= 1 else 7 if since_days is not None and since_days <= 7 else 30)
    q["f_TPR"] = "r%d" % seconds
    return ENDPOINT + "?" + urllib.parse.urlencode(q)


def parse_list(html_text, today=None):
    offers = []
    for block in re.split(r"<li>", html_text)[1:]:
        link = re.search(r'class="base-card__full-link[^"]*"\s+href="([^"]+)"', block)
        if not link:
            link = re.search(r'href="(https://[a-z]+\.linkedin\.com/jobs/view/[^"]+)"', block)
        if not link:
            continue
        url = N.clean_text(link.group(1)).split("?")[0]
        title = re.search(r'<h3 class="base-search-card__title">(.*?)</h3>', block, re.S)
        company = re.search(r'<h4 class="base-search-card__subtitle">(.*?)</h4>', block, re.S)
        location = re.search(r'<span class="job-search-card__location">(.*?)</span>', block, re.S)
        date = re.search(r'<time[^>]*datetime="([0-9-]{10})"', block)
        loc = N.clean_text(location.group(1)) if location else ""
        offers.append({
            "title": N.clean_text(title.group(1)) if title else "",
            "company": N.clean_text(company.group(1)) if company else "",
            "location": loc,
            "contract": "",
            "remote": loc if re.search(r"remote|télétravail|hybrid", loc, re.I) else "",
            "salary": N.clean_text((re.search(r'<span class="job-search-card__salary-info">(.*?)</span>', block, re.S)
                                    or [None, ""])[1]),
            "url": url,
            "published_at": date.group(1) if date else "",
            "description": "",
        })
    return offers


def search(client, keywords, criteria, limit, since=None, secrets=None):
    started = time.time()
    since_days = base.days_since(since)
    negs = base.negatives(keywords)
    pairs = [(t, loc) for t in base.titles(keywords) for loc in base.locations(keywords)]

    def fetch_page(title, loc, page):
        body, final = client.get(search_url(title, loc, page, since_days))
        if "login" in final or "authwall" in final:
            from ..http import Blocked
            raise Blocked("LinkedIn demande une connexion : source arrêtée pour ce passage")
        if body.strip() and "base-card" not in body and "<li>" not in body:
            raise FetchError("format de page inattendu sur LinkedIn")
        raw = parse_list(body)
        return [o for o in raw if not base.excluded(o["title"], negs)], len(raw) >= PAGE_SIZE

    offers, queries, status, message = base.run_queries(client, pairs, limit, fetch_page, max_pages=2)
    return base.result(offers, client, status, message, queries, started)
