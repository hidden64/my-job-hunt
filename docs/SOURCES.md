# Sources d'offres

Ce document fait foi pour tout ce qui touche aux sources : modes d'accès, contrat, plafonds,
gestion des échecs, et liste des sources. Le skill `collect` enchaîne les sources sans rien savoir
de chacune : le moteur (`scripts/jh`) exécute les sources HTTP, Claude exécute les sources
navigateur en suivant leur fiche.

## Règle zéro clé

**Aucune source n'exige de clé, de compte ou d'inscription pour fonctionner.** Une clé ne peut
être qu'un accélérateur optionnel (aujourd'hui : l'API officielle France Travail). Sans clé, la
source marche quand même. Le setup ne demande jamais de clé.

## Modes d'accès

| Mode | Qui l'exécute | Où | Principe |
|---|---|---|---|
| `http` | le moteur Python (`scripts/jh source <nom>`) | local et cloud | requête HTTP simple sur une page publique rendue côté serveur, lecture du HTML |
| `browser` | Claude, avec l'extension Claude in Chrome | local uniquement | ouverture de la page dans le navigateur, lecture des résultats affichés |

En mode cloud, l'environnement doit autoriser l'accès réseau aux domaines des sources HTTP
(voir « Mode cloud » dans le README). Sans navigateur (mode cloud, ou extension non connectée),
les sources `browser` sont notées `unavailable` et le passage continue.

## Les sources

| Source | Nom | Mode | Local | Cloud | Plafond par défaut | Vérifiée en direct |
|---|---|---|---|---|---|---|
| France Travail | `france_travail` | http (API en option) | oui | oui | 20 | oui, 07/10/2026 |
| HelloWork | `hellowork` | http | oui | oui | 8 | oui, 07/10/2026 |
| LinkedIn (recherche publique) | `linkedin` | http | oui | oui | 5 | oui, 07/10/2026 |
| Welcome to the Jungle | `wttj` | browser | oui | non | 6 | à vérifier au premier passage local |
| APEC | `apec` | browser | oui | non | 6 | à vérifier au premier passage local |
| Jobteaser | `jobteaser` | browser | oui | non | 6 | à vérifier au premier passage local |
| Indeed | `indeed` | browser | oui | non | 4 | à vérifier au premier passage local |
| Glassdoor | `glassdoor` | browser | oui | non | 4 | à vérifier au premier passage local |
| Source de test | `test` | http (fichier local) | oui | oui | 3 | tests automatiques |

Pourquoi ce partage : le 07/10/2026, France Travail, HelloWork et la recherche publique LinkedIn
répondent à une requête simple avec des pages lisibles. Welcome to the Jungle construit ses
résultats en JavaScript (la page brute est vide), et APEC, Indeed, Glassdoor et Jobteaser
refusent les requêtes simples (HTTP 403). Ces cinq-là demandent un vrai navigateur.

## Contrat d'une source

Chaque source a une fiche `.claude/skills/collect/sources/<nom>.md` qui déclare ses propriétés
et décrit comment chercher. Les sources HTTP ont en plus un module
`scripts/jobhunter/sources/<nom>.py`.

### Propriétés

| Propriété | Valeurs | Rôle |
|---|---|---|
| `name` | voir tableau | identifiant, identique à la clé dans `kit.yml` et au champ `source` des offres |
| `label` | texte | nom affiché au candidat |
| `mode` | `http`, `browser` | mode d'accès |
| `requires_login` | `false` | toujours `false` : aucune source ne se connecte à un compte du candidat |
| `available_in` | `[local, cloud]` ou `[local]` | `http` partout, `browser` en local seulement |
| `optional_secrets` | liste ou vide | clés facultatives qui améliorent la source (jamais obligatoires) |
| `default_limit` | entier 1 à 50 | plafond de requêtes par passage, repris dans `kit.example.yml` |
| `freshness_filter` | `true`, `false` | la source sait-elle limiter aux offres récentes |

### Recherche

```
search(keywords, criteria, limit, since) -> { offers, requests_used, status, message, queries }
```

