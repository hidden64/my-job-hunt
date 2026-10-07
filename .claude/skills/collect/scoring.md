# Noter une offre

Tu donnes des **notes par composante** ; le moteur calcule le score final (0 à 100) avec les poids
de `config/kit.yml` → `scoring.weights` et plafonne à `scoring.hard_filter_cap` si un critère
obligatoire est violé. Méthode complète et exemples : `docs/SCORING.md`.

## Format d'un lot

```json
[
  {
    "id": "3f2a9c1b7d4e5f60",
    "components": {
      "title_match": 9,
      "skills_match": 7,
      "experience_level": 8,
      "location_remote": 10,
      "contract": 10,
      "salary": null,
      "education": 8
    },
    "violations": [],
    "rationale": "CDI hybride à Lyon, SQL et Power BI demandés comme dans ton profil ; salaire non indiqué."
  }
]
```

## Les composantes (0 à 10, ou null si l'information manque)

| Composante | 10 | 5 | 0 |
|---|---|---|---|
| `title_match` | l'intitulé est celui visé ou un intitulé validé | métier voisin (Data Scientist pour Data Analyst) | autre métier |
| `skills_match` | la plupart des compétences demandées sont dans le profil | la moitié | aucune ; `null` si l'offre ne cite aucune compétence |
| `experience_level` | expérience demandée ≤ celle du candidat, niveau cohérent | 1 à 2 ans d'écart | niveau très au-dessus ; `null` si non précisé |
| `location_remote` | dans la zone et télétravail conforme au souhait | zone limite ou télétravail différent mais acceptable | hors zone sans télétravail |
| `contract` | type de contrat souhaité | contrat non souhaité mais critère flexible | — ; `null` si le contrat est inconnu (`autre`) |
| `salary` | ≥ salaire minimum | légèrement en dessous | très en dessous ; `null` si non indiqué ou si `salary_min` vaut 0 |
| `education` | diplôme, cours ou spécialisation directement utiles | en partie | sans rapport ; `null` si l'offre n'en dit rien |

Une composante inconnue (`null`) ne pénalise pas : elle est simplement ignorée dans le calcul.

## Critères obligatoires violés (`violations`)

Pour chaque critère du profil marqué `priority: required`, vérifie si l'offre le **contredit
clairement**. Si oui, ajoute sa clé : `location`, `remote`, `contract`, `experience_years`,
`languages`, `salary_min`, `availability`.

- Contredire, c'est une information explicite contraire : « Stage » alors que le contrat exigé est
  CDI ; « 100 % présentiel » alors que l'hybride est exigé ; « Paris » alors que Lyon est exigé
  sans télétravail ; « 5 ans d'expérience minimum » pour 1 an.
- Une information **absente** n'est pas une violation (salaire non indiqué, télétravail non
  précisé).

## La justification (`rationale`)

1 à 2 phrases, en français, factuelles, du point de vue du candidat. Commence par ce qui compte le
plus. Si un critère obligatoire est violé, le dire en premier.

- « Stage de 6 mois alors que tu cherches un CDI ou une alternance (obligatoire). »
- « CDI à Écully avec Power BI et SQL, exige 2 ans d'expérience contre 1 dans ton profil. »
- « Intitulé et compétences alignés, mais Paris sans télétravail mentionné. »

## Rapidité

Une offre se note en quelques secondes à partir du titre, de l'entreprise, du lieu, du contrat et
de l'extrait de description. Ne va pas chercher la page de l'offre.
