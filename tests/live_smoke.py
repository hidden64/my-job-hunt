"""Test réseau manuel des sources HTTP (France Travail, HelloWork, LinkedIn).

Usage depuis la racine : python3 tests/live_smoke.py
Fait au plus 2 requêtes par source avec un profil fictif « Data Analyst » à Lyon, et affiche ce
que chaque source renvoie. À lancer quand une source semble cassée ou après un changement de site.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from jobhunter import normalize as N  # noqa: E402
from jobhunter.http import Client  # noqa: E402
from jobhunter.sources import REGISTRY  # noqa: E402

KEYWORDS = {"titles": ["Data Analyst"], "negative": ["senior"],
            "locations": [{"label": "Lyon", "city": "Lyon", "department": "69"}]}


def main():
    failed = 0
    for name in ("france_travail", "hellowork", "linkedin"):
        r = REGISTRY[name].search(Client(1, 2), KEYWORDS, {}, 2, None, {})
        valid = []
        for o in r["offers"]:
            try:
                valid.append(N.normalize_offer(o, name))
            except N.InvalidOffer:
                pass
        ok = r["status"] == "ok" and len(valid) > 0
        failed += 0 if ok else 1
        print("%-15s %-8s requêtes=%d offres=%d valides=%d %s" % (
            name, r["status"], r["requests_used"], len(r["offers"]), len(valid), r["message"]))
        for o in valid[:2]:
            print("    - %s | %s | %s | %s | %s" % (o["title"], o["company"], o["location"], o["contract"], o["url"]))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
