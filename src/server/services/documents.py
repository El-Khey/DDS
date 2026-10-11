from pathlib import Path

from lxml import etree


XSLT_PATH = Path(__file__).resolve().parents[1] / "xslt" / "facture.xsl"


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
                enfant = etree.SubElement(element, cle)
                _remplir_element(enfant, item)
        else:
            enfant = etree.SubElement(element, cle)
            _remplir_element(enfant, contenu)


def facture_vers_xml(payload, feuille_style=None):
    racine = etree.Element("facture")
    _remplir_element(racine, payload["facture"])

    if feuille_style:
        instruction = etree.ProcessingInstruction(
            "xml-stylesheet",
            f'type="text/xsl" href="{feuille_style}"',
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


def factures_vers_xml(factures):
    racine = etree.Element("base_de_donnees")

    for payload in factures:
        element_facture = etree.SubElement(racine, "facture")
        _remplir_element(
            element_facture,
            payload["facture"],
        )

    return etree.tostring(
        racine.getroottree(),
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )
