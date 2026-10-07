---
name: export
description: Exporter les offres Job Hunter dans un classeur Excel mis en forme. À utiliser quand le candidat dit "exporte mes offres en Excel", "fais-moi un fichier Excel", "je veux un tableur", "export xlsx".
---

# Skill `export` — export Excel

1. `scripts/jh export` (ou `scripts/jh export --path data/exports/<nom>.xlsx` si le candidat
   veut un nom précis). Fonctionne avec les deux stockages (CSV et Airtable).
2. Réponds avec le chemin du fichier et ce qu'il contient :

> Ton export est prêt : `data/exports/offres-2026-10-08.xlsx` (142 offres).
> - Feuille **Offres** : triées par score, en-têtes figés, filtres sur chaque colonne, score en
>   vert au-dessus de ton seuil, en jaune juste en dessous.
> - Feuille **Résumé** : nombre d'offres par source, par statut et par tranche de score.

3. Rappelle une fois que c'est une **copie** : les annotations faites dans Excel ne reviennent pas
   dans Job Hunter. Pour suivre une candidature, dire « j'ai postulé chez … ».

Le dossier `data/exports/` n'est pas versionné : l'export reste sur la machine du candidat.
En session cloud, le fichier est créé dans la session ; propose de le joindre ou de l'envoyer si
l'outil d'envoi de fichiers est disponible.
