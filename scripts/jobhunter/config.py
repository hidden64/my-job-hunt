"""Chemins du dépôt, lecture de kit.yml, candidate.yml et secrets.env, valeurs par défaut."""
import copy
import os

from . import yamlmini

DEFAULT_KIT = {
    "schema_version": 1,
    "execution": {"mode": "local"},
    "schedule": {"times": ["08:00", "13:00", "19:00"], "timezone": "Europe/Paris"},
    "storage": {
        "backend": "csv",
        "csv": {"path": "data/offers.csv", "auto_commit": False},
        "airtable": {"base_id": "", "table": "Offres"},
    },
    "sources": {
        "enabled": ["france_travail", "hellowork", "linkedin", "wttj", "apec", "jobteaser",
                    "indeed", "glassdoor"],
        "limits": {"france_travail": 20, "hellowork": 8, "linkedin": 5, "wttj": 6, "apec": 6,
                   "jobteaser": 6, "indeed": 4, "glassdoor": 4, "test": 3},
        "browser_delay_seconds": {"min": 2, "max": 6},
        "http_delay_seconds": {"min": 1, "max": 3},
    },
    "scoring": {
        "alert_threshold": 70,
        "hard_filter_cap": 30,
        "weights": {"title_match": 5, "skills_match": 5, "experience_level": 3,
                    "location_remote": 3, "contract": 3, "salary": 2, "education": 2},
    },
    "notifications": {"channel": "system", "max_offers_in_alert": 3},
    "logging": {"archive_after_days": 30, "show_summary_on_session_start": True},
}


def find_root(start=None):
    """Racine du dépôt : variable JH_ROOT, sinon premier parent contenant CLAUDE.md et config/."""
    env = os.environ.get("JH_ROOT")
    if env:
        return os.path.abspath(env)
    cur = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isfile(os.path.join(cur, "CLAUDE.md")) and os.path.isdir(os.path.join(cur, "config")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    # Repli : le dépôt qui contient ce fichier (scripts/jobhunter/config.py).
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Paths:
    def __init__(self, root):
        self.root = root

    def p(self, *parts):
        return os.path.join(self.root, *parts)

    @property
    def kit(self):
        return self.p("config", "kit.yml")

    @property
    def candidate(self):
        return self.p("config", "candidate.yml")

    @property
    def secrets(self):
        return self.p("config", "secrets.env")

    @property
    def runs(self):
        return self.p("data", "runs")

    @property
    def summaries(self):
        return self.p("data", "summaries")

    @property
    def exports(self):
        return self.p("data", "exports")

    @property
    def pending(self):
        return self.p("data", "pending")

    @property
    def state(self):
        return self.p("data", "runs", "state.json")


def load_kit(paths, required=True):
    if not os.path.isfile(paths.kit):
        if required:
            raise FileNotFoundError("config/kit.yml absent : le kit n'est pas installé (dis « installe Job Hunter »).")
        return copy.deepcopy(DEFAULT_KIT)
    return _merge(DEFAULT_KIT, yamlmini.load_file(paths.kit))


def load_candidate(paths, required=True):
    if not os.path.isfile(paths.candidate):
        if required:
            raise FileNotFoundError("config/candidate.yml absent : lance le questionnaire (dis « crée mon profil »).")
        return {}
    return yamlmini.load_file(paths.candidate) or {}


def load_secrets(paths):
    """Lit config/secrets.env (CLÉ=valeur). Les variables d'environnement priment."""
    out = {}
    if os.path.isfile(paths.secrets):
        with open(paths.secrets, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    for k in list(out) + ["FRANCE_TRAVAIL_CLIENT_ID", "FRANCE_TRAVAIL_CLIENT_SECRET", "AIRTABLE_API_KEY"]:
        if os.environ.get(k):
            out[k] = os.environ[k]
    return out


def keywords_validated(candidate):
    kw = (candidate or {}).get("keywords") or {}
    return bool(kw.get("validated_at")) and bool(kw.get("titles"))
