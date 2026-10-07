"""Requêtes HTTP polies pour les sources : un vrai User-Agent de navigateur, un délai aléatoire entre
deux requêtes, aucune nouvelle tentative, et détection des pages de blocage."""
import random
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")


class Blocked(Exception):
    """Captcha, page de connexion, 403/429 : la source s'arrête pour ce passage."""


class FetchError(Exception):
    """Réseau, statut inattendu, page illisible."""


class Client:
    def __init__(self, delay_min=1.0, delay_max=3.0, opener=None, sleep=time.sleep):
        self.delay_min, self.delay_max = float(delay_min), float(delay_max)
        self._open = opener or urllib.request.urlopen
        self._sleep = sleep
        self._last = None
        self.requests = 0

    def get(self, url, headers=None, timeout=30):
        """Une requête. Une seule nouvelle tentative, 5 s plus tard, si la connexion est coupée
        (erreur réseau). Jamais de nouvelle tentative sur un blocage (403, 429, captcha)."""
        try:
            return self._get(url, headers, timeout)
        except FetchError as e:
            if not str(e).startswith("réseau"):
                raise
            self._sleep(5)
            self._last = None
            return self._get(url, headers, timeout)

    def _get(self, url, headers=None, timeout=30):
        if self._last is not None:
            wait = random.uniform(self.delay_min, self.delay_max) - (time.time() - self._last)
            if wait > 0:
                self._sleep(wait)
        h = {"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.6",
             "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"}
        h.update(headers or {})
        req = urllib.request.Request(url, headers=h)
        self.requests += 1
        try:
            with self._open(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
                final = resp.geturl() if hasattr(resp, "geturl") else url
        except urllib.error.HTTPError as e:
            self._last = time.time()
            if e.code in (401, 403, 429, 999):
                raise Blocked("HTTP %s sur %s" % (e.code, url.split("?")[0]))
            raise FetchError("HTTP %s sur %s" % (e.code, url.split("?")[0]))
        except urllib.error.URLError as e:
            self._last = time.time()
            raise FetchError("réseau : %s (si tu es en mode cloud, vérifie l'accès réseau de l'environnement)" % e.reason)
        except Exception as e:  # timeout, connexion coupée
            self._last = time.time()
            raise FetchError("réseau : %s" % e)
        self._last = time.time()
        low = body[:20000].lower()
        if any(m in low for m in ("captcha", "cf-challenge", "challenge-platform", "verify you are human",
                                    "vérifiez que vous êtes humain", "authwall", "/checkpoint/")):
            raise Blocked("page de vérification anti-robot sur %s" % url.split("?")[0])
        return body, final
