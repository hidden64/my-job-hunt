# Scoring des offres

Chaque nouvelle offre reçoit un score de 0 à 100 d'adéquation avec le profil, et une
justification d'une ou deux phrases. Le score pilote le résumé du jour, l'alerte et l'export.

## Partage du travail

| Qui | Quoi |
|---|---|
| Claude (skill `collect`, `.claude/skills/collect/scoring.md`) | lit l'offre et le profil, donne une note de 0 à 10 par composante (ou `null` si l'information manque), liste les critères obligatoires violés, écrit la justification |
| Le moteur (`scripts/jobhunter/scoring.py`) | calcule le score final avec les poids de `kit.yml`, applique le plafond, stocke |

Ce partage rend le score reproductible : à notes égales, score égal. Les notes par composante ne
sont pas conservées : après un changement de profil, de poids ou de plafond, « renote mes offres »
(skill `rescore`) refait les notes et les scores.

## Calcul

```
brut       = 100 × Σ(poids × note) / Σ(poids × 10)          sur les composantes notées
couverture = Σ(poids des composantes notées) / Σ(tous les poids)
si couverture < 0,5 : brut = 50 + (brut − 50) × couverture / 0,5
score      = arrondi(brut)
si au moins un critère obligatoire est violé : score = min(score, hard_filter_cap)
```

La couverture empêche une offre presque vide (un titre et une ville, cas fréquent sur LinkedIn)
d'obtenir un score parfait : moins on en sait, plus le score est ramené vers 50. Exemple : titre
10/10 et lieu 8/10, rien d'autre → 80 au lieu de 93.

Composantes et poids par défaut (`scoring.weights`, modifiables de 0 à 10) :

| Composante | Poids | Mesure |
|---|---|---|
| `title_match` | 5 | adéquation de l'intitulé aux intitulés validés |
| `skills_match` | 5 | compétences du profil présentes dans l'offre |
| `experience_level` | 3 | expérience demandée face à celle du candidat |
| `location_remote` | 3 | zone et télétravail |
| `contract` | 3 | type de contrat |
| `salary` | 2 | salaire face au minimum souhaité |
| `education` | 2 | diplôme, cours, spécialisation |

Une composante `null` sort du numérateur et du dénominateur : l'absence d'une information ne
pénalise pas, tant qu'au moins la moitié des poids reste connue (voir couverture ci-dessus).

Plafond (`scoring.hard_filter_cap`, défaut 30) : une offre qui contredit un critère **obligatoire**
ne peut pas dépasser 30, donc jamais atteindre le seuil d'alerte (70 par défaut, toujours supérieur
au plafond).

## Exemples

Profil : Data Analyst junior, Lyon flexible, hybride obligatoire, CDI ou alternance obligatoire.

| Offre | Notes | Violations | Score |
|---|---|---|---|
| Data Analyst H/F, CDI, Lyon, hybride, SQL/Power BI, 1-2 ans | 10, 9, 9, 10, 10, null, 8 | — | 94 |
| Data Scientist, CDI, Lyon, télétravail non précisé, Python | 5, 6, 7, 7, 10, null, 8 | — | 69 |
| Data Analyst, stage 6 mois, Lyon | 10, 8, 10, 8, 0, null, 8 | `contract` | 30 |
| Data Analyst confirmé, CDI, Paris, 100 % présentiel, 5 ans | 9, 8, 2, 0, 10, null, 7 | `remote` | 30 |

## Coût

Seules les nouvelles offres du passage sont notées, par lots de 10, à partir des champs déjà
stockés (pas de page supplémentaire). Au plus 150 offres par passage ; le reste est noté au passage
suivant ou à la demande. Après une modification du profil, `rescore` efface les scores des offres
encore ouvertes (`new`, `seen`) et les renote.

## Validation

`tests/fixtures/scoring-sample.json` contient 30 offres fictives avec l'ordre attendu, à faire
noter par Claude dans une vraie session pour vérifier la cohérence (au moins 25 sur 30 dans le bon
groupe). Le calcul lui-même est couvert par `tests/test_engine.py`.
