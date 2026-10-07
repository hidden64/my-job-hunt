# Job Hunter

Un assistant de recherche d'emploi qui tourne dans Claude Code. Tu décris ton parcours et le poste
que tu vises ; Job Hunter cherche pour toi plusieurs fois par jour sur France Travail, HelloWork,
LinkedIn, et, avec le navigateur, Welcome to the Jungle, l'APEC, Jobteaser, Indeed et Glassdoor. Il
supprime les doublons, note chaque offre selon ton profil, et te prévient quand une offre vaut le
coup. Aucune clé ni inscription n'est nécessaire, et tes données restent dans ta copie.

## Installation

**Prérequis** : un compte GitHub, [Claude Code](https://code.claude.com) installé et connecté à ton
compte Claude, Python 3.8 ou plus (Claude t'aide à l'installer s'il manque).

1. **Crée ta copie.** Sur la page GitHub de ce dépôt : **Use this template** → **Create a new
   repository** → nom au choix → **Private** → valider. Ne clone jamais le dépôt modèle
   lui-même : tes données personnelles y seraient envoyées.
2. **Clone ta copie** sur ton ordinateur (bouton **Code**), ou ouvre-la dans Claude Code sur le
   web.
3. **Ouvre Claude Code dans ce dossier et colle :**

```
Installe Job Hunter : lis CLAUDE.md puis lance le skill setup.
```

Claude te pose quelques questions (où faire tourner les recherches, où stocker les offres, à
quelles heures), planifie les recherches, puis fait ton profil avec toi (avec ton CV si tu en as
un) et te propose des mots-clés à valider. Compte 20 minutes. Une première recherche peut être
lancée tout de suite.

## Local ou cloud ?

| | Local (recommandé) | Cloud |
|---|---|---|
| Où ça tourne | Sur ta machine | Sur l'infrastructure Claude |
| Condition | Ordinateur allumé aux heures prévues | Autoriser l'accès réseau aux sites d'emploi dans l'environnement cloud |
| Sources | 3 sans navigateur, 8 avec l'extension Claude in Chrome | France Travail, HelloWork, LinkedIn |
| Planification | automatique (cron sur Mac et Linux, Planificateur de tâches sur Windows) ou routines de l'application | routines Claude Code (`/schedule` ou claude.ai/code/routines) |
| Alertes | notification sur ta machine | notification push dans l'app Claude si disponible |

Tu peux changer d'avis plus tard : « passe en mode cloud ».

**Mode cloud, accès réseau.** Dans les réglages de ton environnement cloud (« Network access »),
autorise au moins `candidat.francetravail.fr`, `www.hellowork.com` et `www.linkedin.com`. Sinon les
recherches échouent avec une erreur réseau. Détails :
[documentation](https://code.claude.com/docs/en/cloud-environments#network-access).

## Au quotidien

Tu n'as rien à faire : les recherches tournent seules (8 h, 13 h et 19 h par défaut). Quand une
offre dépasse ton seuil (70 % par défaut), tu reçois une alerte. À chaque ouverture de Claude Code
dans ce dossier, le résumé du jour s'affiche.

Quelques phrases utiles (liste complète dans [docs/COMMANDES.md](docs/COMMANDES.md)) :

- « Montre-moi le résumé du jour »
- « Montre mes offres au-dessus de 80 »
- « J'ai postulé chez Acme »
- « Lance une collecte maintenant »
- « Change ma localisation pour Paris »
- « Passe à 2 passages par jour »
- « Exporte mes offres en Excel »

## Les sources

| Source | Comment | Où |
|---|---|---|
| France Travail | site public (API officielle en option : « branche l'API France Travail ») | local et cloud |
| HelloWork | site public | local et cloud |
| LinkedIn | recherche publique, **jamais connecté à ton compte** | local et cloud |
| Welcome to the Jungle, APEC, Jobteaser, Indeed, Glassdoor | navigateur, avec l'extension Claude in Chrome | local |

Job Hunter lit des pages publiques, lentement, sans jamais se connecter à un compte, sans résoudre
de captcha et sans postuler à ta place. Si un site bloque, il s'arrête poliment et réessaie au
passage suivant. Respecte les conditions d'utilisation des sites ; tu peux désactiver une source à
tout moment (« désactive Indeed »).

Les sources navigateur demandent l'extension
[Claude in Chrome](https://code.claude.com/docs/en/chrome) et une session Claude Code dans le
terminal (`claude --chrome`). Leur fonctionnement dans les recherches planifiées n'est pas garanti :
sans navigateur, elles sont simplement sautées et les 3 autres sources tournent.

## Tes données

| Fichier | Contenu | Envoyé sur GitHub |
|---|---|---|
| `config/candidate.yml` | ton profil et tes mots-clés | oui, dans ta copie privée |
| `config/kit.yml` | tes réglages | oui |
| `config/cv/` | ton CV | **non** |
| `config/secrets.env` | clés facultatives | **non** |
| `data/offers.csv` | toutes tes offres (ouvrable dans Excel) | oui |
| `data/summaries/`, `data/runs/` | résumés du jour et journaux | oui |
| `data/exports/` | exports Excel | non |

Rien n'est envoyé à un service tiers. L'option Airtable (« utilise Airtable ») stocke les offres
dans **ta** base Airtable.

## Dépannage

| Problème | Que faire |
|---|---|
| « Ce dépôt est le modèle » à l'installation | Tu as cloné le modèle : crée ta copie avec **Use this template** (étape 1). |
| « Python est introuvable » | Installe Python 3 ([python.org](https://www.python.org/downloads/), sous Windows coche « Add python.exe to PATH »), puis relance. |
| Aucune recherche ne tourne | Machine éteinte aux heures prévues, ou planification absente : `bash scripts/schedule.sh list` (Mac, Linux). Sur Mac, autorise `/usr/sbin/cron` dans Réglages → Confidentialité → Accès complet au disque. Ou dis « lance une collecte ». |
| Une source est « bloquée » | Normal de temps en temps. Après 3 blocages de suite, le résumé te propose de la désactiver. |
| Erreur réseau en mode cloud | Autorise les domaines des sources dans l'accès réseau de l'environnement (voir plus haut). |
| Les sources navigateur sont « indisponibles » | Mode cloud, ou extension Claude in Chrome non connectée (`/chrome` dans Claude Code). |
| Une source renvoie toujours « format de page inattendu » | Le site a changé. Lance `python3 tests/live_smoke.py` et préviens le mainteneur du kit. |
| Trop d'offres hors sujet | « Revois mes mots-clés » : ajoute des mots exclus, retire les intitulés trop larges. |
| Pas assez d'offres | Ajoute des intitulés ou une zone, ou élargis le rayon (« change ma localisation »). |

## Pour aller plus loin

- [docs/COMMANDES.md](docs/COMMANDES.md) : tout ce que tu peux demander.
- [docs/SOURCES.md](docs/SOURCES.md), [docs/STORAGE.md](docs/STORAGE.md),
  [docs/SCORING.md](docs/SCORING.md) : fonctionnement détaillé.
- [docs/TESTS.md](docs/TESTS.md) : tests du kit.
- [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md) : pour le mainteneur du modèle.
