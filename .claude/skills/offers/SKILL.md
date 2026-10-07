---
name: offers
description: Consulter et suivre les offres Job Hunter stockées. À utiliser quand le candidat dit "montre mes offres", "les offres au-dessus de 80", "les offres HelloWork de cette semaine", "ouvre l'offre Acme", "j'ai postulé chez Acme", "pas intéressé par celle-là", "marque comme vue", "on m'a refusé chez X", "combien d'offres j'ai".
---

# Skill `offers` — consulter et suivre les offres

Toutes les opérations passent par `scripts/jh` ; jamais d'édition directe du CSV ou d'Airtable.

## Consulter

| Demande | Commande |
|---|---|
| « mes meilleures offres », « au-dessus de 80 » | `scripts/jh list --min-score 80 --status new,seen` |
| « les nouvelles » | `scripts/jh list --status new --order recent` |
| « de cette semaine » | `--since <date du lundi>` |
| « sur HelloWork » | `--source hellowork` |
| « mes candidatures » | `scripts/jh list --status applied --limit 100` |
| « combien d'offres » | `scripts/jh check` → `offers`, puis répartition via `list` si demandé |

Affiche un tableau court : score, titre (lien), entreprise, lieu, contrat, statut. Au plus 20
lignes ; propose « la suite » s'il y en a plus. Montre la justification du score si le candidat
demande « pourquoi ».

## Retrouver une offre

`scripts/jh find "<mots>"` (entreprise, titre, ville). Plusieurs résultats : liste numérotée et
demande laquelle. Aucun : dis-le et propose une recherche plus large.

## Changer un statut

| Le candidat dit | Statut |
|---|---|
| « vue », « je l'ai lue » | `seen` |
| « j'ai postulé », « candidature envoyée » | `applied` |
| « refusé », « pas retenu », « ils ont dit non » | `rejected` |
| « pas intéressé », « ignore », « supprime-la » | `ignored` |
| « remets-la en nouvelle » | `new` |

`scripts/jh set-status <id> <statut>`, puis confirme en une phrase : « Noté : candidature envoyée
chez Acme (Data Analyst). » Les offres ne sont jamais supprimées : `ignored` les sort des listes et
des résumés. Les collectes suivantes ne touchent jamais au statut.

Statut en masse (« marque toutes les offres de plus de 30 jours comme vues ») : liste d'abord ce
qui va changer, demande confirmation, puis applique une par une.

## Ouvrir une offre

Donne le lien `url`. Si le navigateur Claude in Chrome est connecté et que le candidat le demande,
ouvre-la dans un onglet. Ne postule jamais à sa place et ne remplis aucun formulaire.
