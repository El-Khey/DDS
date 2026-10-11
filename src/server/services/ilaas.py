import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SERVER_DIR = Path(__file__).resolve().parents[1]


class IlaasNonConfigure(Exception):
    pass


class ErreurIlaas(Exception):
    pass


def _retirer_bloc_markdown(texte):
    texte = texte.strip()
    if not texte.startswith("```"):
        return texte

    lignes = texte.splitlines()[1:]
    if lignes and lignes[-1].strip() == "```":
        lignes.pop()
    return "\n".join(lignes).strip()


def _creer_consigne(description):
    schema = (SERVER_DIR / "schema" / "facture.schema.json").read_text(
        encoding="utf-8"
    )
    exemple = (SERVER_DIR / "examples" / "facture.json").read_text(
        encoding="utf-8"
    )
    return f"""
Transforme la description suivante en facture JSON.

Retourne uniquement un objet JSON, sans texte ni bloc Markdown.

Le résultat doit respecter exactement ce JSON Schema :

{schema}

Voici un exemple de forme attendue :

{exemple}

Description de l'utilisateur :

{description}
""".strip()


def description_vers_facture(description):
    cle_api = os.getenv("ILAAS_API_KEY")
    if not cle_api:
        raise IlaasNonConfigure(
            "Définissez ILAAS_API_KEY avant d'utiliser cette fonction."
        )

    url_base = os.getenv("ILAAS_API_URL", "https://llm.ilaas.fr/v1")
    corps = json.dumps(
        {
            "model": "mistral-small-4-119b",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu extrais des données structurées "
                        "sans ajouter de commentaire."
                    ),
                },
                {"role": "user", "content": _creer_consigne(description)},
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
            resultat = json.loads(reponse.read().decode("utf-8"))
        contenu = resultat["choices"][0]["message"]["content"]
        return json.loads(_retirer_bloc_markdown(contenu))
    except HTTPError as erreur:
        corps_erreur = erreur.read().decode("utf-8", errors="replace")
        raise ErreurIlaas(
            f"Erreur HTTP ILaaS {erreur.code} : {corps_erreur}"
        ) from erreur
    except (URLError, KeyError, IndexError, json.JSONDecodeError) as erreur:
        raise ErreurIlaas(f"Réponse ILaaS inutilisable : {erreur}") from erreur
