"""Vérifie les exemples du dossier examples contre les schémas du projet.

    python -m src.server.scripts.verifier_exemples

- facture.json   → facture.schema.json (qui référence logement.schema.json)
- logement.json  → logement.schema.json
- facture.xml    → facture.dtd et facture.xsd
- le XML produit depuis facture.json → facture.dtd et facture.xsd
"""
import json
import sys
from pathlib import Path

from src.server.services.documents import erreurs_xml, facture_vers_xml
from src.server.services.validation import (
    DocumentInvalide,
    valider_facture,
    valider_logement,
)


EXEMPLES = Path(__file__).resolve().parents[1] / "examples"


def charger_json(nom):
    return json.loads((EXEMPLES / nom).read_text(encoding="utf-8"))


def verifier(titre, erreurs):
    etat = "OK" if not erreurs else "ERREUR"
    print(f"[{etat}] {titre}")
    for erreur in erreurs:
        print(f"       {erreur}")
    return not erreurs


def erreurs_json(valider, payload):
    try:
        valider(payload)
    except DocumentInvalide as erreur:
        return erreur.erreurs
    return []


def main():
    facture = charger_json("facture.json")
    xml_exemple = (EXEMPLES / "facture.xml").read_bytes()
    xml_genere = facture_vers_xml(facture)

    resultats = [
        verifier("facture.json → facture.schema.json", erreurs_json(valider_facture, facture)),
        verifier("logement.json → logement.schema.json", erreurs_json(valider_logement, charger_json("logement.json"))),
        verifier("facture.xml → facture.dtd", erreurs_xml(xml_exemple, "facture.dtd")),
        verifier("facture.xml → facture.xsd", erreurs_xml(xml_exemple, "facture.xsd")),
        verifier("XML généré depuis facture.json → facture.dtd", erreurs_xml(xml_genere, "facture.dtd")),
        verifier("XML généré depuis facture.json → facture.xsd", erreurs_xml(xml_genere, "facture.xsd")),
    ]
    sys.exit(0 if all(resultats) else 1)


if __name__ == "__main__":
    main()
