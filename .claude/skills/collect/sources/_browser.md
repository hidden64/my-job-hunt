# Procédure commune des sources navigateur

À suivre pour `wttj`, `apec`, `jobteaser`, `indeed`, `glassdoor`, en complément de la fiche de la
source. Ces sources ne tournent qu'en mode local, avec l'extension Claude in Chrome connectée
(`/chrome` dans Claude Code).

## Avant de commencer

1. Vérifie que les outils du navigateur Claude in Chrome sont disponibles dans cette session.
   S'ils ne le sont pas : `scripts/jh source-result <nom> --run <id> --status unavailable
   --message "navigateur Claude in Chrome non connecté"`, puis passe à la source suivante.
2. Lis le plafond de la source dans le plan du passage (`limit`), et les délais
   `sources.browser_delay_seconds` de `config/kit.yml`.
3. Prépare la liste des couples intitulé × zone : `keywords.titles` × `keywords.locations` de
   `config/candidate.yml`, dans cet ordre. Parcours en largeur : première page de chaque couple,
   puis pages suivantes si le plafond le permet.

## Pour chaque page

1. Construis l'URL selon la fiche et ouvre-la dans un onglet du navigateur. Un chargement de page
   compte pour une requête, y compris un passage à la page suivante.
2. Attends que la liste des offres soit affichée (quelques secondes au plus).
3. **Signes de blocage** : captcha, « vérifiez que vous êtes humain », page Cloudflare, demande de
   connexion qui masque les résultats, page d'erreur 403. Au premier signe : enregistre le texte
   visible de la page dans `data/runs/evidence/<run>-<nom>.txt`, arrête cette source, note
   `blocked` (voir « Terminer »). Ne clique sur rien pour « débloquer ».
4. Une bannière de cookies peut être refusée (« Continuer sans accepter », « Tout refuser ») si
   elle masque les résultats. Jamais d'autre clic que la pagination et cette bannière.
5. Lis les offres affichées et, pour chacune, relève les champs demandés par la fiche. Écarte les
   offres dont le titre contient un mot de `keywords.negative`.
6. Respecte un délai aléatoire entre deux pages (entre `min` et `max` secondes).

Ne pas ouvrir les pages de détail des offres, sauf si la fiche le demande et que le plafond le
permet.

## Format des offres

Écris toutes les offres de la source dans `data/runs/work/<run>/<nom>.json`, un tableau JSON :

```json
[
  {
    "title": "Data Analyst H/F",
    "company": "Entreprise",
    "location": "Lyon (69)",
    "contract": "CDI",
    "remote": "Télétravail occasionnel",
    "salary": "40K à 45K €",
    "url": "https://www.example.com/offre/123",
    "published_at": "2026-10-06",
    "description": "Une ou deux phrases visibles sur la carte, si présentes."
  }
]
```

- Recopie les textes tels qu'affichés : le moteur normalise contrat, télétravail et URL.
- `url` : lien direct vers l'offre, absolu. Une offre sans URL sera rejetée.
- `published_at` : date `AAAA-MM-JJ` si tu peux la déduire (« il y a 2 jours »), sinon vide.
- Champs inconnus : chaîne vide. N'invente jamais un salaire ou un contrat.

## Terminer

- Résultat normal :
  `scripts/jh ingest <nom> --run <id> --file data/runs/work/<id>/<nom>.json --requests <pages chargées> --queries '[{"title":"Data Analyst","location":"Lyon","count":12}]'`
- Blocage après quelques pages : même commande avec `--status blocked --message "<cause>"` pour
  garder les offres déjà lues.
- Blocage dès la première page ou erreur sans offre :
  `scripts/jh source-result <nom> --run <id> --status blocked --requests <n> --message "<cause>"`

Ferme l'onglet à la fin de chaque source.
