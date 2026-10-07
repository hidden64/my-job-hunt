"""Source factice sans réseau, pour tester toute la chaîne (voir .claude/skills/collect/sources/test.md)."""
import json
import os
import time

from .. import normalize as N
from ..config import find_root
from . import base

FIXTURE = os.path.join("tests", "fixtures", "sources", "test-offers.json")


class _Counter:
    def __init__(self):
        self.requests = 0


def _fold(s):
    return N.strip_accents(N.clean_text(s)).lower()


def search(client, keywords, criteria, limit, since=None, secrets=None, root=None):
    started = time.time()
    counter = _Counter()
    path = os.path.join(root or find_root(), FIXTURE)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return base.result([], counter, "error", "fichier de test illisible : %s" % FIXTURE, [], started)
    negs = base.negatives(keywords)
    offers, queries = [], []
    for title in base.titles(keywords):
        for loc in base.locations(keywords):
            if counter.requests >= limit:
                break
            counter.requests += 1
            found = []
            for o in data:
                if o.get("title") == "__BLOCK__":
                    return base.result(offers, counter, "blocked", "blocage simulé", queries, started)
                if o.get("title") == "__ERROR__":
                    return base.result(offers, counter, "error", "erreur simulée", queries, started)
                if _fold(title) not in _fold(o.get("title")):
                    continue
                if base.excluded(o.get("title", ""), negs):
                    continue
                if _fold(loc["label"]) not in _fold(o.get("location")) and o.get("remote") != "full":
                    continue
                found.append(dict(o))
            offers.extend(found)
            queries.append({"title": title, "location": loc["label"], "page": 0, "count": len(found)})
    return base.result(offers, counter, "ok", "", queries, started)
