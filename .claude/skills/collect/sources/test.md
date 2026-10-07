# Fiche source : Source de test

```yaml
name: test
label: Source de test
mode: http
requires_login: false
available_in: [local, cloud]
optional_secrets: []
default_limit: 3
freshness_filter: false
```

Source factice sans réseau, pour vérifier toute la chaîne (collecte, dédoublonnage, scoring,
journal, résumé, alerte) sans dépendre d'un site. Elle n'est **jamais** dans `sources.enabled` par
défaut : on l'active le temps d'un essai (« active la source test »), puis on la retire.

## Exécution

```
scripts/jh source test --run <id>
```

## Comportement

Le moteur lit `tests/fixtures/sources/test-offers.json`. Une requête par couple intitulé × zone :
une offre correspond si son titre contient l'intitulé (sans tenir compte de la casse ni des
accents), si son lieu contient le libellé de la zone ou si elle est en télétravail total, et si son
titre ne contient aucun mot-clé négatif.

| Si le fichier contient une offre de titre | Alors |
|---|---|
| `__BLOCK__` | la source renvoie `blocked`, « blocage simulé » |
| `__ERROR__` | la source renvoie `error`, « erreur simulée » |

## Résultat attendu avec le fichier livré

Intitulé « Data Analyst », zones « Lyon » et « Villeurbanne », négatif « senior » : 2 requêtes,
4 offres remontées, 1 rejetée (sans URL), 2 offres uniques après dédoublonnage (« Data Analyst
(H/F) » chez Acme Analytics et sa republication en minuscules ne font qu'une). Vérifié par
`tests/test_engine.py`.
