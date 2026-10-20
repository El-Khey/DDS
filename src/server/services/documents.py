"""Génération et contrôle des documents XML de facture.

Le JSON de la facture reprend la structure du XML : une clé "@nom" devient
un attribut, "#text" le contenu de l'élément, une liste des éléments répétés.
Les présentations (HTML, texte) sont obtenues par des feuilles XSLT.
"""
from pathlib import Path

from lxml import etree


SERVER_DIR = Path(__file__).resolve().parents[1]
XSLT_DIR = SERVER_DIR / "xslt"
SCHEMA_DIR = SERVER_DIR / "schema"

DOCTYPE_FACTURE = '<!DOCTYPE facture SYSTEM "/schema/facture.dtd">'
XSD_BASE_DE_DONNEES = "/schema/base_de_donnees.xsd"


def _remplir_element(element, valeur):
    if not isinstance(valeur, dict):
        element.text = str(valeur)
        return

    for cle, contenu in valeur.items():
        if cle.startswith("@"):
            element.set(cle[1:], str(contenu))
        elif cle == "#text":
            element.text = str(contenu)
        elif isinstance(contenu, list):
            for item in contenu:
                _remplir_element(etree.SubElement(element, cle), item)
        else:
            _remplir_element(etree.SubElement(element, cle), contenu)


def _serialiser(racine, doctype=None):
    return etree.tostring(
        racine.getroottree(),
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
        doctype=doctype,
    )


def _transformer(payload, feuille):
    xml = etree.fromstring(facture_vers_xml(payload))
    transformation = etree.XSLT(etree.parse(str(XSLT_DIR / feuille)))
    return str(transformation(xml))


def facture_vers_xml(payload, feuille_style=None):
    racine = etree.Element("facture")
    _remplir_element(racine, payload["facture"])

    if feuille_style:
        instruction = etree.ProcessingInstruction(
            "xml-stylesheet",
            f'type="text/xsl" href="{feuille_style}"',
        )
        racine.addprevious(instruction)

    return _serialiser(racine, DOCTYPE_FACTURE)


def facture_vers_html(payload):
    return _transformer(payload, "facture.xsl")


def facture_vers_texte(payload):
    return _transformer(payload, "facture-texte.xsl")


def factures_vers_xml(factures):
    racine = etree.Element(
        "base_de_donnees",
        nsmap={"xsi": "http://www.w3.org/2001/XMLSchema-instance"},
    )
    racine.set(
        "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation",
        XSD_BASE_DE_DONNEES,
    )
    for payload in factures:
        _remplir_element(etree.SubElement(racine, "facture"), payload["facture"])

    return _serialiser(racine)


def erreurs_xml(xml, nom_schema):
    """Valide un document XML contre une DTD ou un XSD du dossier schema."""
    chemin = SCHEMA_DIR / nom_schema
    if chemin.suffix == ".dtd":
        schema = etree.DTD(str(chemin))
    else:
        schema = etree.XMLSchema(etree.parse(str(chemin)))

    schema.validate(etree.fromstring(xml))
    return [f"ligne {erreur.line} : {erreur.message}" for erreur in schema.error_log]
