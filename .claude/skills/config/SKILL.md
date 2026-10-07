---
name: config
description: Modifier un réglage de Job Hunter dans config/kit.yml en langage naturel, avec validation. À utiliser quand le candidat dit par exemple "passe à 2 passages par jour", "change les horaires", "désactive Indeed", "mets le seuil d'alerte à 80", "passe en mode cloud", "montre-moi ma config". Ne gère pas le profil du candidat (voir le skill profile) ni les mots-clés (voir keywords).
---

# Skill `config` — modifier les réglages du kit

Tu modifies `config/kit.yml` à la demande du candidat. Une seule règle compte : **tu n'écris jamais
une valeur invalide.** Les règles de validation sont dans `reference.md`, dans ce dossier. Lis-le
avant toute modification.

## Déroulé

1. **Lire** `config/kit.yml`. S'il n'existe pas, dire au candidat que le kit n'est pas installé et
   renvoyer vers le skill `setup`. Ne pas le créer toi-même.

2. **Comprendre la demande.** Traduire la phrase du candidat en une ou plusieurs modifications
   `clé → nouvelle valeur`. Le tableau « Formulations courantes » de `reference.md` couvre les cas
   fréquents. Si la demande est ambiguë (ex. « change les horaires » sans préciser lesquels),
   poser une question courte au lieu de deviner.

3. **Valider** chaque nouvelle valeur avec les règles de `reference.md` : type, valeurs permises,
   bornes, cohérence entre clés (ex. `notifications.channel: push` n'a de sens qu'en mode cloud).
   Si une valeur est invalide : expliquer en une phrase pourquoi, proposer la valeur valide la plus
   proche, et **ne rien écrire**. S'arrêter là tant que le candidat n'a pas reformulé.

4. **Montrer avant / après** pour chaque clé modifiée, sur une ligne :
   `schedule.times : ["08:00", "13:00", "19:00"] → ["08:00", "19:00"]`
   Si la modification a une conséquence, la dire en une phrase (voir « Conséquences » ci-dessous).

5. **Écrire** dans `config/kit.yml` en ne touchant que les clés concernées. Conserver les
   commentaires et l'ordre des sections. Ne pas réécrire le fichier entier depuis l'exemple.

6. **Confirmer** en une phrase ce qui a changé. Si des routines doivent être replanifiées, le dire
   explicitement (voir ci-dessous).

## Afficher la configuration

Si le candidat demande « montre-moi ma config » ou « quels sont mes réglages », afficher un
tableau lisible, en français, des valeurs actuelles : mode, horaires et fuseau, stockage, sources
actives (avec la mention « ignorée en mode cloud » pour les sources navigateur si le mode est
cloud), seuil d'alerte, canal de notification. Ne pas afficher le YAML brut sauf demande.

## Conséquences à signaler

| Modification | À dire au candidat |
|---|---|
| `schedule.times` ou `schedule.timezone` | Replanifier. Si les collectes sont planifiées par le kit (`bash scripts/schedule.sh list` renvoie des entrées, ou `scripts\schedule.ps1 list` sous Windows) : relance `install` avec les nouvelles heures, sur accord. Sinon (routines de l'application ou cloud) : guide la modification des routines comme dans `.claude/skills/setup/reference.md`, section « Planification ». |
| `execution.mode` → `cloud` | Lister les sources navigateur qui seront ignorées (5) et celles qui restent (France Travail, HelloWork, LinkedIn). Si `notifications.channel` est `system`, proposer `push`. Supprimer la planification locale (`schedule.sh remove`) et créer les routines cloud, avec l'accès réseau (setup, « Planification » → « Cloud »). |
| `execution.mode` → `local` | Rappeler que la machine doit être allumée aux heures prévues. Si `notifications.channel` est `push`, proposer `system`. Désactiver les routines cloud et planifier en local (setup, « Planification »). |
| `storage.backend` → `airtable` | Si `storage.airtable.base_id` est vide, dire que la base doit être créée et renvoyer vers le skill `setup` (étape stockage). Les offres déjà dans le CSV ne sont pas migrées automatiquement. |
| `storage.backend` → `csv` | Les offres déjà dans Airtable restent dans Airtable. |
| `sources.enabled` retrait d'une source | Les offres déjà collectées depuis cette source restent stockées. |
| `sources.limits` augmentation | Rappeler le risque de captcha et de blocage sur les sources navigateur. |
| `scoring.alert_threshold` | Dire combien d'offres déjà stockées dépassent le nouveau seuil, si le stockage est lisible. |
| `scoring.weights` ou `scoring.hard_filter_cap` | Proposer de relancer le scoring sur les offres existantes via le skill `rescore`. |

## Ce que ce skill ne fait pas

- Il ne modifie pas `config/candidate.yml` (profil, critères, mots-clés). Renvoyer vers `profile`
  ou `keywords`.
- Il ne crée pas de base Airtable et ne demande jamais de clé. Renvoyer vers `connect`.
- Il n'écrit jamais dans `config/secrets.env`.
