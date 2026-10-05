const form = document.querySelector("#texte-form");
const preview = document.querySelector("#llm-preview");
const resultat = document.querySelector("#llm-resultat");

form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const requete = {description: data.get("description_libre")};

    preview.textContent = JSON.stringify(requete, null, 2);
    preview.hidden = false;
    resultat.hidden = true;

    try {
        const response = await fetch("/api/factures/depuis-texte", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(requete),
        });
        const reponse = await response.json();
        resultat.replaceChildren();

        const message = document.createElement("p");
        message.textContent = response.ok
            ? `${reponse.message} Numéro : ${reponse.numero}`
            : reponse.erreur;
        resultat.append(message);

        if (reponse.details?.length) {
            const liste = document.createElement("ul");
            for (const detail of reponse.details) {
                const item = document.createElement("li");
                item.textContent = detail;
                liste.append(item);
            }
            resultat.append(liste);
        }

        if (response.ok) {
            for (const [format, url] of Object.entries(reponse.liens)) {
                const lien = document.createElement("a");
                lien.href = url;
                lien.textContent = `Voir ${format.toUpperCase()}`;
                resultat.append(lien);
            }
            preview.textContent = JSON.stringify(reponse.json_genere, null, 2);
        }

        resultat.className = response.ok ? "message success" : "message error";
        resultat.hidden = false;
    } catch (error) {
        resultat.textContent = `Le serveur ne répond pas : ${error.message}`;
        resultat.className = "message error";
        resultat.hidden = false;
    }
});
