---
name: rescore
description: Renoter les offres Job Hunter déjà stockées, après un changement de profil, de critères ou de poids de scoring. À utiliser quand le candidat dit "renote mes offres", "rescore", "recalcule les scores", ou quand les skills profile ou config le proposent.
---

# Skill `rescore` — renoter les offres

1. Explique en une phrase ce qui va se passer et combien d'offres sont concernées :
   `scripts/jh list --status new,seen --limit 1000` → `count`. Les offres auxquelles le candidat a
   postulé, qu'il a refusées ou ignorées ne sont pas renotées, sauf s'il le demande (« renote
   tout » → option `--all`).
2. Au-delà de 150 offres, préviens que ça prendra plusieurs minutes et demande confirmation.
3. `scripts/jh reset-scores` (ou `scripts/jh reset-scores --all`).
4. Boucle de notation de `.claude/skills/collect/SKILL.md`, étape 4, **sans `--run`** :
   `scripts/jh to-score --limit 10`, noter selon `.claude/skills/collect/scoring.md`,
   `scripts/jh apply-scores --file data/runs/work/rescore-<n>.json`, jusqu'à lot vide.
5. `scripts/jh summary` pour rafraîchir le résumé du jour.
6. Compte rendu : nombre d'offres renotées, nombre au-dessus du seuil avant et après, les 3
   meilleures (`scripts/jh list --min-score <seuil> --limit 3`).

Changer seulement les poids (`scoring.weights`) ou le plafond dans `config/kit.yml` demande aussi
un rescore : les notes par composante ne sont pas conservées.
