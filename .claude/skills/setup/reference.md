# Référence du skill `setup`

## Les deux modes, pour le candidat

| | Local | Cloud |
|---|---|---|
| Où ça tourne | Sur ta machine | Sur l'infrastructure Claude |
| Condition | Machine allumée (et session ouverte) aux heures prévues | Aucune côté machine ; autoriser l'accès réseau aux sites d'emploi dans l'environnement cloud |
| Sources | France Travail, HelloWork, LinkedIn, plus Welcome to the Jungle, APEC, Jobteaser, Indeed et Glassdoor avec l'extension Claude in Chrome | France Travail, HelloWork, LinkedIn |
| Alertes | Notification sur ta machine | Notification dans l'app Claude si les notifications push sont actives (sinon résumé à l'ouverture) |
| Pour qui | Ton ordinateur est souvent allumé | Tu veux que ça tourne sans y penser |

Un passage manqué (machine éteinte) n'est pas rattrapé ; le suivant couvre les offres publiées
depuis le dernier passage réussi.

## Python

Le moteur (`scripts/jh`) demande Python 3.8 ou plus, sans aucune bibliothèque à installer.

| Système | Vérifier | Installer |
|---|---|---|
| macOS | `python3 --version` | si absent : `xcode-select --install`, ou l'installeur de https://www.python.org/downloads/ |
| Windows | `python --version` | `winget install Python.Python.3.12`, ou https://www.python.org/downloads/ en cochant « Add python.exe to PATH » |
| Linux | `python3 --version` | `sudo apt install python3` (Debian, Ubuntu) ou équivalent |
| Cloud | présent | — |

Sous Windows, les commandes du kit passent par Git Bash, installé avec Git (Claude Code l'utilise
déjà).

## En-tête de `data/offers.csv`

Défini par `docs/STORAGE.md`, écrit par `scripts/jh init-storage`. Les scripts
`scripts/init-csv.sh` et `scripts/check-remote.sh` de ce dossier restent utilisables sans Python.

## `config/secrets.env`

Copié vide depuis `config/secrets.example.env`, jamais versionné, jamais lu par Claude (règle de
`.claude/settings.json`). Rempli seulement si le candidat branche une option (skill `connect`).

## Prompt de routine

```
Lance une collecte Job Hunter.
```

## Planification

Une exécution par heure de `schedule.times`.

### Local, macOS et Linux : `scripts/schedule.sh` (recommandé)

```
bash scripts/schedule.sh install 08:00 13:00 19:00
bash scripts/schedule.sh list
bash scripts/schedule.sh remove
```

Ajoute à la crontab du candidat une ligne par heure qui lance
`claude -p "Lance une collecte Job Hunter." --permission-mode acceptEdits` dans le dossier du
dépôt, avec un journal dans `data/runs/work/cron.log`. Les autorisations nécessaires (moteur,
écriture dans `data/`) sont déjà dans `.claude/settings.json`. Prérequis : la commande `claude`
(Claude Code en ligne de commande, connecté au compte du candidat). Les heures sont celles de la
machine.

Sur macOS, si les collectes ne tournent pas, cron peut avoir besoin de l'accès complet au disque :
Réglages Système → Confidentialité et sécurité → Accès complet au disque → ajouter `/usr/sbin/cron`.

Sources navigateur en planifié : non documenté par Claude Code. Par défaut la tâche tourne sans
navigateur (3 sources). Pour essayer avec : d'abord une collecte à la main dans le terminal avec
`claude --chrome`, puis si tout va bien `JH_CHROME=1 bash scripts/schedule.sh install <heures>`.

### Local, Windows : `scripts/schedule.ps1`

```
powershell -ExecutionPolicy Bypass -File scripts\schedule.ps1 install 08:00 13:00 19:00
powershell -ExecutionPolicy Bypass -File scripts\schedule.ps1 list
powershell -ExecutionPolicy Bypass -File scripts\schedule.ps1 remove
```

Crée une tâche du Planificateur de tâches par heure (démarrage au plus tôt si la machine était
éteinte), avec un journal dans `data\runs\work\schedule.log`.

### Local, application de bureau sans commande `claude`

1. Onglet **Code**, puis **Routines** (ou « Scheduled »), puis **New routine**.
2. Choisir **Local**, dossier : la copie de Job Hunter.
3. Prompt : `Lance une collecte Job Hunter.`
4. Fréquence : tous les jours à l'heure voulue.
5. Mode d'autorisation de la routine : « Accept edits » (ou équivalent), pour ne pas bloquer sur
   une demande d'autorisation.
6. Enregistrer, recommencer pour chaque heure.

L'application doit être ouverte à l'heure dite. Les noms de menu viennent de la documentation au
07/10/2026 ; s'ils ont changé, chercher « Routines » ou « Scheduled tasks ».

### Cloud

Terminal : `/schedule`, puis suivre l'assistant (dépôt : la copie du candidat, jamais le modèle ;
prompt ; heure). Web : https://claude.ai/code/routines. Une routine par heure, intervalle minimum
1 heure.

**Accès réseau** (obligatoire en cloud) : dans les réglages de l'environnement cloud (menu de
l'environnement dans la barre de titre de la session, puis « Edit »), « Network access » : niveau
« Limited » avec ces domaines autorisés, ou un niveau plus large :

```
candidat.francetravail.fr
www.hellowork.com
www.linkedin.com
```

Avec les options : `entreprise.francetravail.fr`, `api.francetravail.io` (API France Travail),
`api.airtable.com` (Airtable). Documentation :
https://code.claude.com/docs/en/cloud-environments#network-access

## Vérification avant l'onboarding

- `scripts/jh check` : `kit: true`, aucun problème autre que « profil absent ».
- `bash scripts/schedule.sh list` (ou la liste des routines) montre une entrée par heure, ou le
  candidat a choisi le lancement manuel.
