const form = document.querySelector("#facture-form");
const preview = document.querySelector("#json-preview");
const resultat = document.querySelector("#resultat");

const numberValue = (data, name) => Number(data.get(name));

function construireFacture(data) {
    const reference = data.get("id_logement");
    const montants = {
        "Loyer mensuel": numberValue(data, "loyer_mensuel"),
        "Charges": numberValue(data, "charges"),
        "Dépôt de garantie": numberValue(data, "depot_garantie"),
        "Frais d'agence": numberValue(data, "frais_d_agence"),
    };
    const lignes = Object.entries(montants).map(([libelle, montant]) => ({
        "@refLogement": reference,
        libelle,
        montant,
    }));
    const totalBrut = lignes.reduce((somme, ligne) => somme + ligne.montant, 0);
    const total = Math.round((totalBrut + Number.EPSILON) * 100) / 100;

    return {
        facture: {
            "@numero": data.get("numero"),
            "@date": data.get("date"),
            emetteur: {
                nom: data.get("emetteur_nom"),
                adresse: {
                    rue: data.get("emetteur_rue"),
                    code_postal: data.get("emetteur_code_postal"),
                    ville: data.get("emetteur_ville"),
                },
                email: data.get("emetteur_email"),
            },
            client: {
                nom: data.get("client_nom"),
                prenom: data.get("client_prenom"),
                adresse: {
                    rue: data.get("client_rue"),
                    code_postal: data.get("client_code_postal"),
                    ville: data.get("client_ville"),
                },
                email: data.get("client_email"),
            },
            offre_logement: {
                description: data.get("description"),
                type_bien: data.get("type_bien"),
                logement: [{
                    "@idLogement": reference,
                    "@meuble": data.get("meuble"),
                    adresse: {
                        rue: data.get("logement_rue"),
                        code_postal: data.get("logement_code_postal"),
                        ville: data.get("logement_ville"),
                    },
                    loyer_mensuel: montants["Loyer mensuel"],
                    charges: montants.Charges,
                    depot_garantie: montants["Dépôt de garantie"],
                    frais_d_agence: montants["Frais d'agence"],
                }],
            },
            details_paiement: {
                ligne_facture: lignes,
            },
            total: {
                "@devise": "EUR",
                "#text": total,
            },
        },
    };
}

function afficherErreur(reponse) {
    resultat.className = "message error";
    resultat.replaceChildren();
    const titre = document.createElement("strong");
    titre.textContent = reponse.erreur || "Une erreur est survenue.";
    resultat.append(titre);

    if (reponse.details?.length) {
        const liste = document.createElement("ul");
        for (const detail of reponse.details) {
            const item = document.createElement("li");
            item.textContent = detail;
            liste.append(item);
        }
        resultat.append(liste);
    }
    resultat.hidden = false;
}

function afficherSucces(reponse) {
    resultat.className = "message success";
    resultat.replaceChildren();

    const texte = document.createElement("p");
    texte.textContent = `${reponse.message} Numéro : ${reponse.numero}`;
    resultat.append(texte);

    for (const [format, url] of Object.entries(reponse.liens)) {
        const lien = document.createElement("a");
        lien.href = url;
        lien.textContent = `Voir ${format.toUpperCase()}`;
        resultat.append(lien);
    }
    resultat.hidden = false;
}

form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const facture = construireFacture(new FormData(form));
    preview.textContent = JSON.stringify(facture, null, 2);
    preview.hidden = false;
    resultat.hidden = true;

    try {
        const response = await fetch("/api/factures", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(facture),
        });
        const reponse = await response.json();
        if (!response.ok) {
            afficherErreur(reponse);
            return;
        }
        afficherSucces(reponse);
    } catch (error) {
        afficherErreur({erreur: `Le serveur ne répond pas : ${error.message}`});
    }
});
