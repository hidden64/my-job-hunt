# Fiche source : LinkedIn (recherche publique)

```yaml
name: linkedin
label: LinkedIn (recherche publique)
mode: http
requires_login: false
available_in: [local, cloud]
optional_secrets: []
default_limit: 5
freshness_filter: true
```

**Règle absolue : le kit ne se connecte jamais au compte LinkedIn du candidat**, ni par le moteur,
ni par le navigateur. Seules les pages publiques destinées aux visiteurs non connectés sont lues.

## Exécution

```
scripts/jh source linkedin --run <id>
```

## Comment le moteur cherche

Pages publiques « jobs-guest » (celles que LinkedIn sert aux visiteurs non connectés) :

```
https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=<intitulé>&location=<ville>, France&f_TPR=r<secondes>&start=<25 × page>
```

- `f_TPR` : 24 h, 7 jours ou 30 jours selon l'ancienneté du dernier passage.
- 25 offres par page, 2 pages au plus par couple intitulé × zone.
- Champs lus : titre, entreprise, ville, date de publication, lien de l'offre (sans paramètres de
  suivi). Le contrat et la description ne sont pas sur la liste : le scoring les considère comme
  inconnus.
- Plafond bas (5 requêtes) : LinkedIn limite vite les visiteurs anonymes.

## Blocage et erreurs

- Redirection vers une page de connexion (`authwall`, `login`), HTTP 429 ou 999 : `blocked`.
  C'est attendu de temps en temps ; le passage suivant réessaie.

## Domaine à autoriser en mode cloud

`www.linkedin.com`

## Dernière vérification

07/10/2026 : 13 offres « Data Analyst » autour de Lyon en 2 requêtes, pagination vérifiée.
