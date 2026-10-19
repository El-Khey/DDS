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
                logement["type_bien"],       
                logement["description"],
                logement["loyer_mensuel"],
                logement["charges"],
                logement["depot_garantie"],
                logement.get("frais_agence", 0),
                logement.get("@meuble", "non"),
            ),
        )

        # Insertion de l'environnement / refuge climatique si présent
        env = logement.get("environnement_logement")
        if env:
            db.execute(
                """
                INSERT INTO environnement_logement (
                    id_logement, temperature_moyenne_ete, indice_canicule,
                    altitude, services_disponibles, informations_meteo
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    logement["@idLogement"],
                    env.get("temperature_moyenne_ete"),
                    env.get("indice_canicule"),
                    env.get("altitude"),
                    env.get("services_disponibles"),
                    env.get("informations_meteo"),
                ),
            )

        # Insertion des activités à proximité si présentes
        activites = logement.get("activites_proximite", [])
        for act in activites:
            db.execute(
                """
                INSERT INTO activite_proximite (
                    id_logement, nom, type_activite, distance_km, description
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    logement["@idLogement"],
                    act.get("nom"),
                    act.get("type_activite"),
                    act.get("distance_km"),
                    act.get("description"),
                ),
            )
def _inserer_sejour(db, id_client, id_logement, sejour_data):
    curseur = db.execute(
        """
        INSERT INTO sejour (
            id_client, id_logement, date_debut, date_fin, statut, montant_total
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            id_client,
            id_logement,
            sejour_data["date_debut"],
            sejour_data["date_fin"],
            sejour_data["statut"],
            sejour_data["montant_total"],
        ),
    )
    return curseur.lastrowid


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

            # Récupération de l'id du premier logement pour lier le séjour
            id_logement = facture["offre_logement"]["logement"][0]["@idLogement"]
            id_sejour = _inserer_sejour(db, id_client, id_logement, facture["sejour"])

            db.execute(
                """
                INSERT INTO facture (numero, id_emetteur, id_client, id_sejour, date_facture)
                VALUES (?, ?, ?, ?, ?)
                """,
                (facture["@numero"], id_emetteur, id_client, id_sejour, facture["@date"]),
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