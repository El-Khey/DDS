from datetime import date, datetime
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, request, url_for

from src.server.database import get_db, init_app, init_db
from src.server.factures import (
    FactureExisteDeja,
    FactureInvalide,
    facture_vers_html,
    facture_vers_xml,
    inserer_facture,
    lire_facture,
)
from src.server.ilaas import ErreurIlaas, IlaasNonConfigure, description_vers_facture


BASE_DIR = Path(__file__).resolve().parent
CLIENT_DIR = BASE_DIR.parent / "client"


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(CLIENT_DIR / "pages"),
        static_folder=str(CLIENT_DIR / "public"),
        static_url_path="/public",
    )
    app.config.from_mapping(
        DATABASE=BASE_DIR / "instance" / "refuge_climatique.sqlite",
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    init_app(app)

    with app.app_context():
        init_db()

    @app.get("/")
    def index():
        factures = get_db().execute(
            """
            SELECT
                facture.numero,
                facture.date_facture,
                emetteur.nom AS emetteur_nom,
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
        return render_template("index.html", factures=factures)

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

    @app.post("/api/factures")
    def creer_facture_api():
        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify(erreur="Le corps de la requête doit être un objet JSON."), 400

        try:
            numero = inserer_facture(get_db(), payload)
        except FactureInvalide as erreur:
            return jsonify(erreur="JSON invalide", details=erreur.erreurs), 400
        except FactureExisteDeja as erreur:
            return jsonify(erreur=str(erreur)), 409

        return jsonify(_reponse_creation(numero)), 201

    @app.post("/api/factures/depuis-texte")
    def creer_facture_depuis_texte_api():
        donnees = request.get_json(silent=True) or {}
        description = str(donnees.get("description", "")).strip()
        if not description:
            return jsonify(erreur="La description ne peut pas être vide."), 400

        try:
            payload = description_vers_facture(description)
            numero = inserer_facture(get_db(), payload)
        except IlaasNonConfigure as erreur:
            return jsonify(erreur=str(erreur)), 503
        except ErreurIlaas as erreur:
            return jsonify(erreur=str(erreur)), 502
        except FactureInvalide as erreur:
            return jsonify(
                erreur="Le JSON produit par ILaaS est invalide.",
                details=erreur.erreurs,
            ), 422
        except FactureExisteDeja as erreur:
            return jsonify(erreur=str(erreur)), 409

        reponse = _reponse_creation(numero)
        reponse["json_genere"] = payload
        return jsonify(reponse), 201

    @app.get("/api/factures/<string:numero>")
    def lire_facture_api(numero):
        payload = lire_facture(get_db(), numero)
        if payload is None:
            abort(404)
        return jsonify(payload)

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
        contenu = (BASE_DIR / "xslt" / "facture.xsl").read_text(encoding="utf-8")
        return Response(contenu, content_type="application/xml; charset=utf-8")

    def _reponse_creation(numero):
        return {
            "message": "Facture enregistrée.",
            "numero": numero,
            "liens": {
                "json": url_for("lire_facture_api", numero=numero),
                "xml": url_for("exporter_facture_xml", numero=numero),
                "html": url_for("afficher_facture_html", numero=numero),
            },
        }

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
