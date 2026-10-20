from datetime import date, datetime
from pathlib import Path

from flask import Response, abort, render_template, send_from_directory, url_for

from src.server.database.connexion import get_db
from src.server.database.factures import (
    lire_facture,
    lire_toutes_factures,
    lister_factures,
)
from src.server.database.logements import (
    lire_logement,
    lister_logements,
    lister_logements_proprietaire,
)
from src.server.database.personnes import lire_personne
from src.server.services.documents import (
    facture_vers_html,
    facture_vers_texte,
    facture_vers_xml,
    factures_vers_xml,
)
from src.server.services.fiche_logement import (
    logement_vers_html,
    logement_vers_texte,
)


SERVER_DIR = Path(__file__).resolve().parents[1]

TYPES_SCHEMA = {
    ".dtd": "application/xml-dtd",
    ".xsd": "application/xml",
    ".json": "application/schema+json",
}


def _nombre(valeurs):
    return f"{len(valeurs):,}".replace(",", " ")


def _facture_ou_404(numero):
    payload = lire_facture(get_db(), numero)
    if payload is None:
        abort(404)
    return payload


def _logement_ou_404(id_logement):
    payload = lire_logement(get_db(), id_logement)
    if payload is None:
        abort(404)
    return payload


def enregistrer_routes_pages(app):
    @app.get("/")
    def index():
        factures = lister_factures(get_db())
        return render_template(
            "index.html",
            factures=factures,
            nombre_factures=_nombre(factures),
        )

    @app.get("/factures/nouvelle")
    def nouvelle_facture():
        suffixe = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return render_template(
            "creer_facture.html",
            numero_facture=f"FAC-{suffixe}",
            reference_logement=f"LOG-{suffixe}",
            reference_sejour=f"SEJ-{suffixe}",
            date_facture=date.today().isoformat(),
        )

    @app.get("/import-texte")
    def import_texte():
        return render_template("import_texte.html")

    # Facture d'un séjour : XML, puis HTML et texte par XSLT

    @app.get("/factures/<string:numero>.xml")
    def exporter_facture_xml(numero):
        xml = facture_vers_xml(_facture_ou_404(numero), url_for("feuille_xslt"))
        return Response(xml, content_type="application/xml; charset=utf-8")

    @app.get("/factures/<string:numero>.html")
    def afficher_facture_html(numero):
        return Response(
            facture_vers_html(_facture_ou_404(numero)),
            content_type="text/html; charset=utf-8",
        )

    @app.get("/factures/<string:numero>.txt")
    def imprimer_facture(numero):
        return Response(
            facture_vers_texte(_facture_ou_404(numero)),
            content_type="text/plain; charset=utf-8",
        )

    @app.get("/factures.xml")
    def exporter_toutes_factures_xml():
        xml = factures_vers_xml(lire_toutes_factures(get_db()))
        return Response(
            xml,
            content_type="application/xml; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="base_de_donnees.xml"'
            },
        )

    @app.get("/xslt/facture.xsl")
    def feuille_xslt():
        return send_from_directory(
            SERVER_DIR / "xslt", "facture.xsl", mimetype="application/xml"
        )

    @app.get("/schema/<string:nom>")
    def fichier_schema(nom):
        type_mime = TYPES_SCHEMA.get(Path(nom).suffix)
        if type_mime is None:
            abort(404)
        return send_from_directory(SERVER_DIR / "schema", nom, mimetype=type_mime)

    # Logements : fiche HTML et texte produites à partir du JSON

    @app.get("/logements")
    def lister_offres_logement():
        logements = lister_logements(get_db())
        return render_template(
            "logements.html",
            logements=logements,
            nombre_logements=_nombre(logements),
        )

    @app.get("/logements/<string:id_logement>.html")
    def afficher_logement_html(id_logement):
        return logement_vers_html(_logement_ou_404(id_logement))

    @app.get("/logements/<string:id_logement>.txt")
    def imprimer_logement(id_logement):
        return Response(
            logement_vers_texte(_logement_ou_404(id_logement)),
            content_type="text/plain; charset=utf-8",
        )

    @app.get("/proprietaires/<int:identifiant>")
    def afficher_proprietaire(identifiant):
        db = get_db()
        proprietaire = lire_personne(db, "emetteur", identifiant)
        if proprietaire is None:
            abort(404)

        return render_template(
            "proprietaire.html",
            proprietaire=proprietaire,
            logements=lister_logements_proprietaire(db, identifiant),
        )
