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
| `make clean` | Supprime les caches Python, sans toucher à la BDD |
| `make help` | Affiche les commandes disponibles |

La base SQLite est créée automatiquement dans :

```text
src/server/instance/refuge_climatique.sqlite
```

## Utilisation

1. Ouvrir **Formulaire**.
2. Remplir la facture et l'offre de logement.
3. Cliquer sur **Enregistrer la facture**.
4. Consulter le résultat en JSON, XML ou HTML.
5. Revenir à l'accueil pour voir les factures enregistrées.

Le serveur vérifie le JSON, les références entre les données et le montant total avant l'insertion dans SQLite.

## Organisation

```text
src/
├── client/                     # ce qui est affiché dans le navigateur
│   ├── pages/                  # pages HTML
│   └── public/
│       ├── css/                # styles
│       └── js/                 # code exécuté dans le navigateur
│
└── server/                     # backend Flask
    ├── app.py                  # routes HTTP
    ├── database.py             # connexion SQLite
    ├── factures.py             # validation, insertion et export
    ├── ilaas.py                # appel au LLM
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

## ILaaS

La partie formulaire fonctionne sans clé. Pour utiliser la page **Texte libre**, définir les variables fournies par le professeur avant le lancement :

```bash
export ILAAS_API_KEY="cle-fournie-par-le-professeur"
export ILAAS_MODEL="nom-du-modele"
make run
```

L'adresse par défaut est `https://llm.ilaas.fr/v1`. Une autre adresse peut être utilisée avec :

```bash
export ILAAS_API_URL="https://adresse-fournie/v1"
```

La clé reste uniquement sur le serveur et ne doit pas être ajoutée au dépôt.
