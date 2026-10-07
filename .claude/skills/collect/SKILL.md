---
name: collect
description: Lancer un passage de collecte Job Hunter — interroger les sources d'offres d'emploi, dédoublonner, noter chaque nouvelle offre selon le profil, stocker, écrire le journal et le résumé du jour, et alerter si une offre dépasse le seuil. À utiliser quand le prompt est "Lance une collecte Job Hunter." (prompt des routines planifiées), ou quand le candidat dit "lance une collecte", "cherche des offres maintenant", "relance la recherche", "note les offres en attente".
---

# Skill `collect` — un passage de collecte

Ce skill tourne le plus souvent **sans personne devant l'écran** (routine planifiée). Donc : ne
pose aucune question, ne t'arrête pas sur une erreur de source, va jusqu'au bout, et termine par un
compte rendu court. Toutes les commandes passent par `scripts/jh` (lancé depuis la racine du
dépôt), qui renvoie du JSON.

Références : `docs/SOURCES.md` (sources), `docs/STORAGE.md` (stockage), `scoring.md` (notation),
fiches dans `sources/`.

## Étape 1 — Démarrer

1. Détermine si le navigateur est disponible : les outils Claude in Chrome sont-ils présents dans
   cette session ? Oui → `--browser yes`, non → `--browser no`.
2. `scripts/jh run start --browser yes|no`
   - `"error": "keywords_not_validated"` : arrête-toi. Message : « Pas de collecte : tes mots-clés
     ne sont pas validés. Dis "revois mes mots-clés". »
   - `"error": "python_missing"` : arrête-toi et relaie le message (installer Python 3.8+).
   - `"error": "storage"` ou `"not_found"` : arrête-toi, relaie le message, propose le setup.
   - Sinon garde `run_id` et `plan` (liste ordonnée des sources avec `available`, `limit`,
     `since`, `reason`).

## Étape 2 — Sources HTTP

Pour chaque source du plan avec `mode: "http"` et `available: true`, dans l'ordre :

```
scripts/jh source <name> --run <run_id>
```

Le moteur cherche, normalise, dédoublonne, stocke et note le résultat. Lis seulement `status`,
`received`, `created`, `message`. Un `blocked` ou `error` n'arrête rien : passe à la suivante.

## Étape 3 — Sources navigateur

Seulement si le plan contient des sources `mode: "browser"` avec `available: true` (mode local et
navigateur connecté). Pour chacune, dans l'ordre : lis `sources/_browser.md` puis la fiche
`sources/<name>.md`, et suis-les. Ces sources sont les plus fragiles : au moindre doute (captcha,
page inattendue), note `blocked` et passe à la suivante. Ne passe jamais plus de 10 minutes sur une
source.

Les sources `available: false` sont déjà connues du moteur : ne fais rien pour elles.

## Étape 4 — Noter les nouvelles offres

Boucle jusqu'à épuisement :

1. `scripts/jh to-score --run <run_id> --limit 10` → `batch` (offres avec description), `weights`,
   `components`.
2. Si `batch` est vide, sors de la boucle.
3. Note chaque offre du lot en suivant `scoring.md` : une note de 0 à 10 par composante (ou
   `null` si l'information manque), la liste des critères **obligatoires** violés, une
   justification d'une ou deux phrases en français. Lis `config/candidate.yml` une seule fois
   pour tout le passage.
4. Écris le lot dans `data/runs/work/<run_id>/scores-<n>.json` et lance
   `scripts/jh apply-scores --file data/runs/work/<run_id>/scores-<n>.json`. Le moteur calcule
   le score final avec les poids et le plafond de `kit.yml`.
5. Si `errors` n'est pas vide, corrige les éléments fautifs et relance pour eux seulement.

Limite de sécurité : au plus 15 lots (150 offres) par passage. S'il en reste, elles seront notées
au passage suivant (« note les offres en attente » les traite à la demande) : signale-le dans le
compte rendu.

## Étape 5 — Terminer

```
scripts/jh run finish --run <run_id>
```

Le moteur écrit le journal `data/runs/<run_id>.md`, met à jour `data/runs/state.json` et le résumé
du jour `data/summaries/<date>.md`, archive les vieux journaux, et décide de l'alerte :

- `alert` vide : aucune nouvelle offre au-dessus du seuil, pas d'alerte (c'est voulu).
- `alert.channel = "system"` : le moteur a déjà envoyé la notification système ;
  `system_notification.ok = false` n'est pas grave, mentionne-le simplement.
- `push_needed = true` (canal `push`) : envoie toi-même **une seule** notification avec l'outil
  PushNotification si tu en disposes, titre `alert.title`, message `alert.message`. Si l'outil
  n'est pas disponible ou échoue, mentionne-le dans le compte rendu ; le résumé reste consultable.

Si `storage.csv.auto_commit` vaut `true` dans `config/kit.yml` et que le dépôt a un remote : fais
le commit et le push décrits dans `storage/csv.md`. Un échec n'est pas bloquant.

## Étape 6 — Compte rendu

Court, en français, lisible sur un téléphone :

> **Collecte du 08/10 à 08h00 terminée.** 23 nouvelles offres, dont 4 au-dessus de 70 %.
> Meilleure : Data Analyst chez Acme (Lyon, 86 %).
> Sources : France Travail 12, HelloWork 8, LinkedIn 3 ; Indeed bloqué (captcha).
> Résumé : `data/summaries/2026-10-08.md`.

Ajoute les `warnings` renvoyés par `run finish` s'il y en a.

## Commande « note les offres en attente »

Seulement l'étape 4 sans `--run` (`scripts/jh to-score --limit 10` prend toutes les offres sans
score), puis `scripts/jh summary` pour rafraîchir le résumé du jour.

## Ce que ce skill ne fait jamais

- Se connecter à un compte (LinkedIn ou autre), résoudre un captcha, dépasser un plafond.
- Écrire dans `data/offers.csv` ou Airtable autrement que par `scripts/jh`.
- Modifier `config/candidate.yml` ou `config/kit.yml`.
- Poser une question pendant une routine.
