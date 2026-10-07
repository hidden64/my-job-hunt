# Fiche source : Jobteaser

```yaml
name: jobteaser
label: Jobteaser
mode: browser
requires_login: false
available_in: [local]
optional_secrets: []
default_limit: 6
freshness_filter: false
auto_enable_rule: "profil étudiant ou diplômé depuis moins de 2 ans"
```

Suivre d'abord `_browser.md`. Jobteaser cible stages, alternances et premiers emplois.

## Quand l'utiliser

Le setup et le skill `onboarding` laissent `jobteaser` dans `sources.enabled` seulement si le
profil a un diplôme `in_progress` ou obtenu il y a moins de 2 ans. Sinon ils le retirent (le
candidat peut le remettre : « réactive Jobteaser »). Si la source est appelée pour un profil
expérimenté, la lancer quand même : c'est le choix du candidat.

## URL de recherche

```
https://www.jobteaser.com/fr/job-offers?q=<intitulé>&location=<ville>&page=<n>
```

- Si le paramètre `location` n'est pas pris en compte, utiliser le filtre de localisation de la
  page une fois par zone.
- `page` commence à 1.

## Ce qu'il faut lire sur chaque carte

| Champ | Où |
|---|---|
| `title` | intitulé |
| `company` | entreprise |
| `location` | ville |
| `contract` | « Stage », « Alternance », « CDI », « VIE »… |
| `url` | lien de la carte, de la forme `https://www.jobteaser.com/fr/job-offers/<id>-<slug>` |
| `published_at` | date relative convertie |
| `remote`, `salary`, `description` | si visibles, sinon vides |

Certaines offres sont réservées aux étudiants d'écoles partenaires et demandent une connexion pour
être lues en détail : les enregistrer quand même avec leur URL et `description` =
« accès réservé aux écoles partenaires ». Ne jamais se connecter.

## Blocage

Page de vérification, connexion obligatoire pour voir la liste, HTTP 403 : `blocked`.

## Dernière vérification

07/10/2026 : HTTP 403 en requête simple, confirmé. Parcours navigateur à valider au premier
passage local.
