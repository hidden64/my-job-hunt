# Fiche source : HelloWork

```yaml
name: hellowork
label: HelloWork
mode: http
requires_login: false
available_in: [local, cloud]
optional_secrets: []
default_limit: 8
freshness_filter: true
```

## Exécution

```
scripts/jh source hellowork --run <id>
```

## Comment le moteur cherche

```
https://www.hellowork.com/fr-fr/emploi/recherche.html?k=<intitulé>&l=<ville>&d=<d|w>&p=<page>
```

- `l` : ville de la zone (`keywords.locations[].city`).
- `d` : `d` (24 h) si le dernier passage date de moins de 12 h, `w` (7 jours) s'il date de moins
  d'une semaine, absent sinon.
- `p` : page, à partir de 2. Environ 20 à 30 offres par page.
- Les cartes contiennent titre, entreprise, ville, contrat, salaire (souvent), télétravail
  (« Télétravail partiel »…) et date relative : aucune page de détail n'est ouverte.

## Blocage et erreurs

- Page sans cartes `serpCard` ni filtres : `error`, « format de page inattendu ».
- HTTP 403/429 ou page anti-robot : `blocked`.

## Domaine à autoriser en mode cloud

`www.hellowork.com`

## Dernière vérification

07/10/2026 : 24 offres « Data Analyst » à Lyon, 30 par page sur « comptable » à Paris, filtre
`d=w` vérifié.
