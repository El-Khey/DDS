"""Peuple la base avec des factures aléatoires mais valides.

    python -m src.server.scripts.populate --count 100 [--sql fichier.sql]

Les noms, adresses et montants sont tirés des listes de data/population.json.
Chaque facture passe par la validation et l'insertion de l'application.
Avec --sql, les INSERT correspondants sont aussi écrits dans un fichier.
"""
import argparse
import json
import random
import sqlite3
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from src.server.database.connexion import migrer_db
from src.server.database.insertion import inserer_facture
from src.server.database.suppression import supprimer_toutes_factures
from src.server.services.validation import valider_facture


SERVER_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = SERVER_DIR / "instance" / "refuge_climatique.sqlite"
SCHEMA_PATH = SERVER_DIR / "schema" / "database.sql"
DATA_PATH = SERVER_DIR / "data" / "population.json"

PREMIER_JOUR_ETE = date(2026, 6, 1)


def entier_positif(valeur):
    nombre = int(valeur)
    if nombre < 1:
        raise argparse.ArgumentTypeError("le nombre de factures doit être positif")
    return nombre


def texte_pour_email(texte):
    sans_accents = unicodedata.normalize("NFKD", texte)
    return "".join(
        caractere
        for caractere in sans_accents
        if caractere.isascii() and caractere.isalnum()
    ).lower()


def adresse_aleatoire(donnees):
    ville = random.choice(donnees["villes"])
    return {
        "rue": f"{random.randint(1, 180)} {random.choice(donnees['voies'])}",
        "code_postal": ville["code_postal"],
        "ville": ville["nom"],
    }


def personne_aleatoire(donnees):
    prenom = random.choice(donnees["prenoms"])
    nom = random.choice(donnees["noms"])
    return {
        "nom": nom,
        "prenom": prenom,
        "adresse": adresse_aleatoire(donnees),
        "email": f"{texte_pour_email(prenom)}.{texte_pour_email(nom)}@gmail.com",
        "tel": [
            {"@usage": "mobile", "#text": f"06{random.randint(0, 99_999_999):08d}"}
        ],
    }


def environnement_aleatoire(donnees):
    return {
        "temperature_moyenne_ete": round(random.uniform(18.0, 26.5), 1),
        "indice_canicule": random.choice(donnees["indices_canicule"]),
        "altitude": random.randint(300, 1800),
        "services_disponibles": random.choice(donnees["services_disponibles"]),
        "informations_meteo": random.choice(donnees["informations_meteo"]),
    }


def activites_aleatoires(donnees):
    choisies = random.sample(donnees["activites_types"], k=random.randint(1, 3))
    return {
        "activite": [
            {
                "nom": activite["nom"],
                "type_activite": activite["type"],
                "distance_km": round(random.uniform(0.5, 8.5), 1),
                "description": "Idéal pour profiter de la fraîcheur à proximité.",
            }
            for activite in choisies
        ]
    }


def logement_aleatoire(reference, donnees, montants):
    type_logement = random.choice(donnees["types_logement"])
    return {
        "@idLogement": reference,
        "@meuble": random.choice(["oui", "non"]),
        "type_bien": type_logement["nom"],
        "description": random.choice(type_logement["descriptions"]),
        "adresse": adresse_aleatoire(donnees),
        "loyer_mensuel": montants["Loyer mensuel"],
        "charges": montants["Charges"],
        "depot_garantie": montants["Dépôt de garantie"],
        "frais_agence": montants["Frais d'agence"],
        "environnement_logement": environnement_aleatoire(donnees),
        "activites_proximite": activites_aleatoires(donnees),
    }


def generer_facture(index, donnees):
    numero = f"FAC-2026-P{index:06d}"
    reference = f"LOG-P{index:06d}"

    emetteur = personne_aleatoire(donnees)
    client = personne_aleatoire(donnees)
    while client["email"] == emetteur["email"]:
        client = personne_aleatoire(donnees)

    montants = {
        "Loyer mensuel": random.randint(350, 1300),
        "Charges": random.randint(0, 120),
        "Dépôt de garantie": random.randint(300, 1500),
        "Frais d'agence": random.choice([0, random.randint(80, 250)]),
    }
    total = sum(montants.values())

    debut = PREMIER_JOUR_ETE + timedelta(days=random.randint(0, 110))
    fin = debut + timedelta(days=random.randint(3, 14))

    return {
        "facture": {
            "@numero": numero,
            "@date": debut.isoformat(),
            "emetteur": emetteur,
            "client": client,
            "sejour": {
                "@idSejour": f"SEJ-{index:06d}",
                "date_debut": debut.isoformat(),
                "date_fin": fin.isoformat(),
                "statut": "confirme",
                "montant_total": total,
            },
            "offre_logement": {
                "logement": [logement_aleatoire(reference, donnees, montants)],
            },
            "details_paiement": {
                "ligne_facture": [
                    {"@refLogement": reference, "libelle": libelle, "montant": montant}
                    for libelle, montant in montants.items()
                ]
            },
            "total": {"@devise": "EUR", "#text": total},
        }
    }


# Ordre d'insertion respectant les clés étrangères
TABLES = (
    "adresse",
    "emetteur",
    "client",
    "tel",
    "logement",
    "environnement_logement",
    "activite_proximite",
    "sejour",
    "facture",
    "ligne_facture",
)


def ecrire_sql(db, chemin):
    """Écrit les INSERT correspondant au contenu de la base."""
    insertions = {table: [] for table in TABLES}
    for ligne in db.iterdump():
        if ligne.startswith("INSERT INTO"):
            table = ligne.split('"')[1]
            if table in insertions:
                insertions[table].append(ligne)

    contenu = [
        "-- Jeu de données généré par src/server/scripts/populate.py",
        "PRAGMA foreign_keys = ON;",
        "BEGIN TRANSACTION;",
    ]
    for table in TABLES:
        contenu += insertions[table]
    contenu.append("COMMIT;")
    chemin.write_text("\n".join(contenu) + "\n", encoding="utf-8")


def peupler(nombre, chemin_sql=None):
    donnees = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    factures = [generer_facture(index, donnees) for index in range(1, nombre + 1)]
    for facture in factures:
        valider_facture(facture)

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    migrer_db(db)

    try:
        supprimer_toutes_factures(db)
        for facture in factures:
            inserer_facture(db, facture)
        if chemin_sql:
            ecrire_sql(db, chemin_sql)
    except Exception:
        supprimer_toutes_factures(db)
        raise
    finally:
        db.close()

    print(f"Base peuplée avec {nombre} factures.")
    if chemin_sql:
        print(f"Insertions SQL écrites dans {chemin_sql}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--count", type=entier_positif, default=100)
    parser.add_argument("--seed", type=int, help="graine pour un jeu reproductible")
    parser.add_argument("--sql", type=Path, help="fichier où écrire les INSERT")
    arguments = parser.parse_args()

    if arguments.seed is not None:
        random.seed(arguments.seed)
    peupler(arguments.count, arguments.sql)


if __name__ == "__main__":
    main()
