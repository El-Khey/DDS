const form = document.querySelector("#facture-form");
const preview = document.querySelector("#json-preview");
const resultat = document.querySelector("#resultat");
const containerActivites = document.querySelector("#liste-activites");
const btnAjouterActivite = document.querySelector("#btn-ajouter-activite");

const numberValue = (data, name) => Number(data.get(name));

// Fonction pour ajouter un bloc d'activité dans le formulaire
function ajouterChampActivite(nom = "", type = "randonnee", distance = "", description = "") {
    const div = document.createElement("div");
    div.className = "activite-item";
    div.style.borderBottom = "1px solid #ccc";
    div.style.paddingBottom = "10px";
    div.style.marginBottom = "10px";

    div.innerHTML = `
        <label>Nom de l'activité</label>
        <input name="activite_nom[]" value="${nom}" placeholder="Ex: Baignade au lac" required>
        
        <label>Type d'activité</label>
        <select name="activite_type[]">
            <option value="randonnée" ${type === 'randonnée' ? 'selected' : ''}>Randonnée</option>
            <option value="baignade" ${type === 'baignade' ? 'selected' : ''}>Baignade</option>
            <option value="culture" ${type === 'culture' ? 'selected' : ''}>Culture</option>
            <option value="commerce" ${type === 'commerce' ? 'selected' : ''}>Commerce</option>
        </select>
        
        <label>Distance (km)</label>
        <input name="activite_distance[]" type="number" step="0.1" min="0" value="${distance}" placeholder="Ex: 2.5">
        
        <label>Description</label>
        <input name="activite_desc[]" value="${description}" placeholder="Petite description...">
        
        <button type="button" class="btn-supprimer-activite" style="margin-top: 5px;">Supprimer</button>
    `;

    div.querySelector(".btn-supprimer-activite").addEventListener("click", () => div.remove());
    containerActivites.appendChild(div);
}

// Ajouter une activité par défaut lors du chargement
ajouterChampActivite("Randonnée en forêt", "randonnée", "1.5", "Sentier ombragé très agréable.");

btnAjouterActivite?.addEventListener("click", () => ajouterChampActivite());

function extraireActivites(formElement) {
    const noms = formElement.querySelectorAll('input[name="activite_nom[]"]');
    const types = formElement.querySelectorAll('select[name="activite_type[]"]');
    const distances = formElement.querySelectorAll('input[name="activite_distance[]"]');
    const descs = formElement.querySelectorAll('input[name="activite_desc[]"]');

    const activites = [];
    noms.forEach((nomInput, index) => {
        if (nomInput.value.trim() !== "") {
            activites.push({
                nom: nomInput.value.trim(),
                type_activite: types[index].value,
                distance_km: Number(distances[index].value) || 0,
                description: descs[index].value.trim()
            });
        }
    });
    return activites;
}

