# Backend de stockage : Airtable (option)

Une base « Job Hunter » dans le compte Airtable **du candidat**, créée par le kit. Le kit n'utilise
jamais une base existante et n'écrit jamais dans le compte de quelqu'un d'autre.

## Ce qu'il faut

- `AIRTABLE_API_KEY` dans `config/secrets.env` : un jeton d'accès personnel Airtable avec les
  droits `data.records:read`, `data.records:write`, `schema.bases:read`, `schema.bases:write`, et
  l'accès à l'espace de travail où créer la base.
- `storage.airtable.base_id` dans `config/kit.yml`, rempli après création.

La mise en place est guidée par le skill `connect` (« utilise Airtable »).

## Implémentation

`scripts/jobhunter/storage.py`, classe `AirtableBackend`, derrière le même contrat que le CSV
(même dédoublonnage, mêmes règles d'upsert).

| Opération | Appel Airtable |
|---|---|
| création de la base | `POST /v0/meta/bases` avec la table `Offres` et ses 16 champs (`scripts/jh airtable-create-base --workspace <wsp...>`) |
| `init` | `GET /v0/meta/bases/<base>/tables` ; crée la table si absente, refuse si des champs manquent |
| lecture | `GET /v0/<base>/Offres`, pages de 100 |
| écriture | `POST` (création) et `PATCH` (mise à jour) par lots de 10, `typecast: true` |
| débit | 5 requêtes par seconde au plus (limite Airtable) |
| échec d'un lot | le lot est écrit dans `data/pending/` et rejoué au début du passage suivant ; le passage continue |

Types des champs : listes à choix pour `contract`, `remote`, `source`, `status` ; nombre entier
pour `score` ; date pour `published_at` ; date et heure pour `detected_at` ; texte long pour
`description`, `score_rationale`, `secondary_sources` ; URL pour `url`.

## Vues

L'API Airtable ne permet pas de créer des vues. Le skill `connect` guide le candidat pour créer en
deux minutes, dans l'interface Airtable, les trois vues prévues :

| Vue | Filtre | Tri |
|---|---|---|
| Nouvelles | `status` = `new` | `detected_at` décroissant |
| À traiter | `score` ≥ seuil d'alerte et `status` = `new` ou `seen` | `score` décroissant |
| Candidatures en cours | `status` = `applied` | `detected_at` décroissant |

## Limites connues

Testé contre une imitation de l'API (tests automatiques), pas contre un vrai compte : à confirmer
lors de la première installation avec Airtable.
