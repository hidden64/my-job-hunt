# Fiche source : Indeed

```yaml
name: indeed
label: Indeed
mode: browser
requires_login: false
available_in: [local]
optional_secrets: []
default_limit: 4
freshness_filter: true
```

Suivre d'abord `_browser.md`. Indeed est protégé par Cloudflare : plafond le plus bas, délai
minimum de 5 secondes entre deux pages, arrêt au premier signe de vérification.

## URL de recherche

```
https://fr.indeed.com/jobs?q=<intitulé>&l=<ville>&radius=<km>&fromage=<jours>&start=<10 × page>
```

- `radius` : `criteria.location.radius_km` du profil, arrondi à 10, 25 ou 50 (25 par défaut).
- `fromage` : 1, 3, 7 ou 14 selon l'ancienneté du dernier passage réussi de la source (`since`
  dans le plan du passage) ; 14 au premier passage.
- 15 offres environ par page.

## Ce qu'il faut lire sur chaque carte

| Champ | Où |
|---|---|
| `title` | titre de la carte |
| `company` | nom de l'entreprise |
| `location` | lieu (peut contenir « Télétravail hybride à Lyon (69) ») |
| `remote` | même texte que le lieu s'il mentionne le télétravail |
| `salary` | fourchette si affichée |
| `contract` | étiquette « CDI », « CDD »… si affichée |
| `url` | `https://fr.indeed.com/viewjob?jk=<identifiant>` (l'identifiant `jk` est dans le lien de la carte) |
| `published_at` | « Publié il y a 3 jours », « Employeur actif il y a… » : convertir seulement « Publié » |
| `description` | extrait sous la carte |

## Blocage

Page « Vérification que vous êtes humain », « Additional verification required », challenge
Cloudflare : `blocked` immédiatement. C'est fréquent. Après 3 passages bloqués de suite, le résumé
propose au candidat de désactiver Indeed.

## Dernière vérification

07/10/2026 : HTTP 403 en requête simple, confirmé. Parcours navigateur à valider au premier
passage local.
