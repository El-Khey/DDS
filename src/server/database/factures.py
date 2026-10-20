"""Lecture des factures."""
from src.server.database.logements import lire_logements_facture
from src.server.database.personnes import lire_personne


def lister_factures(db):
    return db.execute(
        """
        SELECT
            facture.numero,
            facture.date_facture,
            emetteur.id AS emetteur_id,
            emetteur.nom AS emetteur_nom,
            emetteur.prenom AS emetteur_prenom,
            client.nom AS client_nom,
            client.prenom AS client_prenom,
            COALESCE(SUM(ligne_facture.montant), 0) AS total
        FROM facture
        JOIN emetteur ON emetteur.id = facture.id_emetteur
        JOIN client ON client.id = facture.id_client
        LEFT JOIN ligne_facture
            ON ligne_facture.numero_facture = facture.numero
        GROUP BY facture.numero
        ORDER BY facture.date_facture DESC, facture.numero DESC
        """
    ).fetchall()


def _sejour(db, id_sejour):
    if id_sejour is None:
        return None

    sejour = db.execute(
        """
        SELECT id, date_debut, date_fin, statut, montant_total
        FROM sejour
        WHERE id = ?
        """,
        (id_sejour,),
    ).fetchone()
    if sejour is None:
        return None

    return {
        "@idSejour": f"SEJ-{sejour['id']:06d}",
        "date_debut": sejour["date_debut"],
        "date_fin": sejour["date_fin"],
        "statut": sejour["statut"],
        "montant_total": sejour["montant_total"],
    }


def lire_facture(db, numero):
    entete = db.execute(
        """
        SELECT numero, date_facture, id_emetteur, id_client, id_sejour
        FROM facture
        WHERE numero = ?
        """,
        (numero,),
    ).fetchone()
    if entete is None:
        return None

    lignes = db.execute(
        """
        SELECT id_logement, libelle, montant
        FROM ligne_facture
        WHERE numero_facture = ?
        ORDER BY id
        """,
        (numero,),
    ).fetchall()

    # L'ordre des clés est celui des éléments attendus dans le XML.
    facture = {
        "@numero": entete["numero"],
        "@date": entete["date_facture"],
        "emetteur": lire_personne(db, "emetteur", entete["id_emetteur"]),
        "client": lire_personne(db, "client", entete["id_client"]),
    }

    sejour = _sejour(db, entete["id_sejour"])
    if sejour:
        facture["sejour"] = sejour

    facture["offre_logement"] = {"logement": lire_logements_facture(db, numero)}
    facture["details_paiement"] = {
        "ligne_facture": [
            {
                "@refLogement": ligne["id_logement"],
                "libelle": ligne["libelle"],
                "montant": ligne["montant"],
            }
            for ligne in lignes
        ]
    }
    facture["total"] = {
        "@devise": "EUR",
        "#text": sum(ligne["montant"] for ligne in lignes),
    }
    return {"facture": facture}


def lire_toutes_factures(db):
    numeros = db.execute("SELECT numero FROM facture ORDER BY numero").fetchall()
    return [lire_facture(db, ligne["numero"]) for ligne in numeros]
