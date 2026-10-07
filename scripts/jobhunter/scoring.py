"""Calcul déterministe du score à partir des notes par composante données par Claude (docs/SCORING.md).

Claude lit chaque offre et le profil, puis note chaque composante de 0 à 10 (ou null si
l'information manque) et liste les critères obligatoires violés. Ce module transforme ces notes
en score 0-100 avec les poids et le plafond de config/kit.yml. Le même calcul s'applique à chaque
offre : deux offres identiques ont le même score, quel que soit le passage.
"""

COMPONENTS = ["title_match", "skills_match", "experience_level", "location_remote", "contract",
              "salary", "education"]

REQUIRED_KEYS = {"location", "remote", "contract", "experience_years", "languages", "salary_min",
                 "availability"}


class ScoreError(ValueError):
    pass


MIN_COVERAGE = 0.5   # en dessous, le score est ramené vers 50 (information trop maigre)


def compute(components, violations, weights, cap):
    num = den = 0.0
    total = sum(float(weights.get(n, 0) or 0) for n in COMPONENTS)
    for name in COMPONENTS:
        w = float(weights.get(name, 0) or 0)
        v = components.get(name)
        if v is None or w <= 0:
            continue                       # composante inconnue : neutre, ni bonus ni malus
        v = float(v)
        if not 0 <= v <= 10:
            raise ScoreError("%s doit être entre 0 et 10 (reçu %s)" % (name, v))
        num += w * v
        den += w * 10
    if den == 0:
        raise ScoreError("aucune composante notée : impossible de calculer un score")
    raw = 100 * num / den
    coverage = (den / 10) / total if total else 1.0
    if coverage < MIN_COVERAGE:
        # Peu d'informations connues : on ne laisse pas un titre seul faire une offre « parfaite ».
        raw = 50 + (raw - 50) * (coverage / MIN_COVERAGE)
    score = int(round(raw))
    if violations:
        score = min(score, int(cap))
    return max(0, min(100, score))


def validate_item(item):
    if not isinstance(item, dict) or not item.get("id"):
        raise ScoreError("chaque élément doit avoir un id")
    comps = item.get("components") or {}
    unknown = [k for k in comps if k not in COMPONENTS]
    if unknown:
        raise ScoreError("composantes inconnues : %s" % ", ".join(unknown))
    viol = item.get("violations") or []
    if not isinstance(viol, list):
        raise ScoreError("violations doit être une liste")
    rationale = (item.get("rationale") or "").strip()
    if not rationale:
        raise ScoreError("rationale manquante pour %s" % item["id"])
    return comps, viol, rationale
