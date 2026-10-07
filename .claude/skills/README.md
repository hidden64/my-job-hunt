# Skills du kit

Un dossier par skill avec son `SKILL.md`, et ses ressources à côté. Toutes les formulations qui
déclenchent les skills sont dans `docs/COMMANDES.md`.

| Skill | Rôle | Cartes |
|---|---|---|
| `setup` | installation en un prompt : garde-fous, choix, configuration, stockage, planification | E0.2, E6.1, E6.2 |
| `config` | modifier un réglage de `config/kit.yml` en langage naturel, avec validation | E0.3 |
| `onboarding` | questionnaire complet et import du CV | E1.1, E1.2 |
| `profile` | mettre à jour le profil | E1.3 |
| `keywords` | générer puis faire valider les mots-clés | E2.1, E2.2 |
| `collect` | un passage de collecte : sources, dédoublonnage, notation, journal, résumé, alerte | E4, E5.1, E6.1, E6.4 |
| `rescore` | renoter les offres après un changement de profil ou de poids | E5.1 |
| `summary` | résumé du jour et journaux | E6.3 |
| `offers` | consulter les offres et suivre les candidatures | E3.1 |
| `export` | export Excel | E3.5 |
| `connect` | options avec clé : API France Travail, Airtable | E3.3, E4.1 |

Le travail déterministe (stockage, dédoublonnage, calcul des scores, journaux, résumé, export,
sources HTTP) est fait par le moteur `scripts/jh`, que les skills appellent.
