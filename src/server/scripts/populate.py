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
    id_sejour = f"SEJ-{index:06d}"
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
    montant_total = sum(montants.values())

    # Dates de séjour
    date_debut_obj = date(2026, 6, 1) + timedelta(days=random.randint(0, 110))
    duree_sejour = random.randint(3, 14)
    date_fin_obj = date_debut_obj + timedelta(days=duree_sejour)

    # Environnement et Refuge Climatique
    environnement = {
        "temperature_moyenne_ete": round(random.uniform(18.0, 26.5), 1),
        "indice_canicule": random.choice(donnees["indices_canicule"]),
        "altitude": random.randint(300, 1800),
        "services_disponibles": random.choice(donnees["services_disponibles"]),
        "informations_meteo": random.choice(donnees["informations_meteo"])
    }

    # Activités à proximité (1 à 3 activités)
    activites_echantillon = random.sample(donnees["activites_types"], k=random.randint(1, 3))
    activites_proximite = []
    for act in activites_echantillon:
        activites_proximite.append({
            "nom": act["nom"],
            "type_activite": act["type"],
            "distance_km": round(random.uniform(0.5, 8.5), 1),
            "description": f"Idéal pour se détendre et profiter de la fraîcheur à proximité."
        })

    return {
        "facture": {
            "@numero": numero,
            "@date": date_debut_obj.isoformat(),
            "emetteur": emetteur,
            "client": client,
            "sejour": {
                "@idSejour": id_sejour,
                "date_debut": date_debut_obj.isoformat(),
                "date_fin": date_fin_obj.isoformat(),
                "statut": "confirme",
                "montant_total": montant_total
            },
            "offre_logement": {
                "logement": [
                    {
                        "@idLogement": reference,
                        "@meuble": random.choice(["oui", "non"]),
                        "type_bien": type_logement["nom"],
                        "description": random.choice(type_logement["descriptions"]),
                        "adresse": adresse_aleatoire(donnees),
                        "loyer_mensuel": loyer,
                        "charges": charges,
                        "depot_garantie": depot,
                        "frais_agence": frais,
                        "environnement_logement": environnement,
                        "activites_proximite": activites_proximite
                    }
                ],
            },
            "details_paiement": {
                "ligne_facture": [
                    {
                        "@refLogement": reference,
                        "libelle": libelle,
                        "montant": montant,
                    }
                    for libelle, montant in montants.items()
                ]
            },
            "total": {"@devise": "EUR", "#text": montant_total},
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

    print(f"Base peuplée avec {nombre} factures, séjours et données environnementales aléatoires.")


def main():
    parser = argparse.ArgumentParser(
        description="Peuple la base avec des factures et séjours aléatoires."
    )
    parser.add_argument("--count", type=entier_positif, default=100)
    arguments = parser.parse_args()
    peupler(arguments.count)


if __name__ == "__main__":
    main()