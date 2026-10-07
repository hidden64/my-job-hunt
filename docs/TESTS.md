# Tests

Deux niveaux : des tests automatiques du moteur, à lancer après chaque modification, et cinq
scénarios de bout en bout à jouer dans une vraie session Claude Code avant de livrer à un
candidat.

## 1. Tests automatiques

```
python3 -m unittest discover -s tests -v      # 30 tests, sans réseau, moins de 2 secondes
python3 tests/live_smoke.py                    # 3 sources HTTP en direct, 2 requêtes chacune
```

| Domaine | Ce qui est vérifié |
|---|---|
| Lecteur YAML | `kit.example.yml` et `candidate.example.yml` lus à l'identique de PyYAML ; sous-ensemble du kit |
| Normalisation | contrats, télétravail, URL sans paramètres de suivi, offres invalides rejetées, description tronquée |
| Dédoublonnage | 24 paires vraies et fausses de `fixtures/dedup-pairs.json` |
| Stockage CSV | BOM et en-tête, fusion entre sources, doublon par URL, statut et date de détection préservés, écriture atomique sur erreur disque, en-tête invalide refusé, 500 offres en moins de 5 s |
| Stockage Airtable | même comportement que le CSV contre une imitation de l'API (création, mise à jour, score) |
| Scoring | bornes, composante inconnue neutre, plafond sur critère obligatoire |
| Sources | lecture des pages fictives France Travail, HelloWork, LinkedIn ; URL construites ; dates relatives ; mots-clés négatifs ; résultat exact de la source de test |
| Passage complet | init, plan, source, notation, source bloquée, fin, résumé, second passage sans doublon, export Excel, changement de statut, refus sans mots-clés, sources navigateur indisponibles en cloud |

## 2. Scénarios de bout en bout

À jouer dans une copie de test du dépôt (« Use this template » vers un dépôt privé jetable), avec
le profil fictif `tests/fixtures/profil-reference.yml` et le CV fictif
`tests/fixtures/cv-reference.pdf`. Noter la date et le résultat dans le tableau final.

### Scénario 1 — Installation locale, stockage CSV

1. Dans la copie, ouvrir Claude Code et coller le prompt d'installation du README.
2. Choisir : terminal ou application, mode local, CSV, heures par défaut.
3. Accepter la planification automatique.
4. Copier `tests/fixtures/cv-reference.pdf` dans `config/cv/`, faire le questionnaire en
   confirmant les champs lus dans le CV.
5. Valider les mots-clés proposés, accepter la première collecte.

Attendu : refus si lancé dans le dépôt modèle ; `config/kit.yml` conforme aux choix ;
`data/offers.csv` créé ; `bash scripts/schedule.sh list` montre 3 entrées ; champs du CV proposés
« (lu dans ton CV) » ; `config/candidate.yml` écrit seulement après accord, identique en substance
au profil de référence ; première collecte avec au moins 10 offres de France Travail, HelloWork ou
LinkedIn, toutes notées ; journal et résumé du jour écrits ; notification système si une offre
dépasse 70 %.

### Scénario 2 — Mode cloud, routines

1. Dans la copie, `passe en mode cloud`.
2. Créer une routine avec `/schedule` (prompt `Lance une collecte Job Hunter.`) et autoriser les
   domaines des sources dans l'environnement cloud.
3. Lancer la routine une fois à la main (« Run now »).

Attendu : sources navigateur notées `unavailable` en une ligne ; France Travail, HelloWork et
LinkedIn `ok` ; offres notées ; commit des données si `auto_commit` est activé ; notification push
si disponible, sinon mention dans le compte rendu.

### Scénario 3 — Changement de profil et renotation

1. « Le télétravail n'est plus obligatoire. »
2. Accepter de renoter.

Attendu : avant → après affiché, accord demandé, `candidate.history.log` complété ; scores
recalculés ; les offres « 100 % présentiel » passent au-dessus de 30.

### Scénario 4 — Source en échec

1. « Active la source test. »
2. Ajouter une offre de titre `__BLOCK__` dans `tests/fixtures/sources/test-offers.json`.
3. « Lance une collecte. »

Attendu : la source de test est `blocked` dans le journal ; les autres sources tournent ; le
passage se termine normalement ; après 3 passages ainsi, le résumé avertit. Retirer ensuite
`__BLOCK__` et la source test.

### Scénario 5 — Deux passages le même jour

1. « Lance une collecte » deux fois à une minute d'écart.

Attendu : le second passage n'ajoute que les offres réellement nouvelles (doublons comptés dans le
journal) ; le résumé du jour cumule les deux passages ; aucune offre en double dans
`data/offers.csv`.

### Scénario complémentaire — Sources navigateur

En local, dans le terminal avec `claude --chrome` et l'extension Claude in Chrome connectée :
« lance une collecte ». Attendu : les 5 sources navigateur sont tentées, chacune `ok` ou `blocked`
proprement, sans dépasser son plafond, et les offres lues ont des URL valides. Mettre à jour la
ligne « Dernière vérification » de chaque fiche.

### Validation du scoring

Faire noter les 30 offres de `tests/fixtures/scoring-sample.json` par Claude avec le profil de
référence (« note ces offres d'essai avec scoring.md, sans les stocker »). Objectif : au moins 25
dans le groupe attendu.

## 3. Registre

| Scénario | Date | Résultat | Remarques |
|---|---|---|---|
| Tests automatiques | 07/10/2026 | 30/30 | — |
| Smoke test des sources HTTP | 07/10/2026 | 3/3 | France Travail 14, HelloWork 21, LinkedIn 7 offres |
| Passage réel simulé (moteur, notation simulée) | 07/10/2026 | OK | 37 offres de 3 sources, 22 doublons fusionnés, journal, résumé, export, second passage sans doublon |
| Passage réel sur copie neuve, profil de référence, notation réelle par Claude selon `scoring.md` | 07/10/2026 | OK | 162 offres reçues, 48 uniques, 48 notées sans erreur : 24 ≥ 70, 19 entre 31 et 69, 5 plafonnées (stage, intérim, freelance, CDD) ; a conduit à la règle de couverture et à la fusion « X / X France » |
| 1. Installation locale | à jouer | | |
| 2. Mode cloud | à jouer | | |
| 3. Changement de profil | à jouer | | |
| 4. Source en échec | à jouer | | |
| 5. Deux passages | à jouer | | |
| Sources navigateur | à jouer | | |
| Validation du scoring | à jouer | | |

Chaque anomalie trouvée devient une carte dans la liste Backlog du tableau Trello JOB HUNTER.
