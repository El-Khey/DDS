"""Lecture des émetteurs et des clients."""


def lire_personne(db, table, identifiant):
    """Retourne une personne de la table `emetteur` ou `client`
    sous la forme utilisée dans les documents JSON et XML."""
    personne = db.execute(
        f"""
        SELECT
            {table}.nom,
            {table}.prenom,
            {table}.email,
            adresse.rue,
            adresse.code_postal,
            adresse.ville
        FROM {table}
        JOIN adresse ON adresse.id = {table}.id_adresse
        WHERE {table}.id = ?
        """,
        (identifiant,),
    ).fetchone()

    if personne is None:
        return None

    telephones = db.execute(
        f"SELECT numero, usage_tel FROM tel WHERE id_{table} = ? ORDER BY id",
        (identifiant,),
    ).fetchall()

    resultat = {
        "nom": personne["nom"],
        "prenom": personne["prenom"],
        "adresse": {
            "rue": personne["rue"],
            "code_postal": personne["code_postal"],
            "ville": personne["ville"],
        },
        "email": personne["email"],
    }
    if telephones:
        resultat["tel"] = [
            {
                **({"@usage": telephone["usage_tel"]} if telephone["usage_tel"] else {}),
                "#text": telephone["numero"],
            }
            for telephone in telephones
        ]
    return resultat
