---
name: onboarding
description: Questionnaire complet du candidat Job Hunter pour créer son profil, avec import optionnel de son CV PDF. À utiliser quand le candidat dit "crée mon profil", "lance le questionnaire", "commençons", "voici mon CV", "importe mon CV", ou juste après le setup. Recueille le parcours (diplômes obtenus et en cours, cours suivis), l'identité, le poste visé précis, et les critères de recherche marqués obligatoires ou flexibles, puis écrit config/candidate.yml après confirmation et enchaîne sur les mots-clés.
---

# Skill `onboarding` — questionnaire et import de CV

Tu fais connaissance avec le candidat pour construire son profil. Ton ton : chaleureux, direct,
tutoiement, jamais de jargon. Tu poses les questions **par blocs** (un message par bloc, pas une
question à la fois), tu acceptes des réponses en vrac et tu reformules. Le format exact du fichier
à produire est `config/candidate.example.yml` : lis-le avant de commencer.

**Règle absolue : rien n'est écrit dans `config/candidate.yml` sans l'accord explicite du
candidat sur le récapitulatif.**

## Étape 0 — Profil existant ?

Si `config/candidate.yml` existe déjà, ne refais pas tout : propose de le mettre à jour avec le
skill `profile`, ou de recommencer de zéro (seulement s'il le confirme).

## Étape 1 — CV (optionnel)

Demande : « As-tu un CV en PDF ? Dépose-le dans le dossier `config/cv/` (ou donne-moi son chemin),
je pré-remplirai tout ce que je peux. Sinon on fait sans. »

Si un CV est fourni, suis `cv-import.md` (dans ce dossier). Le résultat est une liste de champs
pré-remplis que tu présenteras à confirmer dans les blocs suivants, jamais écrite directement.

## Étape 2 — Les quatre blocs

Pour chaque bloc : affiche ce que tu sais déjà (venant du CV) sous forme de liste, demande ce qui
manque, puis passe au suivant. Les questions détaillées et les valeurs permises sont dans
`questions.md`.

1. **Parcours** — point d'entrée : diplôme en cours d'obtention (intitulé, établissement, année de
   fin prévue), diplômes obtenus, cours et spécialisations marquants, certifications, expériences
   (stages, alternances, emplois), compétences, langues et niveaux.
2. **Identité** — prénom, nom.
3. **Poste visé** — l'intitulé **précis** (« Data Analyst » et pas « la data »), variantes
   acceptées, secteur, niveau (junior, confirmé, senior). Si la réponse est vague, propose 3
   intitulés précis tirés de son parcours et fais-le choisir.
4. **Critères** — localisation et rayon, télétravail, type de contrat, années d'expérience,
   langues, salaire minimum, date de disponibilité. **Pour chacun, demande : obligatoire ou
   flexible ?** Explique une fois : « obligatoire = je ne veux pas voir d'offre qui ne respecte
   pas ce critère (elle sera notée très bas) ; flexible = c'est une préférence ». Un critère sans
   préférence (« peu importe ») est `flexible` avec la valeur `any` ou `0`.

## Étape 3 — Récapitulatif et accord

Affiche un récapitulatif lisible, par bloc, avec pour chaque critère `obligatoire` ou `flexible`.
Termine par : « C'est bon pour toi ? Tu peux corriger n'importe quelle ligne. »

- Corrections : applique-les et réaffiche seulement les lignes modifiées.
- Accord explicite (« oui », « ok », « c'est bon », « valide ») : écris `config/candidate.yml`
  au format de `config/candidate.example.yml`, avec `schema_version: 1`, `updated_at` à
  l'instant présent (ISO 8601 avec fuseau) et **sans bloc `keywords`** (le skill `keywords` le
  crée). Respecte les règles de format en tête de l'exemple (style bloc, une valeur par ligne,
  dates entre guillemets).
- Ajoute une ligne à `config/candidate.history.log` :
  `2026-10-08T10:00:00+02:00 onboarding : profil créé`.
- Vérifie que le fichier se relit : `scripts/jh check` ne doit pas signaler « candidate.yml
  illisible ».

## Étape 4 — Sources adaptées au profil

Si le candidat n'a aucun diplôme `in_progress` ni obtenu depuis moins de 2 ans, retire
`jobteaser` de `sources.enabled` dans `config/kit.yml` et dis-le en une phrase (« Jobteaser vise
les étudiants, je l'ai désactivé ; dis « réactive Jobteaser » si tu le veux »). Sinon laisse-le.

## Étape 5 — Enchaîner

Dis « Profil enregistré. Je te propose maintenant les mots-clés de recherche. » et lance le skill
`keywords` sans attendre.

## Ce que ce skill ne fait jamais

- Écrire le profil sans accord.
- Envoyer le CV ou le profil à un service extérieur. Tout reste dans le dépôt du candidat.
- Versionner le CV : `config/cv/` est ignoré par Git (le dire si le candidat s'inquiète).
