---
name: profile
description: Mettre à jour le profil Job Hunter du candidat (config/candidate.yml) après l'onboarding. À utiliser quand le candidat dit "mets à jour mon profil", "change ma localisation", "ajoute un poste visé", "j'ai eu mon diplôme", "je cherche maintenant en CDD aussi", "le télétravail n'est plus obligatoire", "montre mon profil", ou veut refaire le questionnaire. Ne gère pas les mots-clés (voir keywords) ni les réglages techniques (voir config).
---

# Skill `profile` — modifier le profil

Le profil évolue : nouveau diplôme, autre ville, poste affiné. Tu fais une modification **ciblée**
sans refaire tout le questionnaire. Format de référence : `config/candidate.example.yml`.
Questions et valeurs permises : `.claude/skills/onboarding/questions.md`.

## Afficher le profil

« Montre mon profil » : affiche le récapitulatif au format de `questions.md` (section
« Récapitulatif type »), suivi des mots-clés validés et de leur date. Ne montre pas le YAML brut.

## Modifier

1. Lis `config/candidate.yml`. S'il n'existe pas, renvoie vers le skill `onboarding`.
2. Traduis la demande en modifications précises. Ambiguïté : une question courte.
   - « J'ai eu mon diplôme » : passe le diplôme `in_progress` en `obtained`, demande l'année si
     elle n'est pas évidente.
   - « Je cherche aussi en CDD » : ajoute `cdd` à `criteria.contract.value`.
   - « Le télétravail n'est plus obligatoire » : `criteria.remote.priority: flexible`.
   - « Change ma localisation pour Paris » : `city`, `department` (`"75"`), rayon à confirmer.
3. Montre **avant → après** pour chaque champ, sur une ligne :
   `Lieu : Lyon (69), 30 km, flexible → Paris (75), 20 km, flexible`
4. Attends l'accord explicite, puis écris uniquement les champs concernés. Mets à jour
   `updated_at`.
5. Ajoute une ligne à `config/candidate.history.log` :
   `<instant ISO> profile : criteria.location Lyon (69) 30 km -> Paris (75) 20 km`.
6. Si `education.degrees` change (diplôme obtenu), réévalue Jobteaser comme à l'étape 4 du skill
   `onboarding`.

## Après une modification qui change la recherche

Si la modification touche `target`, `criteria.location`, `education.skills` ou
`education.courses` :

> « Ta recherche a changé. Je te propose de régénérer les mots-clés, puis de renoter les offres
> déjà trouvées avec ton nouveau profil. On y va ? »

Sur accord : lance le skill `keywords`, puis le skill `rescore`.

Si la modification touche seulement d'autres critères (contrat, télétravail, salaire,
expérience, langues, disponibilité, ou une priorité obligatoire/flexible) : les mots-clés restent
bons, propose seulement de renoter (skill `rescore`).

## Refaire tout le questionnaire

Sur demande explicite : confirme (« Je repars de zéro, ton profil actuel sera remplacé après ta
validation, d'accord ? »), puis lance le skill `onboarding` en lui indiquant de ne pas s'arrêter à
l'étape 0. L'ancien profil n'est remplacé qu'à la validation du nouveau récapitulatif.

## Jamais

Écrire sans accord. Supprimer l'historique `candidate.history.log`.
