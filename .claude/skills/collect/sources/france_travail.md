# Fiche source : France Travail

```yaml
name: france_travail
label: France Travail
mode: http
requires_login: false
available_in: [local, cloud]
optional_secrets: [FRANCE_TRAVAIL_CLIENT_ID, FRANCE_TRAVAIL_CLIENT_SECRET]
default_limit: 20
freshness_filter: true
```

## Exécution

```
scripts/jh source france_travail --run <id>
```

Le moteur fait tout : requêtes, lecture, normalisation, dédoublonnage, stockage, journal.

## Comment le moteur cherche

**Sans clé (par défaut)** : site public `candidat.francetravail.fr`, rendu côté serveur.

```
https://candidat.francetravail.fr/offres/recherche?motsCles=<intitulé>&lieux=<département>D&emission=<jours>&range=<début>-<fin>
```

- `lieux` : code département de la zone suivi de `D` (`69D`). Sans département, recherche France
  entière.
- `emission` : publiées depuis 1, 3, 7, 14 ou 31 jours, déduit du dernier passage réussi (14 au
  premier passage). Ce paramètre évite aussi la redirection vers l'URL « lisible » du site, qui
  perd la pagination.
- `range` : 20 offres par page (`0-19`, `20-39`…), 3 pages au plus par couple intitulé × zone.
- Champs lus sur la liste : titre, entreprise, ville, contrat, extrait de description, date
  relative. Le salaire et le télétravail ne sont pas sur la liste (télétravail déduit de
  l'extrait quand il en parle).

**Avec clé (option)** : API officielle « Offres d'emploi v2 » si `FRANCE_TRAVAIL_CLIENT_ID` et
`FRANCE_TRAVAIL_CLIENT_SECRET` sont dans `config/secrets.env`. Le moteur bascule tout seul. Apport :
salaire, description complète, 50 offres par requête. Le candidat l'active avec « branche l'API
France Travail » (skill `connect`). Ce chemin n'a pas pu être testé en direct faute de clé.

## Blocage et erreurs

- Page sans liste et sans « Aucune offre » : `error`, « format de page inattendu ». Le site a
  probablement changé : lancer `python3 tests/live_smoke.py` pour confirmer.
- HTTP 403/429 : `blocked`.

## Domaines à autoriser en mode cloud

`candidat.francetravail.fr` (et, avec l'API : `entreprise.francetravail.fr`, `api.francetravail.io`).

## Dernière vérification

07/10/2026 : 14 offres « Data Analyst » dans le Rhône en une requête, pagination vérifiée sur
« comptable » à Paris (2 411 offres).
