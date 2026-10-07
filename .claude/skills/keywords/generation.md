# Générer les mots-clés

Objectif : les intitulés **que les recruteurs écrivent vraiment** dans les offres pour le poste
visé, pas seulement celui du candidat. Pense comme quelqu'un qui tape dans la barre de recherche de
France Travail ou d'Indeed.

## Intitulés (`titles`)

Partir de `target.title`, puis ajouter dans cet ordre, sans dépasser 15 :

1. L'intitulé exact du candidat, sans mention H/F.
2. Les variantes données par le candidat (`target.variants`).
3. L'équivalent français ou anglais s'il est courant en France (« Data Analyst » / « Analyste de
   données », « Développeur » / « Developer »). Ne pas traduire ce qui ne se dit pas.
4. Les déclinaisons de niveau cohérentes avec `target.seniority` (« Junior Data Analyst »).
   Jamais un niveau au-dessus.
5. Les intitulés voisins réellement utilisés pour le même métier, en tenant compte du secteur
   (public : « Chargé d'études », « Gestionnaire » ; cabinets : « Consultant ») et des cours et
   compétences (un parcours finance oriente vers « Data Analyst Finance », « Contrôleur de gestion
   data »).
6. Si `criteria.contract` contient `alternance` : « Alternance <intitulé> » pour les 1 ou 2
   premiers intitulés (les sites cherchent mal l'alternance sans ce mot).

Règles :

- Intitulés courts (2 à 5 mots), sans ponctuation, sans « H/F », sans ville.
- Pas de doublons proches (« Data Analyst » et « Data analyste » : garder un seul).
- Pas d'intitulé trop large (« Data », « Analyste ») : il ramènerait du bruit.
- Ordre : du plus probable au moins probable. Le premier est toujours l'intitulé du candidat.

## Compétences (`skills`)

5 à 12 mots tirés de `education.skills`, `education.courses` et `education.certifications`, en
gardant ceux qui comptent pour le poste visé. Elles servent au scoring (présence dans la
description de l'offre), pas aux recherches.

## Négatifs (`negative`)

Mots qui, présents dans un titre, signalent à coup sûr une offre hors cible :

- niveau au-dessus du candidat : `senior`, `lead`, `principal`, `manager`, `head`, `directeur`,
  `responsable` (sauf si `seniority` le justifie) ;
- contrats exclus **obligatoires** : `stage` / `stagiaire` si le stage n'est pas dans
  `criteria.contract` et que le contrat est obligatoire ; `alternance` / `apprenti` de même ;
  `freelance` de même ;
- métiers voisins qui polluent la recherche (« Data Analyst » ramène des « Data Engineer » :
  proposer `engineer` seulement si le candidat ne le veut pas).

Mots simples, en minuscules, sans accents nécessaires (la comparaison ignore casse et accents et
porte sur des mots entiers). Pas plus de 10. Jamais un mot présent dans un intitulé conservé.

## Zones (`locations`)

- Zone 1 : `criteria.location.city` et son département.
- Si `radius_km` ≥ 15 : ajouter 1 à 3 grandes communes du rayon où les offres sont fréquentes
  (Lyon : Villeurbanne, Vénissieux, Écully ; Paris : La Défense (`department: "92"`), Boulogne,
  Saint-Denis). Les sources HTTP cherchent par département ou par ville : une zone par grande
  commune suffit.
- `criteria.remote.value: full` : ajouter une zone `label: France`, `city: ""`, `department: ""`
  (recherche nationale), en dernier.
- Toute la France demandée : une seule zone `France`.

Format :

```yaml
locations:
  - label: Lyon
    city: Lyon
    department: "69"
```

## Justifications

Une ligne par élément non évident : d'où il vient (« ton Master », « variante fréquente dans les
offres », « tu vises junior »). Les intitulés 1 et 2 n'en ont pas besoin.
