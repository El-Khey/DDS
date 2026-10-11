# Factures d'offres de logement

Petite application Flask qui montre le parcours demandé en cours :

```text
Formulaire → JSON → SQLite → XML → XSLT → HTML
```

Une seconde page prépare également le parcours :

```text
Texte libre → ILaaS → JSON → SQLite
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
| `make populate COUNT=100` | Génère le nombre demandé de factures |
| `make drop` | Supprime les tables de la base SQLite |
| `make clean` | Supprime les caches Python, sans toucher à la BDD |
| `make help` | Affiche les commandes disponibles |

La base SQLite est créée automatiquement dans :

```text
src/server/instance/refuge_climatique.sqlite
```

Pour charger un jeu de données complet et reproductible :

```bash
make populate COUNT=100
```

Cette commande remplace les données présentes par le nombre demandé de
factures valides. Les noms, prénoms, adresses, prix, charges et dates sont
combinés aléatoirement à partir des listes de `data/population.json`. Chaque
facture passe par la validation et l’insertion utilisées par l’application.

## Utilisation

1. Ouvrir **Formulaire**.
2. Remplir la facture et l'offre de logement.
3. Cliquer sur **Enregistrer la facture**.
4. Consulter le résultat en JSON, XML ou HTML.
5. Revenir à l'accueil pour voir les factures enregistrées.

Le serveur vérifie le JSON, les références entre les données et le montant total avant l'insertion dans SQLite.

## XML global et XPath

Le bouton **Télécharger le XML global** génère `base_de_donnees.xml` à partir
de toutes les factures présentes dans SQLite. Le document possède une unique
racine `<base_de_donnees>` contenant les éléments `<facture>`.

Quelques requêtes à exécuter dans un testeur XPath :

```xpath
//facture[client/nom='Dupont']
//logement[loyer_mensuel > 500]
//facture[@numero='FAC-2026-P000001']/emetteur/email/text()
//client/adresse
```

## Organisation

```text
docs/                           # documentation du projet
├── README.md                   # index de la documentation
├── presentation.pptx           # diaporama de présentation
├── presentation-gio.pdf        # autre support de présentation
├── choix-de-la-ville.md         # contexte initial du projet
├── sujet/                       # consignes et documents de rendu
├── schemas/                     # schémas et illustrations complémentaires
└── cours/                       # supports fournis en cours

src/
├── client/                     # ce qui est affiché dans le navigateur
│   ├── pages/                  # pages HTML
│   └── public/
│       ├── css/                # styles
│       └── js/                 # code exécuté dans le navigateur
│
└── server/                     # backend Flask
    ├── app.py                  # création de l'application
    ├── routes/
    │   ├── pages.py            # pages HTML et exports
    │   └── api.py              # routes JSON de l'API
    ├── database/
    │   ├── connexion.py        # connexion et initialisation SQLite
    │   ├── factures.py         # lecture des factures
    │   ├── insertion.py        # insertion d'une facture
    │   └── suppression.py      # suppression des factures
    ├── services/
    │   ├── validation.py       # contrôles JSON et métier
    │   ├── documents.py        # génération XML et HTML
    │   └── ilaas.py            # appel au LLM
    ├── scripts/
    │   └── populate.py         # génération et insertion des données
    ├── data/
    │   └── population.json     # listes utilisées pour le peuplement
    ├── schema/
    │   ├── database.sql        # création des tables
    │   ├── database.drawio     # diagramme BDD
    │   ├── facture.schema.json # validation du JSON
    │   └── facture.xsd         # validation du XML
    ├── examples/
    │   ├── facture.json
    │   └── facture.xml
    ├── xslt/
    │   └── facture.xsl         # transformation XML vers HTML
    └── instance/
        └── refuge_climatique.sqlite
```

Le détail des documents disponibles se trouve dans [`docs/README.md`](docs/README.md).

## ILaaS

La partie formulaire fonctionne sans clé. Pour utiliser la page **Texte libre**, définir les variables fournies par le professeur avant le lancement :

```bash
export ILAAS_API_KEY="cle-fournie-par-le-professeur"
make run
```

L'adresse par défaut est `https://llm.ilaas.fr/v1`. Une autre adresse peut être utilisée avec :

```bash
export ILAAS_API_URL="https://adresse-fournie/v1"
```

La clé reste uniquement sur le serveur et ne doit pas être ajoutée au dépôt.
