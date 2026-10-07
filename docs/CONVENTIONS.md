# Conventions du kit

Ces règles s'appliquent à tout ce qui est ajouté au dépôt. Elles existent pour qu'un candidat non
développeur s'y retrouve et pour que les skills restent prévisibles.

## Langue

- **Français** pour tout ce que le candidat lit : messages des skills, résumés, alertes, README,
  documentation, commentaires dans les fichiers d'exemple.
- **Anglais** pour tout ce qui est identifiant : noms de dossiers, de fichiers, de skills, clés
  YAML, en-têtes CSV. Un identifiant ne change pas de nom, une phrase si.

## Skills

- Un skill = un dossier `.claude/skills/<nom>/` avec un `SKILL.md`.
- Nom en minuscules, un seul mot si possible, verbe ou nom d'action : `setup`, `config`,
  `onboarding`, `profile`, `keywords`, `collect`, `summary`, `export`, `rescore`.
- Le `SKILL.md` commence par un front matter `name` et `description`. La description dit quand
  déclencher le skill, en français, avec les formulations typiques du candidat.
- Un skill lit `config/kit.yml` au démarrage et ne contient aucune valeur de configuration en dur.
- Un skill qui écrit dans `config/candidate.yml` affiche un récapitulatif et attend une
  confirmation explicite avant d'écrire.
- Les ressources d'un skill (modèles de prompt, exemples, schémas) sont dans son dossier, jamais
  dans un dossier partagé.

## Moteur, sources et stockage

- Le moteur est `scripts/jobhunter/` (Python 3.8+, bibliothèque standard uniquement), lancé par
  `scripts/jh`. Chaque commande imprime un objet JSON avec `ok` ; en cas d'échec `error` (code
  court en anglais) et `message` (phrase en français pour le candidat).
- Une source = une fiche `.claude/skills/collect/sources/<nom>.md` ; une source HTTP a en plus un
  module `scripts/jobhunter/sources/<nom>.py` enregistré dans `sources/__init__.py`. Noms :
  `france_travail`, `hellowork`, `linkedin`, `wttj`, `apec`, `jobteaser`, `indeed`, `glassdoor`,
  `test`.
- Les backends de stockage sont des classes de `scripts/jobhunter/storage.py` (`CsvBackend`,
  `AirtableBackend`) avec une fiche dans `.claude/skills/collect/storage/`.
- Toute logique qui doit donner le même résultat à chaque fois (dédoublonnage, calcul de score,
  dates, formats de fichiers) va dans le moteur, avec un test dans `tests/test_engine.py`. Le
  jugement (questions, mots-clés, notes par composante, lecture de pages en navigateur) reste dans
  les skills.

## Fichiers de configuration

- Format YAML, extension `.yml`, style bloc uniquement (le moteur a un lecteur YAML minimal
  quand PyYAML est absent : pas de texte multi-ligne `|` ou `>`).
- Clés en `snake_case` anglais : `execution.mode`, `schedule.times`, `storage.backend`,
  `scoring.alert_threshold`.
- Un fichier d'exemple commenté accompagne chaque fichier de config : `kit.example.yml`. Il est
  la référence des valeurs possibles et des valeurs par défaut.
- Les secrets ne sont jamais dans un `.yml`. Ils vont dans `config/secrets.env`, non versionné,
  une variable par ligne en `MAJUSCULES_SNAKE` : `FRANCE_TRAVAIL_CLIENT_ID`, `AIRTABLE_API_KEY`.

## Données

- Le CSV des offres est `data/offers.csv`, UTF-8 avec BOM, séparateur virgule, en-têtes en
  `snake_case` anglais conformes au schéma de `docs/STORAGE.md`. Il n'est écrit que par le moteur.
- L'état des sources est `data/runs/state.json` (JSON, écrit par le moteur).
- Les dates sont en ISO 8601 : `2026-10-07` pour une date, `2026-10-07T08:00:00+02:00` pour un
  instant.
- Journaux : `data/runs/AAAA-MM-JJ-HHMM.md`. Résumés : `data/summaries/AAAA-MM-JJ.md`.
  Exports : `data/exports/offres-AAAA-MM-JJ.xlsx`.

## Commandes en langage naturel

- Chaque skill déclare dans sa description 2 à 4 formulations de déclenchement en français.
- Toutes les formulations sont recensées dans `docs/COMMANDES.md`.
- Une commande qui change quelque chose (profil, config, données) dit ce qu'elle a changé en une
  phrase à la fin.

## Cartes Trello et commits

- Chaque carte Trello a un identifiant `E<epic>.<numéro>` (ex. `E3.4`). Les messages de commit
  commencent par cet identifiant : `E3.4 — dédoublonnage par clé normalisée`.
- Une carte passe en « En revue » quand son code est poussé et ses critères d'acceptation sont
  cochés ; en « Terminé » après validation.
