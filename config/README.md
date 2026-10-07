# config/

Vos réglages et votre profil. Deux fichiers principaux, créés par le setup et l'onboarding :

- `kit.yml` : comment le kit tourne. Mode d'exécution (local ou cloud), horaires des passages,
  backend de stockage (CSV ou Airtable), sources actives et leurs plafonds, seuil d'alerte, canal
  de notification. Modifiable en langage naturel via le skill `config`. Référence commentée :
  `kit.example.yml`.
- `candidate.yml` : qui vous êtes et ce que vous cherchez. Parcours, identité, poste visé,
  critères marqués obligatoires ou flexibles, mots-clés validés. Écrit par le skill `onboarding`,
  modifié par les skills `profile` et `keywords`. Référence commentée : `candidate.example.yml`.

Dossiers et fichiers annexes :

- `cv/` : déposez-y votre CV PDF pour pré-remplir le questionnaire. Non versionné par défaut.
- `secrets.env` : clés facultatives (API France Travail, Airtable), que vous remplissez vous-même
  si vous branchez une option. **Jamais versionné**, illisible pour Claude. Modèle :
  `secrets.example.env`.
- `candidate.history.log` : historique des modifications du profil.
