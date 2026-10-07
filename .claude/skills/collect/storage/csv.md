# Backend de stockage : CSV (défaut)

Fichier `data/offers.csv` dans la copie du candidat (`storage.csv.path` dans `config/kit.yml`).
Aucun compte, aucune clé. Ouvrable dans Excel, LibreOffice, Numbers ou Google Sheets.

## Implémentation

`scripts/jobhunter/storage.py`, classe `CsvBackend`. Tu n'écris **jamais** ce fichier toi-même :
toutes les opérations passent par `scripts/jh` (voir `README.md` de ce dossier).

| Garantie | Comment |
|---|---|
| Encodage | UTF-8 avec BOM, pour qu'Excel affiche les accents |
| En-tête | exactement les colonnes de `docs/STORAGE.md` ; un fichier avec un autre en-tête est refusé, jamais réécrit |
| Écriture atomique | écriture dans un fichier temporaire du même dossier, puis remplacement ; un passage interrompu laisse l'ancien fichier intact |
| Pas de doublon | `upsert` passe par la clé de dédoublonnage et l'index des URL |
| Volume | 500 offres écrites en moins d'une seconde (test automatique) |

## Commit automatique (option)

Si `storage.csv.auto_commit: true`, le skill `collect` termine le passage par :

```
git add data/offers.csv data/runs data/summaries && git commit -m "Job Hunter : passage <run>" && git push
```

Seulement si le dépôt a un remote et que le push est autorisé. Un échec du commit ou du push est
noté dans la réponse au candidat, jamais bloquant. Par défaut `false` : le candidat committe quand
il veut.

## Si le candidat ouvre le CSV dans Excel

Excel peut verrouiller le fichier. Si une écriture échoue pour cette raison, le passage note
l'erreur ; les offres de ce passage sont perdues pour le CSV mais réapparaîtront au passage
suivant (elles seront toujours en ligne). Conseil au candidat : utiliser l'export Excel
(« exporte mes offres en Excel ») pour travailler sur une copie.
