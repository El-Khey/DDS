from flask import abort, jsonify, request, url_for

from src.server.database.connexion import get_db
from src.server.database.factures import lire_facture
from src.server.database.insertion import FactureExisteDeja, inserer_facture
from src.server.database.suppression import (
    supprimer_facture,
    supprimer_toutes_factures,
)
from src.server.services.ilaas import (
    ErreurIlaas,
    IlaasNonConfigure,
    description_vers_facture,
)
from src.server.services.validation import FactureInvalide


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


def enregistrer_routes_api(app):
    @app.post("/api/factures")
    def creer_facture_api():
        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify(
                erreur="Le corps de la requête doit être un objet JSON."
            ), 400

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

    @app.delete("/api/factures/<string:numero>")
    def supprimer_facture_api(numero):
        if not supprimer_facture(get_db(), numero):
            return jsonify(erreur="Cette facture n'existe pas."), 404
        return jsonify(message="Facture supprimée.", numero=numero)

    @app.delete("/api/factures")
    def supprimer_toutes_factures_api():
        nombre = supprimer_toutes_factures(get_db())
        return jsonify(message=f"{nombre} facture(s) supprimée(s).", nombre=nombre)
