# data/

Tout ce que le kit produit pour vous.

- `offers.csv` : les offres collectées, une ligne par offre, dédoublonnées. C'est le stockage par
  défaut. Si vous avez choisi Airtable, ce fichier n'est pas utilisé. Schéma : `docs/STORAGE.md`.
- `runs/` : un journal technique par passage de collecte (`AAAA-MM-JJ-HHMM.md`). Utile pour
  comprendre ce qui a été cherché, trouvé, bloqué. Archivé après 30 jours dans `runs/archive/`.
- `summaries/` : un résumé lisible par jour (`AAAA-MM-JJ.md`) : nouvelles offres, meilleures
  offres du jour, avertissements. Affiché à l'ouverture de Claude Code.
- `runs/state.json` : état de chaque source (dernier succès, échecs consécutifs), tenu par le
  moteur.
- `runs/work/` et `runs/evidence/` : fichiers de travail des passages et preuves de blocage. Non
  versionnés.
- `exports/` : classeurs Excel produits à la demande par le skill `export`. Non versionné.
- `pending/` : offres en attente d'écriture dans Airtable après une erreur réseau, rejouées au
  passage suivant. Non versionné.
