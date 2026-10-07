---
name: connect
description: Brancher une option facultative de Job Hunter qui demande une clé - l'API officielle France Travail (plus de détails sur les offres) ou le stockage Airtable (base créée dans le compte du candidat). À utiliser quand le candidat dit "branche l'API France Travail", "utilise Airtable", "stocke dans Airtable", "débranche Airtable", "reviens au CSV". Aucune de ces options n'est nécessaire au fonctionnement du kit.
---

# Skill `connect` — options avec clé

Rappel à donner au candidat dès le début : **ces options sont facultatives**. Sans elles, le kit
fonctionne entièrement (règle zéro clé, `docs/SOURCES.md`).

## Règle pour les clés

Les clés vont dans `config/secrets.env`, jamais ailleurs, jamais dans un fichier versionné. Ce
fichier est protégé : tu ne peux ni le lire ni l'écrire. C'est volontaire. Le candidat le remplit
lui-même :

1. Si `config/secrets.env` n'existe pas, crée-le par copie : `cp config/secrets.example.env config/secrets.env`.
2. Demande au candidat d'ouvrir `config/secrets.env` dans un éditeur de texte (sur Mac :
   `open -e config/secrets.env` ; Windows : `notepad config\secrets.env` ; Linux :
   `xdg-open config/secrets.env`), de coller la valeur après le `=` de la bonne ligne, sans espace
   ni guillemets, et d'enregistrer.
3. Vérifie sans voir la valeur : `scripts/jh secrets` → la variable doit apparaître dans `present`.

Ne demande jamais au candidat de coller une clé dans la conversation. S'il le fait quand même,
ne la recopie nulle part, conseille-lui de la régénérer plus tard, et continue.

## API France Travail

Apport : salaire, description complète et télétravail sur chaque offre France Travail, 50 offres
par requête. Le moteur bascule tout seul dès que les deux identifiants sont présents.

1. Explique la démarche (10 minutes, gratuit) :
   - créer un compte sur https://francetravail.io (rubrique « Se connecter » puis « Créer un compte ») ;
   - « Mes applications » → « Créer une application » (nom : Job Hunter) ;
   - ajouter l'API « Offres d'emploi v2 » à l'application ;
   - copier l'« Identifiant client » et la « Clé secrète ».
2. Le candidat les colle dans `FRANCE_TRAVAIL_CLIENT_ID` et `FRANCE_TRAVAIL_CLIENT_SECRET`
   (procédure ci-dessus).
3. Vérifie : `scripts/jh secrets`, puis un essai réel au prochain passage. Le journal de passage
   indique « via l'API officielle » sur la ligne France Travail. En cas d'erreur
   « authentification refusée », les identifiants sont faux ou l'API n'est pas ajoutée à
   l'application.
4. En mode cloud, ajouter `entreprise.francetravail.fr` et `api.francetravail.io` aux domaines
   autorisés de l'environnement.

Débrancher : le candidat vide les deux lignes dans `config/secrets.env`. Le site public reprend
le relais.

## Airtable

Apport : vues filtrées, interface mobile Airtable, partage facile. Le CSV reste plus simple.

1. Prérequis : un compte Airtable (gratuit suffit pour commencer).
2. Jeton : sur https://airtable.com/create/tokens, « Create token », nom « Job Hunter », droits
   `data.records:read`, `data.records:write`, `schema.bases:read`, `schema.bases:write`, accès
   « All current and future bases in » l'espace de travail choisi. Le candidat colle le jeton dans
   `AIRTABLE_API_KEY`.
3. Identifiant de l'espace de travail : dans Airtable, ouvrir l'espace de travail ; l'adresse
   contient `wsp...`. Le candidat te le donne (ce n'est pas un secret).
4. Crée la base : `scripts/jh airtable-create-base --workspace wsp...` → `base_id`.
5. Écris dans `config/kit.yml` : `storage.backend: airtable` et `storage.airtable.base_id: <base_id>`
   (montre l'avant → après, comme le skill `config`).
6. `scripts/jh init-storage` doit répondre `exists`.
7. Les offres déjà dans le CSV ne sont pas transférées : la migration n'est pas automatisée dans
   cette version. Dis-le clairement ; `data/offers.csv` reste lisible et l'export Excel aussi
   (en repassant temporairement au CSV).
8. Guide la création des 3 vues dans l'interface Airtable (`.claude/skills/collect/storage/airtable.md`,
   section « Vues »).
9. En mode cloud, ajouter `api.airtable.com` aux domaines autorisés.

Revenir au CSV (« reviens au CSV ») : `storage.backend: csv` dans `config/kit.yml`. Le CSV reprend
où il en était ; les offres arrivées entre-temps dans Airtable y restent.
