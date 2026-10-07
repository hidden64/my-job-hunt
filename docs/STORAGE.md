# Stockage des offres

Ce document fait foi pour tout ce qui touche aux offres stockées : le schéma d'une offre, le
contrat que chaque backend implémente, et la façon dont les skills y accèdent. Deux backends
existent : `csv` (défaut, fichier dans le dépôt) et `airtable` (base dans le compte du candidat).
Les skills ne connaissent jamais le backend actif : ils parlent au contrat, le contrat parle au
backend désigné par `storage.backend` dans `config/kit.yml`.

## Schéma d'une offre

Identifiants en anglais (voir `docs/CONVENTIONS.md`), un enregistrement par offre unique.

| Champ | Type | Obligatoire | Valeurs / format |
|---|---|---|---|
| `id` | texte | oui | clé de dédoublonnage, calculée selon la règle de la section « Dédoublonnage » (E3.4). Jamais fournie par une source. |
| `title` | texte | oui | intitulé tel qu'affiché par la source, nettoyé des espaces superflus |
| `company` | texte | oui | nom de l'entreprise ; `inconnue` si la source ne le donne pas |
| `location` | texte | oui | `Ville (département)` quand connu, ex. `Lyon (69)` ; `Télétravail total` si pas de lieu ; `inconnue` sinon |
| `contract` | choix | oui | `cdi`, `cdd`, `alternance`, `stage`, `freelance`, `interim`, `autre` |
| `remote` | choix | oui | `none`, `hybrid`, `full`, `unknown` |
| `salary` | texte | non | tel qu'affiché par la source (`38-42k€ brut annuel`), vide si absent. Jamais inventé ni converti. |
| `url` | url | oui | lien direct vers l'offre sur la source, sans paramètres de tracking |
| `source` | choix | oui | `france_travail`, `hellowork`, `linkedin`, `wttj`, `apec`, `jobteaser`, `indeed`, `glassdoor`, `test` |
| `secondary_sources` | texte | non | autres sources où la même offre a été vue, format `source:url;source:url` |
| `published_at` | date | non | `AAAA-MM-JJ`, vide si la source ne donne pas de date absolue fiable |
| `detected_at` | datetime | oui | instant du premier passage qui a vu l'offre, ISO 8601 avec fuseau |
| `status` | choix | oui | `new`, `seen`, `applied`, `rejected`, `ignored` ; `new` à la création |
| `score` | entier | non | 0 à 100, vide tant que le scoring n'a pas tourné |
| `score_rationale` | texte | non | 1 à 2 phrases en français, vide tant que le scoring n'a pas tourné |
| `description` | texte long | non | extrait de l'offre (max 2 000 caractères) utilisé par le scoring ; vide si la source ne l'expose pas |

Ordre des colonnes, pour le CSV et pour toute vue tabulaire :

```
id,title,company,location,contract,remote,salary,url,source,secondary_sources,published_at,detected_at,status,score,score_rationale,description
```

### Normalisation des valeurs à l'entrée

Les sources renvoient des libellés variés. Le contrat normalise avant stockage :

| Champ | Règle |
|---|---|
| `contract` | `CDI` → `cdi` ; `CDD`, `Contrat à durée déterminée` → `cdd` ; `Alternance`, `Apprentissage`, `Contrat pro` → `alternance` ; `Stage`, `Internship` → `stage` ; `Freelance`, `Indépendant`, `Mission` → `freelance` ; `Intérim`, `Travail temporaire` → `interim` ; tout le reste → `autre` |
| `remote` | mention « télétravail total », « full remote », « 100 % télétravail » → `full` ; « hybride », « 2 jours », « télétravail partiel », « possible » → `hybrid` ; « sur site », « présentiel », « pas de télétravail » → `none` ; rien → `unknown` |
| `title` | espaces multiples réduits, suppression des espaces en début et fin ; on **garde** les mentions H/F dans `title` (elles ne sont retirées que pour calculer `id`) |
| `url` | suppression des paramètres `utm_*`, `ref`, `trk`, `src`, `from` ; conservation du reste |
| `description` | texte brut sans HTML, tronqué à 2 000 caractères sur une fin de phrase si possible |

## Contrat des backends

Implémentation : `scripts/jobhunter/storage.py`. La classe `Store` porte toute la logique
(dédoublonnage, fusion, règles ci-dessous) ; les backends `CsvBackend` et `AirtableBackend` ne font
que charger et persister. Les skills appellent ces opérations via `scripts/jh` (voir
`.claude/skills/collect/storage/README.md`).

