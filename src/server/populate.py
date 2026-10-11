import argparse
import json
import random
import sqlite3
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from src.server.database import migrer_db
from src.server.factures import (
    inserer_facture,
    supprimer_toutes_factures,
    valider_facture,
)


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "instance" / "refuge_climatique.sqlite"
SCHEMA_PATH = BASE_DIR / "schema" / "database.sql"
DATA_PATH = BASE_DIR / "data" / "population.json"


def entier_positif(valeur):
    nombre = int(valeur)
    if nombre < 1:
        raise argparse.ArgumentTypeError("le nombre de factures doit être positif")
    return nombre


def adresse_aleatoire(donnees):
    ville = random.choice(donnees["villes"])
    return {
        "rue": f"{random.randint(1, 180)} {random.choice(donnees['voies'])}",
        "code_postal": ville["code_postal"],
        "ville": ville["nom"],
    }


def texte_pour_email(texte):
    sans_accents = unicodedata.normalize("NFKD", texte)
    return "".join(
        caractere
        for caractere in sans_accents
        if caractere.isascii() and caractere.isalnum()
    )


def personne_aleatoire(donnees):
    prenom = random.choice(donnees["prenoms"])
    nom = random.choice(donnees["noms"])
    return {
        "nom": nom,
        "prenom": prenom,
        "adresse": adresse_aleatoire(donnees),
        "email": f"{texte_pour_email(prenom)}{texte_pour_email(nom)}@gmail.com",
        "tel": [
            {
                "@usage": "mobile",
                "#text": f"06{random.randint(0, 99_999_999):08d}",
            }
        ],
    }


def generer_facture(index, donnees):
    numero = f"FAC-2026-P{index:06d}"
    reference = f"LOG-P{index:06d}"
    emetteur = personne_aleatoire(donnees)
    client = personne_aleatoire(donnees)
    while client["email"] == emetteur["email"]:
        client = personne_aleatoire(donnees)
    type_logement = random.choice(donnees["types_logement"])

    loyer = random.randint(350, 1300)
    charges = random.randint(0, 120)
    depot = random.randint(300, 1500)
    frais = random.choice([0, random.randint(80, 250)])

    montants = {
        "Loyer mensuel": loyer,
        "Charges": charges,
        "Dépôt de garantie": depot,
        "Frais d'agence": frais,
    }
    lignes = [
        {"@refLogement": reference, "libelle": libelle, "montant": montant}
        for libelle, montant in montants.items()
    ]

    return {
        "facture": {
            "@numero": numero,
            "@date": (
                date(2026, 6, 1) + timedelta(days=random.randint(0, 121))
            ).isoformat(),
            "emetteur": emetteur,
            "client": client,
            "offre_logement": {
                "description": random.choice(type_logement["descriptions"]),
                "type_bien": type_logement["nom"],
                "logement": [
                    {
                        "@idLogement": reference,
                        "@meuble": random.choice(["oui", "non"]),
                        "adresse": adresse_aleatoire(donnees),
                        "loyer_mensuel": loyer,
                        "charges": charges,
                        "depot_garantie": depot,
                        "frais_d_agence": frais,
                    }
                ],
            },
            "details_paiement": {"ligne_facture": lignes},
            "total": {"@devise": "EUR", "#text": sum(montants.values())},
        }
    }


def peupler(nombre):
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
    except Exception:
        supprimer_toutes_factures(db)
        raise
    finally:
        db.close()

    print(f"Base peuplée avec {nombre} factures aléatoires.")


def main():
    parser = argparse.ArgumentParser(description="Peuple la base avec des factures aléatoires.")
    parser.add_argument("--count", type=entier_positif, default=100)
    arguments = parser.parse_args()
    peupler(arguments.count)


if __name__ == "__main__":
    main()
