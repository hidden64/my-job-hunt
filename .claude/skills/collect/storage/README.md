# Couche de stockage : comment un skill accède aux offres

Tu ne touches **jamais** directement `data/offers.csv` ni une base Airtable. Toutes les opérations
du contrat de `docs/STORAGE.md` passent par le moteur, qui choisit le backend d'après
`storage.backend` dans `config/kit.yml`.

| Besoin | Commande |
|---|---|
| créer le stockage (setup) | `scripts/jh init-storage` |
| enregistrer les offres d'une source | `scripts/jh source <nom> --run <id>` (http) ou `scripts/jh ingest <nom> --run <id> --file f.json` (navigateur) |
| offres à noter | `scripts/jh to-score [--run <id>] --limit 10` |
| enregistrer des scores | `scripts/jh apply-scores --file scores.json` |
| lister | `scripts/jh list [--status new,seen] [--min-score 70] [--source hellowork] [--since 2026-10-01] [--limit 20] [--order recent]` |
| retrouver une offre | `scripts/jh find "acme data"` |
| changer un statut | `scripts/jh set-status <id> applied` |
| renoter | `scripts/jh reset-scores` puis la boucle de scoring |
| exporter | `scripts/jh export` |

Chaque commande renvoie du JSON. En cas d'erreur : `"ok": false`, un code `error` et un `message`
en français à relayer au candidat.

## Fiches

| Fichier | Backend |
|---|---|
| `csv.md` | CSV dans le dépôt (défaut) |
| `airtable.md` | Airtable dans le compte du candidat (option) |
