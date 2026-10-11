import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft4Validator


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "facture.schema.json"


class FactureInvalide(Exception):
    def __init__(self, erreurs):
        super().__init__("La facture est invalide")
        self.erreurs = erreurs


def _validateur():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft4Validator(schema)


def valider_facture(payload):
    erreurs = []
    erreurs_schema = sorted(
        _validateur().iter_errors(payload),
        key=lambda item: list(item.path),
    )
    for erreur in erreurs_schema:
        chemin = ".".join(str(partie) for partie in erreur.absolute_path)
        erreurs.append(f"{chemin or 'racine'} : {erreur.message}")

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
