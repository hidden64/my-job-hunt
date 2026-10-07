# Ce que tu peux dire à Claude

Dans Claude Code, ouvert dans ta copie de Job Hunter. Les formulations sont des exemples : dis-le
avec tes mots.

## Installer et régler

| Tu dis | Ce qui se passe | Skill |
|---|---|---|
| « Installe Job Hunter » | installation complète, puis profil | `setup` |
| « Montre-moi ma config » | tes réglages en clair | `config` |
| « Passe à 2 passages par jour », « ajoute un passage à midi » | nouveaux horaires, replanification | `config` |
| « Passe en mode cloud », « reviens en local » | changement de mode | `config` |
| « Désactive Indeed », « réactive Jobteaser » | sources actives | `config` |
| « Mets le seuil d'alerte à 80 » | seuil des alertes et du résumé | `config` |
| « Coupe les notifications » | plus d'alertes, le résumé reste | `config` |
| « Branche l'API France Travail » | option : plus de détails sur les offres France Travail | `connect` |
| « Utilise Airtable », « reviens au CSV » | option : stockage dans ton Airtable | `connect` |

## Ton profil

| Tu dis | Ce qui se passe | Skill |
|---|---|---|
| « Crée mon profil », « voici mon CV » | questionnaire complet, avec ton CV si tu en as un | `onboarding` |
| « Montre mon profil » | récapitulatif | `profile` |
| « Change ma localisation pour Paris », « j'ai eu mon diplôme », « je cherche aussi en CDD », « le télétravail n'est plus obligatoire » | modification ciblée, avec ton accord | `profile` |
| « Revois mes mots-clés », « montre mes mots-clés », « ajoute l'intitulé Data Engineer junior », « enlève senior » | mots-clés de recherche | `keywords` |

## Les recherches

| Tu dis | Ce qui se passe | Skill |
|---|---|---|
| « Lance une collecte », « cherche des offres maintenant » | un passage complet tout de suite | `collect` |
| « Note les offres en attente » | note les offres restées sans score | `collect` |
| « Renote mes offres » | recalcule les scores après un changement de profil | `rescore` |

## Tes offres

| Tu dis | Ce qui se passe | Skill |
|---|---|---|
| « Montre-moi le résumé du jour », « quoi de neuf ? », « et hier ? » | résumé avec les meilleures offres | `summary` |
| « Comment s'est passée la dernière collecte ? », « pourquoi Indeed ne marche pas ? » | journal expliqué | `summary` |
| « Montre mes offres au-dessus de 80 », « les nouvelles », « celles de HelloWork cette semaine » | liste filtrée | `offers` |
| « J'ai postulé chez Acme », « pas intéressé par celle-là », « on m'a refusé chez X » | suivi des candidatures | `offers` |
| « Mes candidatures » | offres où tu as postulé | `offers` |
| « Exporte mes offres en Excel » | classeur mis en forme dans `data/exports/` | `export` |

## Dans un terminal (facultatif)

```
scripts/jh check                     # état de l'installation
scripts/jh summary                   # résumé du jour
scripts/jh list --min-score 70       # meilleures offres
bash scripts/schedule.sh list        # collectes planifiées (macOS, Linux)
python3 tests/live_smoke.py          # les sites répondent-ils ?
```
