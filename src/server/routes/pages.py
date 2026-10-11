from datetime import date, datetime
from pathlib import Path

from flask import Response, abort, render_template, url_for

from src.server.database.connexion import get_db
from src.server.database.factures import (
    lire_facture,
    lire_proprietaire,
    lister_factures,
)
from src.server.services.documents import facture_vers_html, facture_vers_xml


SERVER_DIR = Path(__file__).resolve().parents[1]


def enregistrer_routes_pages(app):
    @app.get("/")
    def index():
        factures = lister_factures(get_db())
        nombre_factures = f"{len(factures):,}".replace(",", " ")
        return render_template(
            "index.html",
            factures=factures,
            nombre_factures=nombre_factures,
        )

    @app.get("/factures/nouvelle")
    def nouvelle_facture():
        suffixe = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return render_template(
            "creer_facture.html",
            numero_facture=f"FAC-{suffixe}",
            reference_logement=f"LOG-{suffixe}",
            date_facture=date.today().isoformat(),
        )

    @app.get("/import-texte")
    def import_texte():
        return render_template("import_texte.html")

    @app.get("/factures/<string:numero>.xml")
    def exporter_facture_xml(numero):
        payload = lire_facture(get_db(), numero)
        if payload is None:
            abort(404)
        xml = facture_vers_xml(payload, url_for("feuille_xslt"))
        return Response(xml, content_type="application/xml; charset=utf-8")

    @app.get("/factures/<string:numero>.html")
    def afficher_facture_html(numero):
        payload = lire_facture(get_db(), numero)
        if payload is None:
            abort(404)
        return Response(
            facture_vers_html(payload),
            content_type="text/html; charset=utf-8",
        )

    @app.get("/xslt/facture.xsl")
    def feuille_xslt():
        contenu = (SERVER_DIR / "xslt" / "facture.xsl").read_text(
            encoding="utf-8"
        )
        return Response(contenu, content_type="application/xml; charset=utf-8")

    @app.get("/proprietaires/<int:identifiant>")
    def afficher_proprietaire(identifiant):
        proprietaire = lire_proprietaire(get_db(), identifiant)

        if proprietaire is None:
            abort(404)

        return render_template(
            "proprietaire.html",
            proprietaire=proprietaire,
        )
