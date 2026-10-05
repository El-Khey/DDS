import json
import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft4Validator
from lxml import etree


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema" / "facture.schema.json"
XSLT_PATH = BASE_DIR / "xslt" / "facture.xsl"


class FactureInvalide(Exception):
    def __init__(self, erreurs):
        super().__init__("La facture est invalide")
        self.erreurs = erreurs


class FactureExisteDeja(Exception):
    pass


def _validateur():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft4Validator(schema)


def valider_facture(payload):
    erreurs = []
    for erreur in sorted(_validateur().iter_errors(payload), key=lambda item: list(item.path)):
        chemin = ".".join(str(partie) for partie in erreur.absolute_path) or "racine"
        erreurs.append(f"{chemin} : {erreur.message}")

    if erreurs:
        raise FactureInvalide(erreurs)

    facture = payload["facture"]
    try:
        date.fromisoformat(facture["@date"])
    except ValueError:
        erreurs.append("facture.@date : la date doit être au format AAAA-MM-JJ")

    logements = facture["offre_logement"]["logement"]
    references = {logement["@idLogement"] for logement in logements}
    lignes = facture["details_paiement"]["ligne_facture"]

    for index, ligne in enumerate(lignes):
        if ligne["@refLogement"] not in references:
            erreurs.append(
                f"facture.details_paiement.ligne_facture.{index}.@refLogement : "
                "le logement référencé n'existe pas dans l'offre"
            )

    total_calcule = sum(Decimal(str(ligne["montant"])) for ligne in lignes)
    total_annonce = Decimal(str(facture["total"]["#text"]))
    if total_calcule != total_annonce:
        erreurs.append(
            f"facture.total.#text : total annoncé {total_annonce}, "
            f"mais somme des lignes {total_calcule}"
        )

    if erreurs:
        raise FactureInvalide(erreurs)


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


def inserer_facture(db, payload):
    valider_facture(payload)
    facture = payload["facture"]
    emetteur = facture["emetteur"]
    client = facture["client"]
    offre = facture["offre_logement"]

    try:
        with db:
            id_adresse_emetteur = _inserer_adresse(db, emetteur["adresse"])
            curseur = db.execute(
                """
                INSERT INTO emetteur (id_adresse, nom, email)
                VALUES (?, ?, ?)
                """,
                (id_adresse_emetteur, emetteur["nom"], emetteur["email"]),
            )
            id_emetteur = curseur.lastrowid
            _inserer_telephones(db, emetteur.get("tel"), id_emetteur=id_emetteur)

            id_adresse_client = _inserer_adresse(db, client["adresse"])
            curseur = db.execute(
                """
                INSERT INTO client (id_adresse, nom, prenom, email)
                VALUES (?, ?, ?, ?)
                """,
                (id_adresse_client, client["nom"], client["prenom"], client["email"]),
            )
            id_client = curseur.lastrowid
            _inserer_telephones(db, client.get("tel"), id_client=id_client)

            for logement in offre["logement"]:
                id_adresse_logement = _inserer_adresse(db, logement["adresse"])
                db.execute(
                    """
                    INSERT INTO logement (
                        id, id_adresse, type_bien, description, loyer_mensuel,
                        charges, depot_garantie, frais_agence, meuble
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        logement["@idLogement"],
                        id_adresse_logement,
                        offre["type_bien"],
                        offre["description"],
                        logement["loyer_mensuel"],
                        logement["charges"],
                        logement["depot_garantie"],
                        logement.get("frais_d_agence", 0),
                        logement.get("@meuble", "non"),
                    ),
                )

            db.execute(
                """
                INSERT INTO facture (numero, id_emetteur, id_client, date_facture)
                VALUES (?, ?, ?, ?)
                """,
                (facture["@numero"], id_emetteur, id_client, facture["@date"]),
            )

            for ligne in facture["details_paiement"]["ligne_facture"]:
                db.execute(
                    """
                    INSERT INTO ligne_facture (
                        numero_facture, id_logement, libelle, montant
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        facture["@numero"],
                        ligne["@refLogement"],
                        ligne["libelle"],
                        ligne["montant"],
                    ),
                )
    except sqlite3.IntegrityError as erreur:
        raise FactureExisteDeja(
            "Le numéro de facture ou la référence du logement existe déjà."
        ) from erreur

    return facture["@numero"]


def _adresse_depuis_ligne(ligne, prefixe):
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


def lire_facture(db, numero):
    entete = db.execute(
        """
        SELECT
            facture.numero,
            facture.date_facture,
            emetteur.id AS emetteur_id,
            emetteur.nom AS emetteur_nom,
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
        JOIN adresse AS adresse_emetteur ON adresse_emetteur.id = emetteur.id_adresse
        JOIN client ON client.id = facture.id_client
        JOIN adresse AS adresse_client ON adresse_client.id = client.id_adresse
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

    lignes_facture = db.execute(
        """
        SELECT id_logement, libelle, montant
        FROM ligne_facture
        WHERE numero_facture = ?
        ORDER BY id
        """,
        (numero,),
    ).fetchall()

    emetteur = {
        "nom": entete["emetteur_nom"],
        "adresse": _adresse_depuis_ligne(entete, "emetteur"),
        "email": entete["emetteur_email"],
    }
    telephones_emetteur = _telephones(db, "id_emetteur", entete["emetteur_id"])
    if telephones_emetteur:
        emetteur["tel"] = telephones_emetteur

    client = {
        "nom": entete["client_nom"],
        "prenom": entete["client_prenom"],
        "adresse": _adresse_depuis_ligne(entete, "client"),
        "email": entete["client_email"],
    }
    telephones_client = _telephones(db, "id_client", entete["client_id"])
    if telephones_client:
        client["tel"] = telephones_client

    premiere_offre = logements[0]
    logements_json = [
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
    ]
    lignes_json = [
        {
            "@refLogement": ligne["id_logement"],
            "libelle": ligne["libelle"],
            "montant": ligne["montant"],
        }
        for ligne in lignes_facture
    ]

    return {
        "facture": {
            "@numero": entete["numero"],
            "@date": entete["date_facture"],
            "emetteur": emetteur,
            "client": client,
            "offre_logement": {
                "description": premiere_offre["description"],
                "type_bien": premiere_offre["type_bien"],
                "logement": logements_json,
            },
            "details_paiement": {"ligne_facture": lignes_json},
            "total": {
                "@devise": "EUR",
                "#text": sum(ligne["montant"] for ligne in lignes_facture),
            },
        }
    }


def _remplir_element(element, valeur):
    if isinstance(valeur, dict):
        for cle, contenu in valeur.items():
            if cle.startswith("@"):
                element.set(cle[1:], str(contenu))
            elif cle == "#text":
                element.text = str(contenu)
            elif isinstance(contenu, list):
                for item in contenu:
                    enfant = etree.SubElement(element, cle)
                    _remplir_element(enfant, item)
            else:
                enfant = etree.SubElement(element, cle)
                _remplir_element(enfant, contenu)
    else:
        element.text = str(valeur)


def facture_vers_xml(payload, feuille_style=None):
    racine = etree.Element("facture")
    _remplir_element(racine, payload["facture"])

    if feuille_style:
        instruction = etree.ProcessingInstruction(
            "xml-stylesheet", f'type="text/xsl" href="{feuille_style}"'
        )
        racine.addprevious(instruction)

    return etree.tostring(
        racine.getroottree(),
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )


def facture_vers_html(payload):
    xml = etree.fromstring(facture_vers_xml(payload))
    transformation = etree.XSLT(etree.parse(str(XSLT_PATH)))
    return str(transformation(xml))
