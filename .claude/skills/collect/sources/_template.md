# Fiche source : <Nom affiché>

Modèle pour ajouter une source. Copier sous `<name>.md`, remplir, supprimer les chevrons. Contrat
complet : `docs/SOURCES.md`. Règle : aucune clé obligatoire, aucune connexion à un compte.

```yaml
name: <identifiant, ex. cadremploi>
label: <Nom affiché>
mode: <http | browser>
requires_login: false
available_in: [local]            # [local, cloud] pour une source http
optional_secrets: []
default_limit: <1..50>
freshness_filter: <true | false>
```

Avant d'écrire la fiche, tester une requête simple :
`curl -s -o /dev/null -w "%{http_code}" -A "Mozilla/5.0" "<url de recherche>"`. 200 avec les
offres dans le HTML : mode `http`, écrire un module `scripts/jobhunter/sources/<name>.py` sur le
modèle de `hellowork.py`, l'ajouter à `REGISTRY` et `SOURCES` dans
`scripts/jobhunter/sources/__init__.py`, et un test sur une page fictive dans
`tests/fixtures/html/`. 403 ou page vide : mode `browser`, la fiche suffit (suivre
`_browser.md`).

Ajouter enfin la source à `kit.example.yml` (`enabled`, `limits`), à la table de validation de
`.claude/skills/config/reference.md` et au tableau de `docs/SOURCES.md`.

## URL de recherche

<Format exact, paramètres (intitulé, lieu, fraîcheur, page), nombre d'offres par page.>

## Ce qu'il faut lire

| Champ | Où |
|---|---|
| `title` | |
| `company` | |
| `location` | |
| `contract` | |
| `remote` | |
| `salary` | |
| `url` | |
| `published_at` | |
| `description` | |

## Blocage

<Signes concrets et conduite à tenir.>

## Dernière vérification

<Date et résultat.>
