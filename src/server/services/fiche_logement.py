"""Présentation d'un logement à partir de son JSON.

Contrairement à la facture XML, transformée par XSLT, le JSON est parcouru
directement par le programme : la page HTML est produite par un gabarit
Jinja et la version imprimable par ce module.
"""
import textwrap

from flask import render_template


LARGEUR = 60

INDICES_CANICULE = {"faible": "faible", "modere": "modérée", "eleve": "élevée"}


def logement_vers_html(payload):
    return render_template("fiche_logement.html", logement=payload["logement"])


def logement_vers_texte(payload):
    logement = payload["logement"]
    adresse = logement["adresse"]
    meuble = "meublé" if logement.get("@meuble") == "oui" else "non meublé"

    lignes = [
        "=" * LARGEUR,
        f"LOGEMENT {logement['@idLogement']}".center(LARGEUR),
        "Refuge climatique".center(LARGEUR),
        "=" * LARGEUR,
        "",
        _champ("Type de bien", f"{logement['type_bien']} ({meuble})"),
        _champ("Adresse", _adresse(adresse)),
        "",
        textwrap.fill(logement["description"], LARGEUR),
        "",
        *_bloc("TARIFS", [
            _champ("Loyer mensuel", _montant(logement["loyer_mensuel"])),
            _champ("Charges", _montant(logement["charges"])),
            _champ("Dépôt de garantie", _montant(logement["depot_garantie"])),
            _champ("Frais d'agence", _montant(logement["frais_agence"])),
        ]),
    ]

    environnement = logement.get("environnement_logement")
    if environnement:
        lignes += _bloc("ENVIRONNEMENT", _lignes_environnement(environnement))

    activites = logement.get("activites_proximite", {}).get("activite", [])
    if activites:
        lignes += _bloc("ACTIVITÉS À PROXIMITÉ", [
            _champ(activite["nom"], _distance(activite)) for activite in activites
        ])

    proprietaire = logement.get("proprietaire")
    if proprietaire:
        lignes += _bloc("PROPRIÉTAIRE", _lignes_proprietaire(proprietaire))

    lignes.append("=" * LARGEUR)
    return "\n".join(lignes) + "\n"


def _bloc(titre, contenu):
    return [titre, "-" * LARGEUR, *contenu, ""]


def _champ(libelle, valeur):
    return f"{libelle:<24}{valeur}"


def _adresse(adresse):
    return f"{adresse['rue']}, {adresse['code_postal']} {adresse['ville']}"


def _montant(valeur):
    return f"{valeur:,.2f} EUR".replace(",", " ").replace(".", ",")


def _distance(activite):
    texte = activite["type_activite"]
    if activite.get("distance_km") is not None:
        texte += f", à {activite['distance_km']} km"
    return texte


def _lignes_environnement(environnement):
    lignes = []
    if environnement.get("temperature_moyenne_ete") is not None:
        lignes.append(_champ("Température l'été", f"{environnement['temperature_moyenne_ete']} °C"))
    if environnement.get("altitude") is not None:
        lignes.append(_champ("Altitude", f"{environnement['altitude']} m"))
    if environnement.get("indice_canicule"):
        indice = INDICES_CANICULE.get(environnement["indice_canicule"], environnement["indice_canicule"])
        lignes.append(_champ("Exposition canicule", indice))
    for cle, libelle in (
        ("services_disponibles", "Services"),
        ("informations_meteo", "Météo"),
    ):
        if environnement.get(cle):
            lignes.append(textwrap.fill(f"{libelle} : {environnement[cle]}", LARGEUR))
    return lignes


def _lignes_proprietaire(proprietaire):
    lignes = [
        f"{proprietaire['prenom']} {proprietaire['nom']}",
        _adresse(proprietaire["adresse"]),
        proprietaire["email"],
    ]
    for telephone in proprietaire.get("tel", []):
        usage = telephone.get("@usage", "")
        lignes.append(f"Tél. {usage} : {telephone['#text']}".replace("  ", " "))
    return lignes
