# Fiche source : APEC

```yaml
name: apec
label: APEC
mode: browser
requires_login: false
available_in: [local]
optional_secrets: []
default_limit: 6
freshness_filter: false
```

Suivre d'abord `_browser.md`. L'APEC publie les offres cadres et jeunes diplômés (bac+3 et plus).
Le site refuse les requêtes simples (HTTP 403) et charge ses résultats en JavaScript.

## URL de recherche

```
https://www.apec.fr/candidat/recherche-emploi.html/emploi?motsCles=<intitulé>&page=<n>
```

- `page` commence à 0. Une vingtaine d'offres par page.
- Zone : le site attend un code de lieu interne. Après le premier chargement, saisir la ville de la
  zone dans le champ « Lieu », choisir la suggestion correspondante, valider, puis réutiliser l'URL
  obtenue (elle contient le paramètre `lieux=`) pour les pages suivantes et les autres intitulés
  sur la même zone.
- Si le profil est en cours de diplôme ou diplômé depuis moins de 2 ans
  (`education.degrees[].status` / `year` dans `config/candidate.yml`), cocher le filtre « Jeune
  diplômé » s'il est proposé.

## Ce qu'il faut lire sur chaque carte

| Champ | Où |
|---|---|
| `title` | intitulé de l'offre |
| `company` | nom de l'entreprise (parfois « Entreprise confidentielle » : le recopier) |
| `location` | ville et département |
| `contract` | « CDI », « CDD »… |
| `salary` | fourchette affichée (souvent en k€ brut annuel) |
| `url` | lien de la carte, de la forme `https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/<id>` |
| `published_at` | date de publication affichée (`JJ/MM/AAAA` à convertir) |
| `description` | début du texte de la carte s'il est visible |
| `remote` | mention télétravail si elle apparaît, sinon vide |

## Blocage

Page « Access denied » ou vérification anti-robot : `blocked`.

## Dernière vérification

07/10/2026 : HTTP 403 en requête simple, confirmé. Parcours navigateur à valider au premier
passage local.
