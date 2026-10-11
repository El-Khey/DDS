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


def _adresse(ligne, prefixe):
    return {
        "rue": ligne[f"{prefixe}_rue"],
        "code_postal": ligne[f"{prefixe}_code_postal"],
        "ville": ligne[f"{prefixe}_ville"],
    }


def _telephones(db, colonne, identifiant):
    lignes = db.execute(
        f"SELECT numero, usage_tel FROM tel WHERE {colonne} = ? ORDER BY id",
        (identifiant,),
    ).fetchall()
    return [
        {
            **({"@usage": ligne["usage_tel"]} if ligne["usage_tel"] else {}),
            "#text": ligne["numero"],
        }
        for ligne in lignes
    ]


def _personne(db, entete, role):
    personne = {
        "nom": entete[f"{role}_nom"],
        "prenom": entete[f"{role}_prenom"],
        "adresse": _adresse(entete, role),
        "email": entete[f"{role}_email"],
    }
    telephones = _telephones(db, f"id_{role}", entete[f"{role}_id"])
    if telephones:
        personne["tel"] = telephones
    return personne


def lire_facture(db, numero):
    entete = db.execute(
        """
        SELECT
            facture.numero,
            facture.date_facture,
            emetteur.id AS emetteur_id,
            emetteur.nom AS emetteur_nom,
            emetteur.prenom AS emetteur_prenom,
            emetteur.email AS emetteur_email,
            adresse_emetteur.rue AS emetteur_rue,
            adresse_emetteur.code_postal AS emetteur_code_postal,
            adresse_emetteur.ville AS emetteur_ville,
            client.id AS client_id,
            client.nom AS client_nom,
            client.prenom AS client_prenom,
            client.email AS client_email,
            adresse_client.rue AS client_rue,
            adresse_client.code_postal AS client_code_postal,
            adresse_client.ville AS client_ville
        FROM facture
        JOIN emetteur ON emetteur.id = facture.id_emetteur
        JOIN adresse AS adresse_emetteur
            ON adresse_emetteur.id = emetteur.id_adresse
        JOIN client ON client.id = facture.id_client
        JOIN adresse AS adresse_client
            ON adresse_client.id = client.id_adresse
        WHERE facture.numero = ?
        """,
        (numero,),
    ).fetchone()

    if entete is None:
        return None

    logements = db.execute(
        """
        SELECT DISTINCT
            logement.id,
            logement.type_bien,
            logement.description,
            logement.loyer_mensuel,
            logement.charges,
            logement.depot_garantie,
            logement.frais_agence,
            logement.meuble,
            adresse.rue,
            adresse.code_postal,
            adresse.ville
        FROM logement
        JOIN adresse ON adresse.id = logement.id_adresse
        JOIN ligne_facture ON ligne_facture.id_logement = logement.id
        WHERE ligne_facture.numero_facture = ?
        ORDER BY logement.id
        """,
        (numero,),
    ).fetchall()

    lignes = db.execute(
        """
        SELECT id_logement, libelle, montant
        FROM ligne_facture
        WHERE numero_facture = ?
        ORDER BY id
        """,
        (numero,),
    ).fetchall()

    offre = logements[0]
    return {
        "facture": {
            "@numero": entete["numero"],
            "@date": entete["date_facture"],
            "emetteur": _personne(db, entete, "emetteur"),
            "client": _personne(db, entete, "client"),
            "offre_logement": {
                "description": offre["description"],
                "type_bien": offre["type_bien"],
                "logement": [
                    {
                        "@idLogement": logement["id"],
                        "@meuble": logement["meuble"],
                        "adresse": {
                            "rue": logement["rue"],
                            "code_postal": logement["code_postal"],
                            "ville": logement["ville"],
                        },
                        "loyer_mensuel": logement["loyer_mensuel"],
                        "charges": logement["charges"],
                        "depot_garantie": logement["depot_garantie"],
                        "frais_d_agence": logement["frais_agence"],
                    }
                    for logement in logements
                ],
            },
            "details_paiement": {
                "ligne_facture": [
                    {
                        "@refLogement": ligne["id_logement"],
                        "libelle": ligne["libelle"],
                        "montant": ligne["montant"],
                    }
                    for ligne in lignes
                ]
            },
            "total": {
                "@devise": "EUR",
                "#text": sum(ligne["montant"] for ligne in lignes),
            },
        }
    }


def lire_proprietaire(db, identifiant):
    proprietaire = db.execute(
        """
        SELECT
            emetteur.id,
            emetteur.prenom,
            emetteur.nom,
            emetteur.email,
            adresse.rue,
            adresse.code_postal,
            adresse.ville
        FROM emetteur
        JOIN adresse
            ON adresse.id = emetteur.id_adresse
        WHERE emetteur.id = ?
        """,
        (identifiant,),
    ).fetchone()

    if proprietaire is None:
        return None

    telephones = db.execute(
        """
        SELECT numero, usage_tel
        FROM tel
        WHERE id_emetteur = ?
        ORDER BY id
        """,
        (identifiant,),
    ).fetchall()

    return {
        "id": proprietaire["id"],
        "prenom": proprietaire["prenom"],
        "nom": proprietaire["nom"],
        "email": proprietaire["email"],
        "adresse": {
            "rue": proprietaire["rue"],
            "code_postal": proprietaire["code_postal"],
            "ville": proprietaire["ville"],
        },
        "telephones": [
            {
                "numero": telephone["numero"],
                "usage": telephone["usage_tel"],
            }
            for telephone in telephones
        ],
    }
