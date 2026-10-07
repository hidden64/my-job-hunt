---
name: summary
description: Afficher le résumé Job Hunter du jour ou d'un autre jour, et le journal des derniers passages. À utiliser quand le candidat dit "montre-moi le résumé du jour", "quoi de neuf", "qu'est-ce qui s'est passé hier", "les nouvelles offres", "comment s'est passée la dernière collecte", "pourquoi Indeed ne marche pas".
---

# Skill `summary` — résumé et journaux

## Résumé d'un jour

`scripts/jh summary` (aujourd'hui) ou `scripts/jh summary --date AAAA-MM-JJ` (« hier » = la veille,
« lundi » = le dernier lundi). La commande régénère `data/summaries/<date>.md` et renvoie
`markdown`, `new`, `above`, `warnings`, `top`.

Affiche le contenu de `markdown` tel quel (le tableau tient sur un écran), puis une phrase de
conclusion utile :

- offres au-dessus du seuil : « Tu veux que je t'ouvre la meilleure, ou que je marque celles qui
  ne t'intéressent pas ? » ;
- aucune offre : dire depuis quand, et si les sources ont bien tourné (voir journal) ;
- avertissements : les reprendre en une phrase chacun avec l'action proposée.

## Dernière collecte, problèmes de source

Lis le journal le plus récent `data/runs/<AAAA-MM-JJ-HHMM>.md` (le nom le plus grand), ou celui de
la date demandée, et l'état `scripts/jh state`. Explique en langage simple :

| Statut | Explication au candidat |
|---|---|
| `ok` | la source a répondu normalement |
| `blocked` | le site a demandé une vérification anti-robot ou une connexion ; le kit s'est arrêté poliment, il réessaiera au prochain passage |
| `error` | problème réseau ou page inattendue ; si ça se répète, le site a peut-être changé (lancer `python3 tests/live_smoke.py` pour les sources HTTP) |
| `unavailable` | source navigateur en mode cloud, ou navigateur non connecté en local |
| `skipped` | la source n'a pas été lancée pendant ce passage (passage interrompu) |

Propose l'action adaptée : rien (blocage ponctuel), « désactive Indeed » après 3 blocages de
suite, connecter Claude in Chrome (`/chrome`) pour les sources navigateur, ou vérifier l'accès
réseau en mode cloud.

## Ce que ce skill ne fait pas

Il ne lance pas de collecte (skill `collect`) et ne modifie aucune offre (skill `offers`).
