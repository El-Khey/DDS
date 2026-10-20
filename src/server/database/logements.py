"""Lecture des logements."""
from src.server.database.personnes import lire_personne


SELECTION_LOGEMENT = """
    SELECT DISTINCT
        logement.id_logement,
        logement.id_emetteur,
        logement.type_bien,
        logement.description,
        logement.meuble,
        logement.loyer_mensuel,
        logement.charges,
        logement.depot_garantie,
        logement.frais_agence,
        adresse.rue,
        adresse.code_postal,
        adresse.ville,
        environnement.temperature_moyenne_ete,
        environnement.indice_canicule,
        environnement.altitude,
        environnement.services_disponibles,
        environnement.informations_meteo
    FROM logement
    JOIN adresse ON adresse.id = logement.id_adresse
    LEFT JOIN environnement_logement AS environnement
        ON environnement.id_logement = logement.id_logement
"""

CHAMPS_ENVIRONNEMENT = (
    "temperature_moyenne_ete",
    "indice_canicule",
    "altitude",
    "services_disponibles",
    "informations_meteo",
)


def _activites(db, id_logement):
    lignes = db.execute(
        """
        SELECT nom, type_activite, distance_km, description
        FROM activite_proximite
        WHERE id_logement = ?
        ORDER BY id
        """,
        (id_logement,),
    ).fetchall()
    return [
        {
            cle: ligne[cle]
            for cle in ("nom", "type_activite", "distance_km", "description")
            if ligne[cle] is not None
        }
        for ligne in lignes
    ]


def _logement(db, ligne):
    logement = {
        "@idLogement": ligne["id_logement"],
        "@meuble": "oui" if ligne["meuble"] else "non",
        "type_bien": ligne["type_bien"],
        "description": ligne["description"],
        "adresse": {
            "rue": ligne["rue"],
            "code_postal": ligne["code_postal"],
            "ville": ligne["ville"],
        },
        "loyer_mensuel": ligne["loyer_mensuel"],
        "charges": ligne["charges"],
        "depot_garantie": ligne["depot_garantie"],
        "frais_agence": ligne["frais_agence"],
    }

    environnement = {
        cle: ligne[cle] for cle in CHAMPS_ENVIRONNEMENT if ligne[cle] is not None
    }
    if environnement:
        logement["environnement_logement"] = environnement

    activites = _activites(db, ligne["id_logement"])
    if activites:
        logement["activites_proximite"] = {"activite": activites}

    return logement


def lire_logement(db, id_logement):
    """Fiche complète d'un logement, avec son propriétaire."""
    ligne = db.execute(
        SELECTION_LOGEMENT + "WHERE logement.id_logement = ?",
        (id_logement,),
    ).fetchone()
    if ligne is None:
        return None

    logement = _logement(db, ligne)
    logement["proprietaire"] = lire_personne(db, "emetteur", ligne["id_emetteur"])
    return {"logement": logement}


def lire_logements_facture(db, numero):
    """Logements concernés par les lignes d'une facture."""
    lignes = db.execute(
        SELECTION_LOGEMENT
        + """
        JOIN ligne_facture ON ligne_facture.id_logement = logement.id_logement
        WHERE ligne_facture.numero_facture = ?
        ORDER BY logement.id_logement
        """,
        (numero,),
    ).fetchall()
    return [_logement(db, ligne) for ligne in lignes]


def lister_logements(db):
    """Résumé de tous les logements pour la page de liste."""
    return db.execute(
        """
        SELECT
            logement.id_logement,
            logement.type_bien,
            logement.meuble,
            logement.loyer_mensuel,
            logement.charges,
            adresse.ville,
            emetteur.id AS id_emetteur,
            emetteur.nom AS emetteur_nom,
            emetteur.prenom AS emetteur_prenom,
            environnement.temperature_moyenne_ete,
            environnement.altitude
        FROM logement
        JOIN adresse ON adresse.id = logement.id_adresse
        JOIN emetteur ON emetteur.id = logement.id_emetteur
        LEFT JOIN environnement_logement AS environnement
            ON environnement.id_logement = logement.id_logement
        ORDER BY logement.id_logement DESC
        """
    ).fetchall()


def lister_logements_proprietaire(db, id_emetteur):
    return db.execute(
        """
        SELECT logement.id_logement, logement.type_bien, adresse.ville
        FROM logement
        JOIN adresse ON adresse.id = logement.id_adresse
        WHERE logement.id_emetteur = ?
        ORDER BY logement.id_logement
        """,
        (id_emetteur,),
    ).fetchall()
