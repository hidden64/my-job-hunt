# Référence de validation de `config/kit.yml`

Source de vérité pour le skill `config` et pour le skill `setup`. Chaque clé : type, valeurs
permises, défaut, et règles de cohérence. Une valeur hors de ces règles n'est jamais écrite.

## Clés

| Clé | Type | Valeurs permises | Défaut |
|---|---|---|---|
| `schema_version` | entier | `1` (ne pas modifier) | `1` |
| `execution.mode` | chaîne | `local`, `cloud` | `local` |
| `schedule.times` | liste de chaînes | 1 à 6 éléments, format `HH:MM` (00:00 à 23:59), tous distincts, au moins 60 minutes entre deux passages consécutifs (en tenant compte du passage minuit) | `["08:00", "13:00", "19:00"]` |
| `schedule.timezone` | chaîne | identifiant IANA valide (`Europe/Paris`, `America/Montreal`, `Africa/Lome`…) | `Europe/Paris` |
| `storage.backend` | chaîne | `csv`, `airtable` | `csv` |
| `storage.csv.path` | chaîne | chemin relatif à la racine, extension `.csv`, dans `data/` | `data/offers.csv` |
| `storage.csv.auto_commit` | booléen | `true`, `false` | `false` |
| `storage.airtable.base_id` | chaîne | vide, ou commence par `app` suivi de 14 caractères alphanumériques | `""` |
| `storage.airtable.table` | chaîne | non vide, 1 à 50 caractères | `Offres` |
| `sources.enabled` | liste de chaînes | sous-ensemble non vide de : `france_travail`, `hellowork`, `linkedin`, `wttj`, `apec`, `jobteaser`, `indeed`, `glassdoor`, plus `test` (source factice, jamais par défaut) ; sans doublon | les 8 réelles |
| `sources.limits.<source>` | entier | 1 à 50, une entrée par source connue | voir `kit.example.yml` |
| `sources.browser_delay_seconds.min` | entier | 2 à 30 | `2` |
| `sources.browser_delay_seconds.max` | entier | strictement supérieur à `min`, au plus 60 | `6` |
| `sources.http_delay_seconds.min` | entier | 1 à 30 | `1` |
| `sources.http_delay_seconds.max` | entier | strictement supérieur à `min`, au plus 60 | `3` |
| `scoring.alert_threshold` | entier | 0 à 100 | `70` |
| `scoring.hard_filter_cap` | entier | 0 à 50, et strictement inférieur à `scoring.alert_threshold` | `30` |
| `scoring.weights.<composante>` | entier | 0 à 10 ; au moins une composante > 0 ; composantes : `title_match`, `skills_match`, `experience_level`, `location_remote`, `contract`, `salary`, `education` | voir `kit.example.yml` |
| `notifications.channel` | chaîne | `push`, `system`, `none` | `system` |
| `notifications.max_offers_in_alert` | entier | 1 à 5 | `3` |
| `logging.archive_after_days` | entier | 7 à 365 | `30` |
| `logging.show_summary_on_session_start` | booléen | `true`, `false` | `true` |

Toute clé absente de ce tableau est inconnue : la refuser et proposer la clé la plus proche.

## Règles de cohérence entre clés

| Règle | Comportement |
|---|---|
| `notifications.channel: push` exige `execution.mode: cloud` | Refuser `push` en mode local ; proposer `system`. |
| `notifications.channel: system` avec `execution.mode: cloud` | Accepter mais avertir : aucune machine ne recevra la notification ; proposer `push`. |
| `storage.backend: airtable` avec `storage.airtable.base_id` vide | Accepter l'écriture mais signaler que la collecte échouera tant que la base n'est pas créée ; renvoyer vers `setup`. |
| `execution.mode: cloud` avec des sources navigateur dans `sources.enabled` | Accepter ; les sources navigateur sont ignorées à l'exécution. Lister celles concernées. |
| `scoring.hard_filter_cap >= scoring.alert_threshold` | Refuser : une offre violant un critère obligatoire ne doit jamais déclencher une alerte. |

Sources par mode d'accès, pour appliquer ces règles :

| Source | Accès | Disponible en cloud |
|---|---|---|
| `france_travail` | http (site public ; API officielle en option) | oui |
| `hellowork` | http | oui |
| `linkedin` | http (recherche publique, sans connexion) | oui |
| `wttj` | navigateur | non |
| `apec` | navigateur | non |
| `jobteaser` | navigateur | non |
| `indeed` | navigateur | non |
| `glassdoor` | navigateur | non |
| `test` | fichier local (factice) | oui |

## Formulations courantes

| Le candidat dit | Clé | Valeur |
|---|---|---|
| « passe à 2 passages par jour », « deux fois par jour » | `schedule.times` | demander les heures si non précisées ; proposer `["08:00", "19:00"]` |
| « une fois par jour le matin » | `schedule.times` | `["08:00"]` |
| « ajoute un passage à midi » | `schedule.times` | liste actuelle + `"12:00"` |
| « change le fuseau pour Montréal » | `schedule.timezone` | `America/Montreal` |
| « passe en mode cloud », « fais tourner ça dans le cloud » | `execution.mode` | `cloud` |
| « reviens en local » | `execution.mode` | `local` |
| « utilise Airtable », « stocke dans Airtable » | — | renvoyer vers le skill `connect` (il faut un jeton et créer la base) |
| « reviens au CSV » | `storage.backend` | `csv` |
| « désactive Indeed », « enlève Glassdoor » | `sources.enabled` | retirer la source |
| « réactive LinkedIn » | `sources.enabled` | ajouter la source |
| « cherche plus sur HelloWork » | `sources.limits.hellowork` | demander ou proposer +50 %, plafonné à 50, avec l'avertissement captcha |
| « mets le seuil à 80 », « alerte-moi seulement au-dessus de 80 » | `scoring.alert_threshold` | `80` |
| « plus d'alertes », « coupe les notifications » | `notifications.channel` | `none` |
| « commit automatique des offres » | `storage.csv.auto_commit` | `true` |
| « montre-moi ma config », « quels sont mes réglages » | lecture seule | afficher le tableau |

## Format d'un refus

Une phrase sur le problème, une phrase sur la solution, rien d'autre :

> `schedule.times` ne peut pas contenir `"25:00"` : les heures vont de 00:00 à 23:59. Tu voulais
> peut-être `"01:00"` ou `"23:00"` ?

> `scoring.hard_filter_cap` ne peut pas valoir 80 : il doit rester sous le seuil d'alerte (70),
> sinon une offre qui viole un critère obligatoire pourrait te réveiller. Maximum possible : 69.
