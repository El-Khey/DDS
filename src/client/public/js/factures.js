async function demanderSuppression(url, confirmation, bouton) {
    if (!window.confirm(confirmation)) {
        return;
    }

    bouton.disabled = true;

    try {
        const response = await fetch(url, {method: "DELETE"});
        const resultat = await response.json();

        if (!response.ok) {
            throw new Error(resultat.erreur || "La suppression a échoué.");
        }

        window.location.reload();
    } catch (error) {
        window.alert(error.message);
        bouton.disabled = false;
    }
}

for (const bouton of document.querySelectorAll(".delete-invoice")) {
    bouton.addEventListener("click", () => {
        demanderSuppression(
            bouton.dataset.url,
            `Supprimer définitivement la facture ${bouton.dataset.numero} ?`,
            bouton,
        );
    });
}

const supprimerTout = document.querySelector("#delete-all");
supprimerTout?.addEventListener("click", () => {
    demanderSuppression(
        "/api/factures",
        "Supprimer définitivement toutes les factures ?",
        supprimerTout,
    );
});
