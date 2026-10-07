# Fiches des sources

Une fiche par source. Le contrat commun, les plafonds et la gestion des échecs sont dans
`docs/SOURCES.md` ; le déroulé complet d'un passage est dans `../SKILL.md`.

| Fichier | Source | Mode | Qui l'exécute |
|---|---|---|---|
| `france_travail.md` | France Travail | http | le moteur : `scripts/jh source france_travail --run <id>` |
| `hellowork.md` | HelloWork | http | le moteur : `scripts/jh source hellowork --run <id>` |
| `linkedin.md` | LinkedIn, recherche publique | http | le moteur : `scripts/jh source linkedin --run <id>` |
| `wttj.md` | Welcome to the Jungle | browser | Claude, avec Claude in Chrome |
| `apec.md` | APEC | browser | Claude, avec Claude in Chrome |
| `jobteaser.md` | Jobteaser | browser | Claude, avec Claude in Chrome |
| `indeed.md` | Indeed | browser | Claude, avec Claude in Chrome |
| `glassdoor.md` | Glassdoor | browser | Claude, avec Claude in Chrome |
| `test.md` | Source de test | http | le moteur, sans réseau |
| `_browser.md` | procédure commune des sources navigateur | | à lire avant toute fiche browser |
| `_template.md` | modèle pour ajouter une source | | |

## Interdits, pour toutes les sources

- Se connecter à un compte du candidat, remplir un formulaire de connexion, accepter des
  conditions en son nom.
- Résoudre ou contourner un captcha, utiliser un proxy, changer d'identité de navigateur.
- Postuler, enregistrer, aimer, suivre, ou faire autre chose que lire des résultats.
- Dépasser le plafond de pages, même d'une page.
