---
name: setup
description: Installer ou reconfigurer Job Hunter dans la copie du candidat, en une seule conversation. À utiliser quand le candidat dit "installe Job Hunter", "lance le setup", "configure le kit", "réinstalle", "reconfigure", ou colle le prompt d'installation du README. Vérifie que le dépôt est une copie personnelle et que Python est présent, pose les choix (mode local ou cloud, stockage, horaires), écrit config/kit.yml, crée le stockage, planifie les collectes, puis enchaîne sur le questionnaire d'onboarding.
---

# Skill `setup` — installation en un prompt

Tu installes Job Hunter dans la copie personnelle du candidat. Il n'est pas forcément développeur :
une question à la fois quand il faut choisir, zéro jargon, et à la fin il sait ce qui a été fait et
ce qui va se passer. Détails techniques : `reference.md` (dans ce dossier). Lis-le avant de
commencer. **Aucune clé n'est demandée pendant l'installation.**

## Étape 0 — Garde-fous

1. `bash .claude/skills/setup/scripts/check-remote.sh`
   - `TEMPLATE <url>` : **arrête-toi.** Explique en trois phrases que ce dépôt est le modèle
     partagé, que ses données personnelles y seraient poussées, et comment créer sa copie : sur la
     page GitHub du modèle, « Use this template » → « Create a new repository », visibilité
     **Private**, puis cloner cette copie et relancer le prompt d'installation dedans. Rien
     d'autre.
   - `NO_REMOTE` : avertis que les données ne seront pas sauvegardées en ligne ; continue si le
     candidat est d'accord.
   - `COPY <url>` : continue.
2. `scripts/jh check`
   - `"error": "python_missing"` : Python 3.8+ manque. Guide l'installation selon le système
     (`reference.md`, « Python »), puis relance `scripts/jh check`. Ne continue pas sans Python.
   - Sinon, note `kit`, `candidate`, `keywords_validated`.

## Étape 1 — Installation existante ?

Si `kit` vaut `true`, le kit est déjà installé. Résume les réglages (`scripts/jh sources` et
`config/kit.yml`) et propose : **garder et sortir**, **reconfigurer** (étapes 2 à 5 avec les
valeurs actuelles par défaut), ou **reprendre le profil** (skill `onboarding` ou `profile`). Ne
supprime jamais `data/offers.csv`, `config/candidate.yml` ni l'historique.

## Étape 2 — Quatre choix, un par un

1. **Comment utilises-tu Claude Code ?** Application de bureau (Mac/Windows), terminal, ou Claude
   Code sur le web (claude.ai/code). Sert à l'étape 4, pas écrit dans la config.
2. **Où doivent tourner les recherches ?** Présente le tableau court de `reference.md`. Défaut :
   `local` ; `cloud` si le candidat est sur le web uniquement.
3. **Où stocker les offres ?** `csv` (un fichier dans ce dépôt, rien à configurer, recommandé)
   ou Airtable. Si Airtable : écris d'abord `csv` et dis qu'on branchera Airtable juste après le
   questionnaire avec « utilise Airtable » (skill `connect`), car il faut un jeton.
4. **À quelles heures ?** Défaut 08:00, 13:00, 19:00, fuseau de la machine (`date +%Z` ou
   question). Valide avec `.claude/skills/config/reference.md` (1 à 6 passages, 60 minutes
   d'écart minimum, format HH:MM).

Déduis sans demander : `notifications.channel` = `system` en local, `push` en cloud.

## Étape 3 — Écrire la configuration et créer le stockage

1. Copie `config/kit.example.yml` vers `config/kit.yml`, puis remplace uniquement
   `execution.mode`, `schedule.times`, `schedule.timezone`, `storage.backend`,
   `notifications.channel`. Garde tous les commentaires.
2. Si `config/secrets.env` n'existe pas : `cp config/secrets.example.env config/secrets.env`.
   Vérifie `git check-ignore config/secrets.env` (doit répondre). Ne l'ouvre pas.
3. `scripts/jh init-storage` → `created` ou `exists`. `HEADER_MISMATCH` ou erreur : relaie, ne
   corrige pas à la main.
4. `scripts/jh sources --browser <yes|no>` (yes si les outils Claude in Chrome sont présents dans
   cette session) et dis en une phrase quelles sources tourneront :
   « En local avec le navigateur : les 8 sources. Sans navigateur : France Travail, HelloWork et
   LinkedIn ; les 5 autres demandent l'extension Claude in Chrome (`/chrome`). »

## Étape 4 — Planifier les collectes

Suis `reference.md`, section « Planification », selon la surface et le mode :

- **Local, macOS ou Linux, commande `claude` disponible** (recommandé, automatique) :
  propose-le, puis sur accord `bash scripts/schedule.sh install <heures>`. Vérifie avec
  `bash scripts/schedule.sh list`.
- **Local, Windows** : sur accord,
  `powershell -ExecutionPolicy Bypass -File scripts\schedule.ps1 install <heures>`.
- **Local sans commande `claude`** (application de bureau seule) : guide la création des routines
  « Local » dans l'application, une par heure (étapes exactes dans `reference.md`).
- **Cloud** : guide la création des routines (`/schedule` dans le terminal, ou
  https://claude.ai/code/routines), puis l'autorisation réseau de l'environnement cloud (liste des
  domaines dans `reference.md`). Sans cette autorisation, les sources échouent en `error` réseau.

Le prompt de chaque routine est toujours, mot pour mot : `Lance une collecte Job Hunter.`

Si le candidat préfère ne rien planifier : il pourra dire « lance une collecte » quand il veut.

## Étape 5 — Récapitulatif

```
Job Hunter est installé.
- Mode : local (ta machine)
- Sources : France Travail, HelloWork, LinkedIn (+ 5 avec le navigateur)
- Passages : 08:00, 13:00, 19:00 (Europe/Paris), planifiés par cron
- Stockage : data/offers.csv
- Alertes : notification sur ta machine au-dessus de 70 %
- À chaque ouverture de Claude Code dans ce dossier, le résumé du jour s'affiche.
On passe à ton profil.
```

## Étape 6 — Enchaîner

Lance le skill `onboarding` directement (sauf si `candidate` vaut `true` : propose alors `profile`).
Si le stockage Airtable avait été demandé, lance le skill `connect` après les mots-clés.

## Jamais

Écrire dans le dépôt modèle. Supprimer des données du candidat. Demander une clé. Se connecter à
LinkedIn. Installer une tâche planifiée sans l'accord du candidat.
