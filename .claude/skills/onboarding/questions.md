# Questions du questionnaire et valeurs permises

Tout ce qui est entre guillemets est une formulation possible, à adapter. Les clés renvoient à
`config/candidate.example.yml`.

## Bloc 1 — Parcours (`education`)

« Commençons par ton parcours. »

| Question | Clé | Format |
|---|---|---|
| « Quel diplôme prépares-tu en ce moment, dans quel établissement, et quand le termines-tu ? » | `degrees[]` avec `status: in_progress` | `title`, `school`, `year` (année de fin prévue), `level` |
| « Quels diplômes as-tu déjà obtenus ? » | `degrees[]` avec `status: obtained` | idem, `year` = année d'obtention |
| « Quels cours ou spécialisations t'ont le plus marqué ou sont les plus utiles pour le poste visé ? » | `courses` | liste de 3 à 10 intitulés courts |
| « Des certifications ? » | `certifications` | liste, vide si aucune |
| « Tes expériences : stages, alternances, jobs ? » | `experiences[]` | `title`, `company`, `months`, `year` |
| « Tes compétences principales (outils, langages, méthodes) ? » | `skills` | liste de mots courts |
| « Quelles langues parles-tu, à quel niveau ? » | `languages[]` | `language`, `level` : natif, C2, C1, B2, B1, A2, A1 |

`level` d'un diplôme : `bac`, `bac+2`, `bac+3`, `bac+5`, `bac+8`. Déduis-le de l'intitulé
(Licence → bac+3, Master/ingénieur → bac+5, BTS/BUT → bac+2/bac+3, Doctorat → bac+8) et fais-le
confirmer.

## Bloc 2 — Identité (`identity`)

« Comment t'appelles-tu ? » → `first_name`, `last_name`. L'e-mail est facultatif et ne sert à
rien pour l'instant : ne le demande pas.

## Bloc 3 — Poste visé (`target`)

| Question | Clé | Format |
|---|---|---|
| « Quel poste cherches-tu, le plus précisément possible ? » | `title` | un intitulé tel qu'il apparaîtrait dans une offre |
| « D'autres intitulés que tu accepterais ? » | `variants` | liste, peut être vide (les mots-clés en proposeront) |
| « Un secteur en particulier ? » | `sector` | texte libre ou `indifférent` |
| « Junior, confirmé ou senior ? » | `seniority` | `junior` (0 à 2 ans), `confirmé` (3 à 6 ans), `senior` (7 ans et plus) ; propose d'après les expériences |

## Bloc 4 — Critères (`criteria`)

Pour chaque ligne, deux réponses : la valeur, et `required` (obligatoire) ou `flexible`.

| Critère | Clé | Valeur | Remarques |
|---|---|---|---|
| Où ? | `location` | `city`, `department` (code à 2 ou 3 caractères, ex. `"69"`, `"2A"`, `"971"`), `radius_km` | Déduis le département de la ville et fais-le confirmer. « Toute la France » : `city: ""`, `department: ""`. |
| Télétravail | `remote` | `none`, `hybrid`, `full`, `any` | « hybride » = quelques jours par semaine ; `any` = peu importe |
| Contrat | `contract` | liste parmi `cdi`, `cdd`, `alternance`, `stage`, `freelance`, `interim` | Plusieurs choix possibles |
| Expérience | `experience_years` | entier | Années d'expérience du candidat (stages et alternances comptent à moitié) |
| Langues exigées | `languages` | liste de textes (« Anglais C1 ») | Ce que le candidat accepte de pratiquer au travail |
| Salaire | `salary_min` | entier, brut annuel en euros ; `0` si indifférent | Pour une alternance ou un stage : `0` sauf demande contraire |
| Disponibilité | `availability` | date `"AAAA-MM-JJ"` | « dès que possible » = date du jour |

Valeurs par défaut si le candidat ne sait pas : `remote: any` flexible, `salary_min: 0` flexible,
`radius_km: 30` flexible.

## Récapitulatif type

```
PARCOURS
- En cours : Master Data Science, Université Lumière Lyon 2, fin 2027 (bac+5)
- Obtenu : Licence Mathématiques appliquées, Lyon 1, 2025 (bac+3)
- Cours : Statistiques bayésiennes, Machine learning, SQL, Visualisation
- Expérience : Stagiaire data analyst, 6 mois (2025)
- Compétences : SQL, Python, Power BI, Excel
- Langues : Français natif, Anglais C1

IDENTITÉ : Camille Martin

POSTE : Data Analyst (junior) — aussi : Analyste de données — secteur indifférent

CRITÈRES
- Lieu : Lyon (69), 30 km ............ flexible
- Télétravail : hybride ............... OBLIGATOIRE
- Contrat : CDI ou alternance ........ OBLIGATOIRE
- Expérience : 1 an ................... flexible
- Langues : Anglais C1 ................ flexible
- Salaire : 35 000 € brut/an minimum .. flexible
- Disponible : 1er juillet 2027 ....... OBLIGATOIRE
```
