# Import du CV

## Trouver le CV

1. Si le candidat donne un chemin, utilise-le.
2. Sinon, liste `config/cv/` (hors `README.md`). Un seul PDF : prends-le. Plusieurs : demande
   lequel. Aucun : rappelle où le déposer, ou continue sans CV.
3. Formats : PDF de préférence. Un `.docx` ou une image peuvent être lus aussi ; un `.doc` ancien
   non : demande un export PDF.

## Lire le CV

Lis le fichier avec l'outil de lecture de fichiers (il lit les PDF, y compris scannés, page par
page). Si le PDF est illisible (vide, protégé, image trop floue) : dis-le en une phrase et
continue le questionnaire sans pré-remplissage.

## Extraire

Relève uniquement ce qui est écrit. N'invente rien, ne complète pas, ne reformule pas les
intitulés de diplômes.

| Élément du CV | Champ de `candidate.yml` |
|---|---|
| Nom, prénom | `identity.first_name`, `identity.last_name` |
| Formations | `education.degrees[]` : `title`, `school`, `year`, `status` (`in_progress` si la date de fin est future ou « en cours »), `level` déduit |
| Cours, modules, projets académiques cités | `education.courses` |
| Certifications | `education.certifications` |
| Expériences | `education.experiences[]` : `title`, `company`, `months` (calculé depuis les dates), `year` |
| Compétences, outils, langages | `education.skills` |
| Langues et niveaux | `education.languages[]` |
| Titre ou accroche du CV (« Data Analyst junior ») | proposition pour `target.title` |
| Ville | proposition pour `criteria.location.city` |

## Présenter

Au début de chaque bloc du questionnaire, affiche les éléments trouvés pour ce bloc avec la
mention « (lu dans ton CV) » et demande : « C'est juste ? Quelque chose à corriger ou ajouter ? ».
Les champs non trouvés sont demandés normalement.

## Confidentialité

Le CV reste dans `config/cv/`, ignoré par Git. Tu ne le copies nulle part et tu ne cites jamais
son contenu dans un fichier versionné autre que `config/candidate.yml` (après accord).
