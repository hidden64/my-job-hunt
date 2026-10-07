"""Sources HTTP exécutables par le moteur. Les sources navigateur n'ont pas de module :
Claude les pilote à partir de leur fiche dans .claude/skills/collect/sources/."""
from . import france_travail, hellowork, linkedin, test

REGISTRY = {
    "france_travail": france_travail,
    "hellowork": hellowork,
    "linkedin": linkedin,
    "test": test,
}

# Propriétés de toutes les sources, y compris navigateur (miroir de docs/SOURCES.md).
SOURCES = {
    "france_travail": {"label": "France Travail", "mode": "http", "available_in": ["local", "cloud"], "default_limit": 20},
    "hellowork": {"label": "HelloWork", "mode": "http", "available_in": ["local", "cloud"], "default_limit": 8},
    "linkedin": {"label": "LinkedIn (recherche publique)", "mode": "http", "available_in": ["local", "cloud"], "default_limit": 5},
    "wttj": {"label": "Welcome to the Jungle", "mode": "browser", "available_in": ["local"], "default_limit": 6},
    "apec": {"label": "APEC", "mode": "browser", "available_in": ["local"], "default_limit": 6},
    "jobteaser": {"label": "Jobteaser", "mode": "browser", "available_in": ["local"], "default_limit": 6},
    "indeed": {"label": "Indeed", "mode": "browser", "available_in": ["local"], "default_limit": 4},
    "glassdoor": {"label": "Glassdoor", "mode": "browser", "available_in": ["local"], "default_limit": 4},
    "test": {"label": "Source de test", "mode": "http", "available_in": ["local", "cloud"], "default_limit": 3},
}
