"""Contrôle des documents JSON : schéma puis règles métier."""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft4Validator
from referencing import Registry, Resource


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schema"


class DocumentInvalide(Exception):
    def __init__(self, erreurs):
        super().__init__("Le document est invalide")
        self.erreurs = erreurs


class FactureInvalide(DocumentInvalide):
    pass


class LogementInvalide(DocumentInvalide):
    pass


def _charger_schema(nom):
    return json.loads((SCHEMA_DIR / nom).read_text(encoding="utf-8"))


def _validateur(nom):
    # Le schéma de la facture fait référence ($ref) à celui du logement :
    # il doit être connu du validateur pour que la référence soit résolue.
    registre = Resource.from_contents(_charger_schema("logement.schema.json")) @ Registry()
    return Draft4Validator(_charger_schema(nom), registry=registre)


def _erreurs_schema(nom_schema, payload):
    erreurs = sorted(
        _validateur(nom_schema).iter_errors(payload),
        key=lambda erreur: list(erreur.path),
    )
    return [
        f"{'.'.join(str(partie) for partie in erreur.absolute_path) or 'racine'} : "
        f"{erreur.message}"
        for erreur in erreurs
    ]


def _date_valide(valeur):
    try:
        date.fromisoformat(valeur)
    except ValueError:
        return False
    return True


def valider_logement(payload):
    erreurs = _erreurs_schema("logement.schema.json", payload)
    if erreurs:
        raise LogementInvalide(erreurs)


def valider_facture(payload):
    erreurs = _erreurs_schema("facture.schema.json", payload)
    if erreurs:
        raise FactureInvalide(erreurs)

    facture = payload["facture"]
    sejour = facture["sejour"]

    for chemin, valeur in (
        ("facture.@date", facture["@date"]),
        ("facture.sejour.date_debut", sejour["date_debut"]),
        ("facture.sejour.date_fin", sejour["date_fin"]),
    ):
        if not _date_valide(valeur):
            erreurs.append(f"{chemin} : {valeur} n'est pas une date valide")

    if not erreurs and sejour["date_fin"] < sejour["date_debut"]:
        erreurs.append(
            "facture.sejour.date_fin : la fin du séjour précède son début"
        )

    references = {
        logement["@idLogement"]
        for logement in facture["offre_logement"]["logement"]
    }
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

    montant_sejour = Decimal(str(sejour["montant_total"]))
    if montant_sejour != total_calcule:
        erreurs.append(
            f"facture.sejour.montant_total : montant du séjour {montant_sejour}, "
            f"mais total facturé {total_calcule}"
        )

    if erreurs:
        raise FactureInvalide(erreurs)
