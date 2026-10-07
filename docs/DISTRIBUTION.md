# Distribuer le kit (mainteneur)

Ce document est pour toi, mainteneur du dépôt modèle `klakenyuo/the-job-hunter`. Les candidats
n'en ont pas besoin.

## Principe

Le dépôt est un **modèle privé**. Chaque candidat crée sa **propre copie privée** et ne travaille
jamais dans le modèle : ses données personnelles (profil, CV, offres) vivent dans sa copie. Le
skill `setup` refuse de s'installer dans le modèle.

## Une fois

1. Fusionner la branche de développement dans `main` (la copie d'un modèle part de la branche
   par défaut).
2. GitHub → dépôt → **Settings** → **General** → cocher **Template repository**.
3. Vérifier que `main` ne contient aucune donnée personnelle : pas de `config/kit.yml`, pas de
   `config/candidate.yml`, pas de `data/offers.csv`, `data/runs/` et `data/summaries/` réduits à
   leur README. `scripts/jh check` dans le modèle doit répondre « kit.yml absent ».

## Pour chaque candidat

1. **Settings** → **Collaborators** → **Add people** → son compte GitHub, rôle **Read**.
2. Lui envoyer le message ci-dessous.

> Bonjour,
>
> Voici Job Hunter, un assistant qui cherche des offres pour toi plusieurs fois par jour.
>
> 1. Accepte l'invitation GitHub que tu viens de recevoir.
> 2. Sur la page du dépôt, clique **Use this template** → **Create a new repository**, donne-lui un
>    nom, choisis **Private**, valide.
> 3. Clone **ta** copie sur ton ordinateur (bouton **Code**), ou ouvre-la dans Claude Code sur le
>    web.
> 4. Ouvre Claude Code dans ce dossier et colle :
>    `Installe Job Hunter : lis CLAUDE.md puis lance le skill setup.`
>
> Prérequis : Claude Code installé et connecté à ton compte Claude, Python 3 (Claude te guidera
> s'il manque). Compte 20 minutes pour l'installation et ton profil.

## Mettre à jour les candidats

Une copie faite depuis un modèle ne reçoit pas les mises à jour automatiquement. Pour qu'un
candidat récupère une nouvelle version du kit sans perdre ses données :

```
git remote add modele https://github.com/klakenyuo/the-job-hunter.git
git fetch modele
git merge modele/main --allow-unrelated-histories
```

Ses fichiers personnels (`config/kit.yml`, `config/candidate.yml`, `data/`) n'existent pas dans le
modèle, donc pas de conflit sur eux. En cas de conflit sur un fichier du kit, garder la version du
modèle. Annoncer chaque mise à jour avec la liste des changements.

## Retirer un accès

**Settings** → **Collaborators** → retirer le candidat. Sa copie lui appartient et continue de
fonctionner ; il ne reçoit simplement plus les mises à jour.
