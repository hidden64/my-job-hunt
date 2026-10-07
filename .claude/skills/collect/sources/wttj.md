# Fiche source : Welcome to the Jungle

```yaml
name: wttj
label: Welcome to the Jungle
mode: browser
requires_login: false
available_in: [local]
optional_secrets: []
default_limit: 6
freshness_filter: false
```

Suivre d'abord `_browser.md`. Le site construit ses résultats en JavaScript : une requête simple
renvoie une page vide, d'où le navigateur.

## URL de recherche

```
https://www.welcometothejungle.com/fr/jobs?query=<intitulé>&refinementList%5Boffices.country_code%5D%5B%5D=FR&aroundQuery=<ville>%2C%20France&page=<n>
```

- `page` commence à 1. Une trentaine d'offres par page.
- Sans ville (zone « France ») : retirer `aroundQuery`.
- Si le paramètre `aroundQuery` n'est plus pris en compte (la liste montre d'autres villes), saisir
  la ville dans le champ de localisation de la page puis valider, une seule fois par zone.

## Ce qu'il faut lire sur chaque carte

| Champ | Où |
|---|---|
| `title` | titre de la carte |
| `company` | nom de l'entreprise au-dessus ou sous le titre |
| `location` | ville affichée sur la carte |
| `contract` | étiquette « CDI », « Stage », « Alternance »… |
| `remote` | étiquette « Télétravail occasionnel », « fréquent » ou « total » si présente |
| `salary` | étiquette « Salaire : 40K à 45K € » si présente |
| `url` | lien de la carte, de la forme `https://www.welcometothejungle.com/fr/companies/<entreprise>/jobs/<offre>` |
| `published_at` | « il y a 3 jours » converti en date |
| `description` | vide (pas d'extrait sur la carte) |

## Blocage

Rare. Un bandeau de cookies apparaît à la première visite : le refuser si la liste est masquée.

## Dernière vérification

07/10/2026 : page brute vide en HTTP (rendu JavaScript), confirmé. Parcours navigateur à valider
au premier passage local.
