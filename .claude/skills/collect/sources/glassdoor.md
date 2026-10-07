# Fiche source : Glassdoor

```yaml
name: glassdoor
label: Glassdoor
mode: browser
requires_login: false
available_in: [local]
optional_secrets: []
default_limit: 4
freshness_filter: true
```

Suivre d'abord `_browser.md`. Glassdoor affiche une fenêtre d'inscription après quelques pages :
plafond bas et arrêt si elle ne peut pas être fermée.

## URL de recherche

```
https://www.glassdoor.fr/Emploi/emplois.htm?sc.keyword=<intitulé>&locKeyword=<ville>&fromAge=<jours>
```

- Si la ville n'est pas prise en compte, saisir la ville dans le champ « Lieu » de la page une fois
  par zone, puis réutiliser l'URL obtenue.
- `fromAge` : 1, 3, 7 ou 14 selon l'ancienneté du dernier passage réussi.
- Pagination : bouton « Afficher plus d'offres » en bas de liste (chaque clic compte pour une
  requête).

## Ce qu'il faut lire sur chaque carte

| Champ | Où |
|---|---|
| `title` | intitulé |
| `company` | entreprise (avec sa note, ne garder que le nom) |
| `location` | ville |
| `salary` | « 38 k€ – 45 k€ (Estimation de l'employeur) » : garder tel quel, y compris « estimation » |
| `url` | lien de la carte (`https://www.glassdoor.fr/job-listing/...`), sans paramètres de suivi |
| `published_at` | « 3 j » ou « 24 h » converti en date |
| `contract`, `remote`, `description` | si visibles, sinon vides |

## Blocage

- Fenêtre d'inscription : chercher la croix de fermeture. Si elle n'existe pas ou réapparaît
  aussitôt, `blocked` avec « fenêtre d'inscription bloquante ». Ne jamais créer de compte ni saisir
  d'e-mail.
- Vérification anti-robot ou HTTP 403 : `blocked`.

## Dernière vérification

07/10/2026 : HTTP 403 en requête simple, confirmé. Parcours navigateur à valider au premier
passage local.
