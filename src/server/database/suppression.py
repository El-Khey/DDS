def _supprimer_adresse_si_inutilisee(db, identifiant):
    db.execute(
        """
        DELETE FROM adresse
        WHERE id = ?
          AND NOT EXISTS (SELECT 1 FROM emetteur WHERE id_adresse = adresse.id)
          AND NOT EXISTS (SELECT 1 FROM client WHERE id_adresse = adresse.id)
          AND NOT EXISTS (SELECT 1 FROM logement WHERE id_adresse = adresse.id)
        """,
        (identifiant,),
    )


def _supprimer_personne_si_inutilisee(db, table, identifiant, id_adresse):
    if db.execute(
        f"SELECT 1 FROM facture WHERE id_{table} = ?",
        (identifiant,),
    ).fetchone():
        return

    db.execute(f"DELETE FROM tel WHERE id_{table} = ?", (identifiant,))
    db.execute(f"DELETE FROM {table} WHERE id = ?", (identifiant,))
    _supprimer_adresse_si_inutilisee(db, id_adresse)


def supprimer_facture(db, numero):
    facture = db.execute(
        """
        SELECT
            facture.id_emetteur,
            facture.id_client,
            emetteur.id_adresse AS adresse_emetteur,
            client.id_adresse AS adresse_client
        FROM facture
        JOIN emetteur ON emetteur.id = facture.id_emetteur
        JOIN client ON client.id = facture.id_client
        WHERE facture.numero = ?
        """,
        (numero,),
    ).fetchone()
    if facture is None:
        return False

    logements = db.execute(
        """
        SELECT DISTINCT logement.id, logement.id_adresse
        FROM logement
        JOIN ligne_facture ON ligne_facture.id_logement = logement.id
        WHERE ligne_facture.numero_facture = ?
        """,
        (numero,),
    ).fetchall()

    with db:
        db.execute("DELETE FROM ligne_facture WHERE numero_facture = ?", (numero,))
        db.execute("DELETE FROM facture WHERE numero = ?", (numero,))

        for logement in logements:
            suppression = db.execute(
                """
                DELETE FROM logement
                WHERE id = ?
                  AND NOT EXISTS (
                      SELECT 1 FROM ligne_facture WHERE id_logement = logement.id
                  )
                """,
                (logement["id"],),
            )
            if suppression.rowcount:
                _supprimer_adresse_si_inutilisee(db, logement["id_adresse"])

        _supprimer_personne_si_inutilisee(
            db,
            "emetteur",
            facture["id_emetteur"],
            facture["adresse_emetteur"],
        )
        _supprimer_personne_si_inutilisee(
            db,
            "client",
            facture["id_client"],
            facture["adresse_client"],
        )

    return True


def supprimer_toutes_factures(db):
    nombre = db.execute("SELECT COUNT(*) FROM facture").fetchone()[0]
    with db:
        for table in (
            "tel",
            "ligne_facture",
            "facture",
            "logement",
            "client",
            "emetteur",
            "adresse",
        ):
            db.execute(f"DELETE FROM {table}")
        db.execute("DELETE FROM sqlite_sequence")
    return nombre