function construireFacture(data) {
    const reference = data.get("id_logement");
    const montants = {
        "Loyer mensuel": numberValue(data, "loyer_mensuel"),
        "Charges": numberValue(data, "charges"),
        "Dépôt de garantie": numberValue(data, "depot_garantie"),
        "Frais d'agence": numberValue(data, "frais_agence"),
    };
    const lignes = Object.entries(montants).map(([libelle, montant]) => ({
        "@refLogement": reference,
        libelle,
        montant,
    }));
    const totalBrut = lignes.reduce((somme, ligne) => somme + ligne.montant, 0);
    const total = Math.round((totalBrut + Number.EPSILON) * 100) / 100;

    const logement = {
        "@idLogement": reference,
        "@meuble": data.get("meuble"),
        type_bien: data.get("type_bien"),
        description: data.get("description"),
        adresse: {
            rue: data.get("logement_rue"),
            code_postal: data.get("logement_code_postal"),
            ville: data.get("logement_ville"),
        },
        loyer_mensuel: montants["Loyer mensuel"],
        charges: montants["Charges"],
        depot_garantie: montants["Dépôt de garantie"],
        frais_agence: montants["Frais d'agence"],
        environnement_logement: {
            temperature_moyenne_ete: numberValue(data, "temperature_moyenne_ete"),
            indice_canicule: data.get("indice_canicule"),
            altitude: numberValue(data, "altitude"),
            services_disponibles: data.get("services_disponibles"),
            informations_meteo: data.get("informations_meteo"),
        },
    };
    const activites = extraireActivites(form);
    if (activites.length) {
        logement.activites_proximite = {activite: activites};
    }

    return {
        facture: {
            "@numero": data.get("numero"),
            "@date": data.get("date"),
            emetteur: {
                nom: data.get("emetteur_nom"),
                prenom: data.get("emetteur_prenom"),
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
            sejour: {
                "@idSejour": data.get("id_sejour"),
                date_debut: data.get("date_debut"),
                date_fin: data.get("date_fin"),
                statut: data.get("statut_sejour"),
                montant_total: total
            },
            offre_logement: {
                logement: [logement],
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

const btnAleatoire = document.querySelector("#btn-aleatoire");

function choixAleatoire(tableau) {
    return tableau[Math.floor(Math.random() * tableau.length)];
}

function email(prenom, nom) {
    const sansAccents = (texte) => texte.normalize("NFD").replace(/[^a-z]/gi, "");
    return `${sansAccents(prenom)}.${sansAccents(nom)}@gmail.com`.toLowerCase();
}

function dateDansNJours(nombreJours) {
    const date = new Date();
    date.setDate(date.getDate() + nombreJours);
    return date.toISOString().slice(0, 10);
}

btnAleatoire?.addEventListener("click", async () => {
    try {
        const response = await fetch("/api/population");
        if (!response.ok) throw new Error("Erreur de chargement des données");
        const donnees = await response.json();

        const villeEmetteur = choixAleatoire(donnees.villes);
        const villeClient = choixAleatoire(donnees.villes);
        const villeLogement = choixAleatoire(donnees.villes);
        const prenomE = choixAleatoire(donnees.prenoms);
        const nomE = choixAleatoire(donnees.noms);
        const prenomC = choixAleatoire(donnees.prenoms);
        const nomC = choixAleatoire(donnees.noms);
        const typeLogement = choixAleatoire(donnees.types_logement);

        // Émetteur
        document.querySelector("#emetteur_nom").value = nomE;
        document.querySelector("#emetteur_prenom").value = prenomE;
        document.querySelector("#emetteur_email").value = email(prenomE, nomE);
        document.querySelector("#emetteur_rue").value = `${Math.floor(Math.random() * 100) + 1} ${choixAleatoire(donnees.voies)}`;
        document.querySelector("#emetteur_code_postal").value = villeEmetteur.code_postal;
        document.querySelector("#emetteur_ville").value = villeEmetteur.nom;

        // Client
        document.querySelector("#client_nom").value = nomC;
        document.querySelector("#client_prenom").value = prenomC;
        document.querySelector("#client_email").value = email(prenomC, nomC);
        document.querySelector("#client_rue").value = `${Math.floor(Math.random() * 100) + 1} ${choixAleatoire(donnees.voies)}`;
        document.querySelector("#client_code_postal").value = villeClient.code_postal;
        document.querySelector("#client_ville").value = villeClient.nom;

        // Séjour
        document.querySelector("#date_debut").value = dateDansNJours(0);
        document.querySelector("#date_fin").value = dateDansNJours(Math.floor(Math.random() * 10) + 2);

        // Logement
        document.querySelector("#type_bien").value = typeLogement.nom;
        document.querySelector("#description").value = choixAleatoire(typeLogement.descriptions);
        document.querySelector("#logement_rue").value = `${Math.floor(Math.random() * 100) + 1} ${choixAleatoire(donnees.voies)}`;
        document.querySelector("#logement_code_postal").value = villeLogement.code_postal;
        document.querySelector("#logement_ville").value = villeLogement.nom;
        document.querySelector("#loyer_mensuel").value = Math.floor(Math.random() * 900) + 300;
        document.querySelector("#charges").value = Math.floor(Math.random() * 100);
        document.querySelector("#depot_garantie").value = Math.floor(Math.random() * 1000) + 300;
        document.querySelector("#frais_agence").value = Math.random() > 0.5 ? 150 : 0;

        // Environnement & Refuge climatique
        if (donnees.indices_canicule) {
            document.querySelector("#temperature_moyenne_ete").value = (Math.random() * 5 + 19).toFixed(1);
            document.querySelector("#altitude").value = Math.floor(Math.random() * 1500) + 400;
            document.querySelector("#indice_canicule").value = choixAleatoire(donnees.indices_canicule);
            document.querySelector("#services_disponibles").value = choixAleatoire(donnees.services_disponibles);
            document.querySelector("#informations_meteo").value = choixAleatoire(donnees.informations_meteo);
        }

    } catch (error) {
        console.error("Erreur aléatoire :", error);
        alert("Impossible de charger les données aléatoires.");
    }
});