| Opération | Entrée | Sortie | Règles |
|---|---|---|---|
| `init()` | aucune | `ok` ou erreur explicite | Crée le support s'il n'existe pas (fichier avec en-tête, ou base et table). Idempotent : ne touche pas à un support existant. Vérifie que le schéma du support correspond au schéma ci-dessus et signale tout écart au lieu de le corriger silencieusement. |
| `exists(id)` | `id` | `true` / `false` | Recherche exacte sur `id`. |
| `exists_url(url)` | `url` normalisée | `id` trouvé ou `null` | Permet le dédoublonnage par URL (E3.4). |
| `upsert(offer)` | une offre complète au schéma | `created` ou `updated` | Si `id` existe : met à jour tous les champs fournis **sauf** `detected_at` (on garde la première détection), `status` (jamais écrasé par une collecte), `score` et `score_rationale` (écrasés seulement si fournis). Si `source` diffère de celle stockée : ajoute la nouvelle dans `secondary_sources`. Si `id` n'existe pas : crée avec `status = new`. |
| `list(filters)` | filtres optionnels : `status`, `source`, `min_score`, `detected_since` (datetime), `limit`, `order_by` (`score desc` par défaut) | liste d'offres | Utilisée par le résumé, l'alerte, l'export et le rescoring. |
| `update_status(id, status)` | `id`, valeur de `status` | `ok` ou `not_found` | Seule façon de changer `status`. Valeur hors liste refusée. |
| `update_score(id, score, rationale)` | `id`, entier 0 à 100, texte | `ok` ou `not_found` | Seule façon d'écrire un score hors `upsert`. |
| `count_new_since(datetime)` | instant ISO | entier | Nombre d'offres dont `detected_at` est postérieur à l'instant. Alimente le résumé et l'alerte. |

### Garanties communes

- **Atomicité** : une opération d'écriture réussit entièrement ou ne change rien. Pour le CSV :
  écriture dans un fichier temporaire puis renommage. Pour Airtable : lots de 10 et file
  `data/pending/` en cas d'échec.
- **Pas de doublon d'`id`** : `upsert` est la seule porte d'entrée et vérifie `exists` avant.
- **Pas de suppression** : aucune opération ne supprime une offre. Une offre non pertinente passe
  en `status = ignored`.
- **Erreur explicite** : une opération qui échoue renvoie une erreur lisible (fichier illisible,
  base injoignable, schéma différent). Le skill appelant logue et continue, il ne retente pas en
  boucle.

## Résolution du backend

```
backend = kit.yml → storage.backend        # csv | airtable
code    = scripts/jobhunter/storage.py → CsvBackend | AirtableBackend
fiche   = .claude/skills/collect/storage/<backend>.md
```

Un backend mal configuré (fichier absent, jeton Airtable manquant, base vide) renvoie une erreur
explicite ; le skill appelant la relaie et propose la correction (setup, « utilise Airtable », ou
« reviens au CSV »).

## Dédoublonnage

Une même offre apparaît souvent sur plusieurs sites, avec un titre ou un lieu écrit différemment.
Deux règles, appliquées dans cet ordre par `upsert` :

1. **Clé normalisée.** `id` = 16 premiers caractères hexadécimaux du SHA-1 de
   `entreprise|titre|ville`, chaque partie normalisée :

   | Partie | Normalisation |
   |---|---|
   | entreprise | minuscules, sans accents, sans forme juridique (SAS, SASU, SA, SARL, EURL, Inc, Ltd, GmbH…), ponctuation remplacée par des espaces |
   | titre | minuscules, sans accents, sans mention de genre (H/F, F/H, (H/F), M/F, H/F/X…), sans contenu entre parenthèses ou crochets (niveaux, références), ponctuation remplacée par des espaces sauf `+` et `#` (C++, C#) |
   | ville | minuscules, sans accents, sans code postal ni département ni région, sans arrondissement (« Lyon 3e », « Paris 2e Arrondissement » → « lyon », « paris »), « St » → « saint » ; formats France Travail (« 69 - LYON 03 »), HelloWork (« Lyon 3e - 69 ») et LinkedIn (« Lyon, Auvergne-Rhône-Alpes, France ») reconnus |

2. **URL déjà vue.** Si la clé est nouvelle mais que l'URL (sans paramètres de suivi, sans `www.`)
   correspond à une offre stockée, y compris dans ses `secondary_sources`, c'est la même offre.

Quand un doublon est détecté : la première offre stockée est conservée ; la nouvelle source est
ajoutée à `secondary_sources` (`source:url`) ; les champs vides (salaire, date, description,
télétravail inconnu, contrat « autre ») sont complétés ; `detected_at`, `status` et `score` ne
changent pas.

Choix assumés, vérifiés par 24 paires de test (`tests/fixtures/dedup-pairs.json`) : Villeurbanne
n'est pas Lyon ; « Data Analyst » et « Data Analyst Finance » sont deux offres ; une filiale et son
groupe sont deux entreprises. Mieux vaut un doublon visible qu'une offre perdue.

## Backends

| Backend | Fiche | Carte | Particularités |
|---|---|---|---|
| `csv` | `.claude/skills/collect/storage/csv.md` | E3.2 | `data/offers.csv`, UTF-8 avec BOM, écriture atomique, commit Git optionnel |
| `airtable` | `.claude/skills/collect/storage/airtable.md` | E3.3 | base créée par le kit dans le compte du candidat, table `Offres`, 3 vues à créer à la main (guidé), lots de 10, file `data/pending/` |

Dans Airtable, les champs à choix (`contract`, `remote`, `source`, `status`) sont des
`singleSelect` dont les options sont exactement les valeurs du schéma ; `score` est un `number`
entier ; `published_at` une `date` ; `detected_at` une `dateTime` ; `description` et
`score_rationale` du `multilineText` ; le reste du `singleLineText` ou `url`.
