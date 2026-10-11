import sqlite3

from src.server.services.validation import valider_facture


class FactureExisteDeja(Exception):
    pass


def _inserer_adresse(db, adresse):
    curseur = db.execute(
        "INSERT INTO adresse (rue, code_postal, ville) VALUES (?, ?, ?)",
        (adresse["rue"], adresse["code_postal"], adresse["ville"]),
    )
    return curseur.lastrowid


def _inserer_telephones(db, telephones, *, id_emetteur=None, id_client=None):
    for telephone in telephones or []:
        db.execute(
            """
            INSERT INTO tel (id_emetteur, id_client, numero, usage_tel)
            VALUES (?, ?, ?, ?)
            """,
            (id_emetteur, id_client, telephone["#text"], telephone.get("@usage")),
        )


def _inserer_personne(db, table, personne):
    id_adresse = _inserer_adresse(db, personne["adresse"])
    curseur = db.execute(
        f"""
        INSERT INTO {table} (id_adresse, nom, prenom, email)
        VALUES (?, ?, ?, ?)
        """,
        (id_adresse, personne["nom"], personne["prenom"], personne["email"]),
    )
    identifiant = curseur.lastrowid
    _inserer_telephones(
        db,
        personne.get("tel"),
        id_emetteur=identifiant if table == "emetteur" else None,
        id_client=identifiant if table == "client" else None,
    )
    return identifiant


def _inserer_logements(db, offre):
    for logement in offre["logement"]:
        id_adresse = _inserer_adresse(db, logement["adresse"])
        db.execute(
            """
            INSERT INTO logement (
                id, id_adresse, type_bien, description, loyer_mensuel,
                charges, depot_garantie, frais_agence, meuble
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                logement["@idLogement"],
                id_adresse,
                offre["type_bien"],
                offre["description"],
                logement["loyer_mensuel"],
                logement["charges"],
                logement["depot_garantie"],
                logement.get("frais_d_agence", 0),
                logement.get("@meuble", "non"),
            ),
        )


def _inserer_lignes(db, numero, lignes):
    for ligne in lignes:
        db.execute(
            """
            INSERT INTO ligne_facture (
                numero_facture, id_logement, libelle, montant
            ) VALUES (?, ?, ?, ?)
            """,
            (numero, ligne["@refLogement"], ligne["libelle"], ligne["montant"]),
        )


def inserer_facture(db, payload):
    valider_facture(payload)
    facture = payload["facture"]

    try:
        with db:
            id_emetteur = _inserer_personne(db, "emetteur", facture["emetteur"])
            id_client = _inserer_personne(db, "client", facture["client"])
            _inserer_logements(db, facture["offre_logement"])

            db.execute(
                """
                INSERT INTO facture (numero, id_emetteur, id_client, date_facture)
                VALUES (?, ?, ?, ?)
                """,
                (facture["@numero"], id_emetteur, id_client, facture["@date"]),
            )
            _inserer_lignes(
                db,
                facture["@numero"],
                facture["details_paiement"]["ligne_facture"],
            )
    except sqlite3.IntegrityError as erreur:
        raise FactureExisteDeja(
            "Le numéro de facture ou la référence du logement existe déjà."
        ) from erreur

    return facture["@numero"]
