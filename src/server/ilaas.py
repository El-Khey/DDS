import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent


class IlaasNonConfigure(Exception):
    pass


class ErreurIlaas(Exception):
    pass


def _retirer_bloc_markdown(texte):
    texte = texte.strip()

    if texte.startswith("```"):
        lignes = texte.splitlines()
        lignes = lignes[1:]

        if lignes and lignes[-1].strip() == "```":
            lignes = lignes[:-1]

        texte = "\n".join(lignes)

    return texte.strip()


def description_vers_facture(description):
    cle_api = os.getenv("ILAAS_API_KEY")
    modele = "mistral-small-4-119b" 
    url_base = os.getenv(
        "ILAAS_API_URL",
        "https://llm.ilaas.fr/v1"
    )

    if not cle_api:
        raise IlaasNonConfigure(
            "Définissez ILAAS_API_KEY avant d'utiliser cette fonction."
        )

    schema = (
        BASE_DIR / "schema" / "facture.schema.json"
    ).read_text(encoding="utf-8")

    exemple = (
        BASE_DIR / "examples" / "facture.json"
    ).read_text(encoding="utf-8")

    consigne = f"""
Transforme la description suivante en facture JSON.

Retourne uniquement un objet JSON,
sans texte ni bloc Markdown.

Le résultat doit respecter exactement ce JSON Schema :

{schema}

Voici un exemple de forme attendue :

{exemple}

Description de l'utilisateur :

{description}
""".strip()

    corps = json.dumps(
        {
            "model": modele,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu extrais des données structurées "
                        "sans ajouter de commentaire."
                    ),
                },
                {
                    "role": "user",
                    "content": consigne,
                },
            ],
            "temperature": 0,
            "stream": False,
        }
    ).encode("utf-8")

    requete = Request(
        f"{url_base.rstrip('/')}/chat/completions",
        data=corps,
        headers={
            "Authorization": f"Bearer {cle_api}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(requete, timeout=60) as reponse:
            resultat = json.loads(
                reponse.read().decode("utf-8")
            )

        contenu = resultat["choices"][0]["message"]["content"]

        return json.loads(
            _retirer_bloc_markdown(contenu)
        )

    except HTTPError as erreur:
        corps_erreur = erreur.read().decode(
            "utf-8",
            errors="replace"
        )

        raise ErreurIlaas(
            f"Erreur HTTP ILaaS {erreur.code} : "
            f"{corps_erreur}"
        ) from erreur

    except (
        URLError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ) as erreur:

        raise ErreurIlaas(
            f"Réponse ILaaS inutilisable : {erreur}"
        ) from erreur