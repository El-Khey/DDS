# Factures d'offres de logement

Application Flask du projet « Ville refuge climatique » (cours DDS). Elle suit
les parcours demandés en cours :

```text
Formulaire → JSON → SQLite → XML → XSLT → HTML / texte imprimable
Texte libre → ILaaS → JSON → SQLite
SQLite → JSON du logement → programme Python → HTML / texte imprimable
```

## Lancer le projet

À la racine du projet :

```bash
make install
export ILAAS_API_KEY="clé_api_du_prof"
make run
```

Ouvrir ensuite <http://127.0.0.1:5000>.

Pour développer avec le rechargement automatique :

```bash
make dev
```

## Commandes

| Commande | Utilité |
|---|---|
| `make install` | Crée `.venv` et installe les dépendances |
| `make run` | Lance l'application |
| `make dev` | Lance l'application en mode debug |
| `make populate COUNT=100 SEED=1` | Génère les factures et écrit `src/server/data/peuplement.sql` |
| `make verifier` | Vérifie les exemples contre les schémas JSON, DTD et XSD |
| `make drop` | Supprime les tables de la base SQLite |
| `make clean` | Supprime les caches Python, sans toucher à la BDD |
| `make help` | Affiche les commandes disponibles |

La base SQLite est créée automatiquement dans :

```text
src/server/instance/refuge_climatique.sqlite
```

## Peuplement

```bash
make populate COUNT=100
```

Cette commande remplace les données présentes par le nombre demandé de
factures valides. Les noms, adresses, prix et dates sont combinés à partir des
listes de `src/server/data/population.json`. Avec la même graine (`SEED`), le
jeu de données est identique d'une machine à l'autre.

Chaque facture passe par la validation et l'insertion de l'application. Les
INSERT correspondants sont écrits dans `src/server/data/peuplement.sql`, qui
peut être rejoué sur une base vide.

## Pages et documents produits

| Adresse | Contenu | Technique |
|---|---|---|
| `/` | Liste des factures | Jinja |
| `/factures/nouvelle` | Formulaire de création d'une facture | JSON construit côté navigateur |
| `/import-texte` | Description en texte libre | LLM ILaaS → JSON |
| `/factures/<numero>.xml` | Facture XML du séjour (DTD + feuille de style) | lxml |
| `/factures/<numero>.html` | Facture mise en page | XSLT `facture.xsl` |
| `/factures/<numero>.txt` | Facture imprimable en texte | XSLT `facture-texte.xsl` |
| `/factures.xml` | Toutes les factures dans un seul XML | lxml |
| `/logements` | Liste des logements | Jinja |
| `/logements/<id>.html` | Fiche de présentation d'un logement (RDFa) | Python + Jinja depuis le JSON |
| `/logements/<id>.txt` | Fiche imprimable en texte | Python depuis le JSON |
| `/proprietaires/<id>` | Page d'un propriétaire annotée en RDFa | Jinja |
| `/schema/<fichier>` | DTD, XSD et JSON Schema du projet | — |

API JSON :

| Méthode et adresse | Rôle |
|---|---|
| `POST /api/factures` | Enregistre une facture (validation JSON Schema puis règles métier) |
| `POST /api/factures/depuis-texte` | Texte libre → ILaaS → facture |
| `GET /api/factures/<numero>` | Facture en JSON |
| `DELETE /api/factures/<numero>` | Supprime une facture |
| `DELETE /api/factures` | Supprime toutes les factures |
| `GET /api/logements/<id>` | Logement en JSON (format `logement.schema.json`) |
| `GET /api/population` | Listes servant au bouton « Aléatoire » du formulaire |

## Formats

Le JSON reprend la structure du XML : une clé `@nom` devient un attribut,
`#text` le contenu d'un élément et une liste des éléments répétés. Le même
document existe donc dans les deux formats.

