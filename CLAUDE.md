# Job Hunter — guide pour Claude

Tu travailles dans la copie personnelle d'un candidat du kit **Job Hunter**. Ce fichier te dit ce
qu'est le kit, où sont les choses et quelles règles respecter. Lis-le avant toute action.

## Ce que fait le kit

1. **Installation** (skill `setup`) : choix du mode, du stockage et des horaires, création du
   stockage, planification des collectes.
2. **Profil** (skills `onboarding`, `profile`) : parcours (diplômes obtenus et en cours, cours
   suivis), identité, poste visé précis, critères marqués obligatoires ou flexibles, avec import
   optionnel du CV. Résultat : `config/candidate.yml`.
3. **Mots-clés** (skill `keywords`) : intitulés, compétences, négatifs et zones générés depuis le
   profil, validés par le candidat avant tout usage.
4. **Collecte** (skill `collect`) plusieurs fois par jour : sources HTTP par le moteur, sources
   navigateur par Claude, dédoublonnage, notation de chaque nouvelle offre, journal, résumé du
   jour, alerte au-dessus du seuil.
5. **Suivi** (skills `summary`, `offers`, `export`, `rescore`, `config`, `connect`).

## Le moteur

`scripts/jh <commande>` lance le moteur Python (`scripts/jobhunter/`, bibliothèque standard,
Python 3.8+). Il fait tout ce qui doit être exact et reproductible : stockage, dédoublonnage,
calcul des scores, journaux, résumés, export Excel, notifications, sources HTTP. Chaque commande
renvoie du JSON avec `ok`, et en cas d'échec `error` et `message` (en français, à relayer).
`scripts/jh --help` liste les commandes. Claude fait ce qui demande du jugement : questionnaire,
mots-clés, notes par composante des offres, sources navigateur.

## Où sont les choses

| Chemin | Rôle | Versionné |
|---|---|---|
| `.claude/skills/<nom>/SKILL.md` | un skill par capacité | oui |
| `.claude/skills/collect/sources/` | une fiche par source | oui |
| `.claude/skills/collect/storage/` | fiches des backends de stockage | oui |
| `.claude/settings.json` | autorisations (moteur, écriture dans `data/`) et hook d'ouverture | oui |
| `scripts/jh`, `scripts/jobhunter/` | moteur | oui |
| `scripts/schedule.sh`, `scripts/schedule.ps1` | planification locale (cron, Planificateur de tâches) | oui |
| `config/kit.yml` | réglages du candidat (référence : `kit.example.yml`) | oui |
| `config/candidate.yml` | profil et mots-clés (référence : `candidate.example.yml`) | oui |
| `config/candidate.history.log` | historique des modifications du profil | oui |
| `config/cv/` | CV du candidat | non |
| `config/secrets.env` | clés facultatives (illisible pour Claude) | non |
| `data/offers.csv` | offres (stockage CSV) | oui |
| `data/runs/<AAAA-MM-JJ-HHMM>.md` | journal de chaque passage | oui |
| `data/runs/state.json` | état des sources et des intitulés | oui |
| `data/runs/work/`, `data/runs/evidence/` | fichiers de travail, preuves de blocage | non |
| `data/summaries/<AAAA-MM-JJ>.md` | résumé du jour | oui |
| `data/exports/` | exports Excel | non |
| `data/pending/` | file d'attente Airtable | non |
| `docs/` | documentation du kit | oui |
| `tests/` | tests du moteur et jeux de données fictifs | oui |

## Règles

- **Lire `config/kit.yml` avant d'agir.** Aucune valeur de configuration en dur dans un skill.
- **Ne jamais écrire dans `config/candidate.yml` sans l'accord explicite du candidat** sur un
  récapitulatif ou un avant → après.
- **Ne jamais lancer de collecte sans mots-clés validés** : `scripts/jh run start` le refuse, le
  relayer et renvoyer vers `keywords`.
- **Les offres ne passent que par le moteur.** Jamais d'écriture directe dans `data/offers.csv` ni
  dans Airtable (`docs/STORAGE.md`).
- **Les sources suivent leur fiche et `docs/SOURCES.md`.** Une source qui échoue est notée et
  ignorée pour ce passage. Jamais de captcha résolu, de proxy, de plafond dépassé.
- **Zéro clé obligatoire.** Aucune clé n'est demandée à l'installation ; les options avec clé
  passent par le skill `connect`, et c'est le candidat qui remplit `config/secrets.env`.
- **Jamais de connexion à un compte du candidat** (LinkedIn ou autre). Jamais de candidature
  envoyée à sa place.
- **Garde-fou du dépôt modèle** : si `origin` pointe vers `klakenyuo/the-job-hunter`, le candidat
  est dans le modèle et non dans sa copie ; le setup refuse et explique « Use this template ».
- **Pendant une routine** (prompt « Lance une collecte Job Hunter. »), ne poser aucune question.

## Conventions et langue

Nommage : `docs/CONVENTIONS.md`. Tout ce que le candidat lit est en français, avec tutoiement. Les
identifiants (clés YAML, noms de fichiers, valeurs de champs) sont en anglais.

## Développement du kit

Tests : `python3 -m unittest discover -s tests`. Vérification des sites en direct :
`python3 tests/live_smoke.py`. Scénarios de bout en bout : `docs/TESTS.md`.
