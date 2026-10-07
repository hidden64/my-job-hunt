---
name: keywords
description: Générer puis faire valider par le candidat les mots-clés de recherche Job Hunter (intitulés de poste, compétences, mots-clés négatifs, zones) à partir de son profil. À utiliser après l'onboarding, ou quand le candidat dit "revois mes mots-clés", "ajoute un intitulé", "enlève ce mot-clé", "montre mes mots-clés", "régénère les mots-clés". Les routines de collecte refusent de tourner tant que les mots-clés ne sont pas validés.
---

# Skill `keywords` — générer et valider les mots-clés

Les mots-clés pilotent toutes les recherches. Les sources cherchent **chaque intitulé dans chaque
zone**, dans l'ordre de la liste, jusqu'à leur plafond de requêtes : l'ordre compte, les premiers
sont toujours couverts. Le candidat garde la main : rien n'est utilisé avant sa validation.

## 1. Lire

`config/candidate.yml` (s'il n'existe pas : renvoyer vers `onboarding`) et `config/kit.yml`
(pour les plafonds `sources.limits`).

## 2. Générer un brouillon

Suis `generation.md` (dans ce dossier). Le brouillon contient :

| Catégorie | Quantité | Rôle |
|---|---|---|
| `titles` | 5 à 15, du plus probable au moins probable | intitulés cherchés tels quels sur les sites |
| `skills` | 5 à 12 | utilisés par le scoring, pas par les recherches |
| `negative` | 3 à 10 | une offre dont le titre contient l'un d'eux est écartée avant stockage |
| `locations` | 1 à 4 zones | `label`, `city`, `department` |

Chaque élément non évident a une justification d'une ligne.

Écris le brouillon dans `config/keywords.draft.yml` (même structure que le bloc `keywords` de
`config/candidate.example.yml`, sans `validated_at`). Ce fichier n'est jamais lu par la collecte.

## 3. Présenter

Liste numérotée en continu, par catégorie, avec la justification en fin de ligne :

```
INTITULÉS CHERCHÉS (dans cet ordre)
 1. Data Analyst — ton intitulé
 2. Analyste de données — équivalent français
 3. Junior Data Analyst — ton niveau
 4. Business Analyst data — variante fréquente
 5. Chargé d'études statistiques — intitulé courant dans le public pour ton Master
COMPÉTENCES (pour noter les offres)
 6. SQL  7. Python  8. Power BI  9. statistiques
EXCLUS (offres écartées si le titre contient)
10. senior — tu vises junior
11. lead  12. manager
13. stage — tu cherches CDI ou alternance
ZONES
14. Lyon (69)  15. Villeurbanne (69)
```

Puis une phrase sur le volume : « Avec 5 intitulés × 2 zones, France Travail fera 10 recherches
par passage sur ses 20 autorisées ; LinkedIn n'en fera que 5, il couvrira les intitulés 1 à 3. »
(calcule avec les plafonds de `kit.yml` : France Travail, HelloWork, LinkedIn.)

Termine par : « Tu valides ? Tu peux dire "ok", "enlève le 4", "ajoute Data Engineer junior après
le 2", "remonte le 5 en premier", ou reformuler. »

## 4. Boucle d'édition

Applique chaque demande sur le brouillon, réaffiche la liste complète renumérotée, et redemande la
validation. Refuse poliment :

- un intitulé vide ou de plus de 60 caractères ;
- plus de 15 intitulés ou plus de 4 zones (au-delà, les plafonds ne suivent plus : explique-le) ;
- un mot négatif qui figure dans un intitulé conservé (il exclurait tout) : signale le conflit.

## 5. Valider

Sur accord explicite :

1. Écris le bloc `keywords` dans `config/candidate.yml` (remplace l'ancien s'il existe), avec
   `validated_at` à l'instant présent (ISO 8601 avec fuseau), et un bloc `rationale` contenant les
   justifications utiles. Ne touche à rien d'autre dans le fichier.
2. Supprime `config/keywords.draft.yml`.
3. Ajoute à `config/candidate.history.log` : `<instant> keywords : validés (N intitulés, M zones)`.
4. Vérifie avec `scripts/jh check` que `keywords_validated` vaut `true`.
5. Dis : « Mots-clés validés. Les recherches peuvent tourner. » Puis, si le kit vient d'être
   installé (aucun passage dans `data/runs/`), propose : « On lance une première collecte
   maintenant pour voir ce que ça donne ? » et, sur accord, lance le skill `collect`.

## Afficher ou modifier plus tard

- « Montre mes mots-clés » : affiche la liste numérotée et la date de validation, sans rien
  changer.
- « Ajoute / enlève … » sur des mots-clés déjà validés : applique au bloc existant après avoir
  montré l'avant → après, mets à jour `validated_at`, journalise. Pas besoin de régénérer.
- « Régénère » : refais l'étape 2 à partir du profil actuel.