| Fichier | Rôle |
|---|---|
| `schema/logement.schema.json` | JSON Schema de la description d'un logement |
| `schema/facture.schema.json` | JSON Schema de la facture, qui référence (`$ref`) celui du logement |
| `schema/facture.dtd` | DTD de la facture XML |
| `schema/facture.xsd` | XML Schema de la facture XML |
| `schema/base_de_donnees.dtd` / `.xsd` | Modèles de l'export XML complet |
| `examples/` | Un logement, une facture en JSON et la même facture en XML |

Le serveur vérifie le JSON contre le schéma, puis les règles métier : dates
valides, fin de séjour après le début, lignes de facture rattachées à un
logement de l'offre, total égal à la somme des lignes et au montant du séjour.

## XML global et XPath

Le bouton **Télécharger le XML global** génère `base_de_donnees.xml` à partir
de toutes les factures présentes dans SQLite. Le document possède une unique
racine `<base_de_donnees>` contenant les éléments `<facture>` décrits par
`facture.xsd`.

Quelques requêtes à exécuter dans un testeur XPath :

```xpath
//facture[client/nom='Dupont']
//logement[loyer_mensuel > 500]
//facture[@numero='FAC-2026-P000001']/emetteur/email/text()
//logement[environnement_logement/altitude > 1000]/adresse/ville
//activite[type_activite='baignade']/ancestor::logement/@idLogement
count(//facture[sejour/statut='confirme'])
sum(//facture/total)
```

## Organisation

```text
docs/                           # documentation du projet
├── README.md                   # index de la documentation
├── revue-projet.md             # support de la revue de projet
├── presentation.pptx           # diaporama de présentation
├── presentation-gio.pdf        # autre support de présentation
├── choix-de-la-ville.md        # contexte initial du projet
├── sujet/                      # consignes et documents de rendu
├── schemas/                    # schémas et illustrations complémentaires
└── cours/                      # supports fournis en cours

src/
├── client/                     # ce qui est affiché dans le navigateur
│   ├── pages/                  # pages HTML (gabarits Jinja)
│   └── public/
│       ├── css/                # styles
│       └── js/                 # code exécuté dans le navigateur
│
└── server/                     # backend Flask
    ├── app.py                  # création de l'application
    ├── routes/
    │   ├── pages.py            # pages HTML et documents (XML, HTML, texte)
    │   └── api.py              # routes JSON de l'API
    ├── database/
    │   ├── connexion.py        # connexion et initialisation SQLite
    │   ├── factures.py         # lecture des factures
    │   ├── logements.py        # lecture des logements
    │   ├── personnes.py        # lecture des émetteurs et clients
    │   ├── insertion.py        # insertion d'une facture
    │   └── suppression.py      # suppression des factures
    ├── services/
    │   ├── validation.py       # contrôles JSON Schema et métier
    │   ├── documents.py        # facture : JSON → XML, XSLT, validation DTD/XSD
    │   ├── fiche_logement.py   # logement : JSON → HTML / texte (programme)
    │   └── ilaas.py            # appel au LLM
    ├── scripts/
    │   ├── populate.py         # génération des données et du fichier SQL
    │   └── verifier_exemples.py # exemples contre les schémas
    ├── data/
    │   ├── population.json     # listes utilisées pour le peuplement
    │   └── peuplement.sql      # jeu de données généré
    ├── schema/                 # database.sql, DTD, XSD, JSON Schema
    ├── examples/               # facture.json, facture.xml, logement.json
    ├── xslt/
    │   ├── facture.xsl         # facture XML → HTML
    │   └── facture-texte.xsl   # facture XML → texte imprimable
    └── instance/
        └── refuge_climatique.sqlite
```

Le détail des documents disponibles se trouve dans [`docs/README.md`](docs/README.md).

## ILaaS

La partie formulaire fonctionne sans clé. Pour utiliser la page **Texte libre**, définir la variable fournie par le professeur avant le lancement :

```bash
export ILAAS_API_KEY="cle-fournie-par-le-professeur"
make run
```

L'adresse par défaut est `https://llm.ilaas.fr/v1`. Une autre adresse peut être utilisée avec :

```bash
export ILAAS_API_URL="https://autre-adresse/v1"
```