| Entrée | Contenu |
|---|---|
| `keywords` | bloc `keywords` validé de `config/candidate.yml` : `titles`, `skills`, `negative`, `locations` |
| `criteria` | bloc `criteria` du profil |
| `limit` | plafond de requêtes (`kit.yml` → `sources.limits.<nom>`) |
| `since` | instant du dernier passage réussi de cette source (`data/runs/state.json`), ou vide |

| Sortie | Contenu |
|---|---|
| `offers` | offres brutes avec `title`, `company`, `location`, `contract`, `remote`, `salary`, `url`, `published_at`, `description` (texte libre accepté : le moteur normalise) |
| `requests_used` | nombre de pages réellement chargées |
| `status` | `ok`, `blocked` (captcha, connexion forcée, 403/429), `error` (réseau, page inattendue), `unavailable` (pas dans ce mode) |
| `message` | une phrase pour le journal, vide si `ok` |
| `queries` | `[{title, location, count}]`, sert à repérer les intitulés qui ne ramènent rien |

Une source ne juge pas la pertinence : elle remonte ce qui correspond aux mots-clés, applique les
mots-clés négatifs sur le titre, et laisse le scoring trier.

### Ordre des requêtes

Parcours en largeur : la première page de chaque couple intitulé × zone, dans l'ordre de
`keywords.titles` puis de `keywords.locations`, puis les pages suivantes tant que le plafond le
permet. Le premier intitulé et la première zone sont donc toujours couverts.

Si `since` est connu, la source ne demande que les offres récentes (France Travail : paramètre
`emission` en jours ; HelloWork : `d=d` ou `d=w` ; LinkedIn : `f_TPR`). Au premier passage, elle
remonte 14 à 30 jours selon la source.

## Plafonds, délais, blocages

| Règle | Détail |
|---|---|
| Plafond | `sources.limits.<nom>`, jamais dépassé |
| Délai | aléatoire entre deux pages : `http_delay_seconds` (1 à 3 s) et `browser_delay_seconds` (2 à 6 s) dans `kit.yml` |
| Arrêt immédiat | captcha, page de vérification anti-robot, page de connexion, HTTP 401/403/429 : `status = blocked`, plus aucune requête sur cette source pendant ce passage |
| Nouvelle tentative | une seule, 5 s plus tard, uniquement sur une coupure réseau. Jamais après un blocage. |
| Pas de contournement | pas de résolution de captcha, pas de proxy, pas de changement d'identité, pas de connexion |
| Ordre | sources `http` d'abord, puis `browser`, dans l'ordre de `sources.enabled` |

## Gestion des échecs

Un passage ne s'arrête jamais à cause d'une source.

| Événement | Ce qui se passe |
|---|---|
| source `unavailable` | notée dans le journal, une ligne groupée |
| `blocked` ou `error` | notée dans le journal avec le message ; pour une source navigateur, Claude enregistre une capture ou le texte de la page dans `data/runs/evidence/` (non versionné) |
| offre malformée (titre ou URL absents) | écartée, comptée en « rejetées » avec la raison |
| 3 échecs consécutifs d'une source | avertissement dans le résumé quotidien |
| 7 jours sans offre d'une source active | avertissement dans le résumé quotidien |
| 7 jours sans résultat pour un intitulé | avertissement : revoir les mots-clés |

L'état par source (`last_success_at`, `consecutive_failures`, `last_offer_at`) et par intitulé
est tenu par le moteur dans `data/runs/state.json`.

## Commandes du moteur

```
scripts/jh run start [--browser yes|no]          # crée le passage et donne le plan
scripts/jh source <nom> --run <id>               # source http : cherche, normalise, stocke
scripts/jh ingest <nom> --run <id> --file f.json --requests N [--queries '[...]']   # source navigateur
scripts/jh source-result <nom> --run <id> --status blocked --requests N --message "..."
scripts/jh run finish --run <id>                 # journal, état, résumé, alerte
```

## Respect des sites

Le kit lit des pages publiques, plus lentement qu'un humain qui cherche activement, sans jamais se
connecter. Il ne republie rien et renvoie toujours vers l'offre d'origine. Le candidat reste
responsable du respect des conditions d'utilisation de chaque site et peut désactiver une source à
tout moment (« désactive Indeed »).
