CREATE TABLE IF NOT EXISTS adresse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rue TEXT NOT NULL,
    code_postal TEXT NOT NULL,
    ville TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS emetteur (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_adresse INTEGER NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT NOT NULL,
    FOREIGN KEY (id_adresse) REFERENCES adresse(id)
);
CREATE TABLE IF NOT EXISTS client (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_adresse INTEGER NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT NOT NULL,
    FOREIGN KEY (id_adresse) REFERENCES adresse(id)
);
CREATE TABLE IF NOT EXISTS logement (
    id TEXT PRIMARY KEY,
    id_adresse INTEGER NOT NULL,
    type_bien TEXT NOT NULL,
    description TEXT NOT NULL,
    loyer_mensuel REAL NOT NULL CHECK (loyer_mensuel >= 0),
    charges REAL NOT NULL CHECK (charges >= 0),
    depot_garantie REAL NOT NULL CHECK (depot_garantie >= 0),
    frais_agence REAL NOT NULL DEFAULT 0 CHECK (frais_agence >= 0),
    meuble TEXT NOT NULL CHECK (meuble IN ('oui', 'non')),
    FOREIGN KEY (id_adresse) REFERENCES adresse(id)
);
CREATE TABLE IF NOT EXISTS sejour (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_client INTEGER NOT NULL,
    id_logement TEXT NOT NULL,
    date_debut TEXT NOT NULL,
    date_fin TEXT NOT NULL,
    statut TEXT NOT NULL CHECK (statut IN ('en_attente', 'confirme', 'annule', 'termine')),
    montant_total REAL NOT NULL CHECK (montant_total >= 0),
    FOREIGN KEY (id_client) REFERENCES client(id),
    FOREIGN KEY (id_logement) REFERENCES logement(id)
);
CREATE TABLE IF NOT EXISTS environnement_logement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_logement TEXT NOT NULL,
    temperature_moyenne_ete REAL,
    indice_canicule TEXT CHECK (indice_canicule IN ('faible', 'modere', 'eleve')),
    altitude INTEGER,
    services_disponibles TEXT,
    informations_meteo TEXT,
    FOREIGN KEY (id_logement) REFERENCES logement(id)
);
CREATE TABLE IF NOT EXISTS activite_proximite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_logement TEXT NOT NULL,
    nom TEXT NOT NULL,
    type_activite TEXT NOT NULL,
    distance_km REAL CHECK (distance_km >= 0),
    description TEXT,
    FOREIGN KEY (id_logement) REFERENCES logement(id)
);
CREATE TABLE IF NOT EXISTS facture (
    numero TEXT PRIMARY KEY,
    id_emetteur INTEGER NOT NULL,
    id_client INTEGER NOT NULL,
    id_sejour INTEGER,
    date_facture TEXT NOT NULL,
    FOREIGN KEY (id_emetteur) REFERENCES emetteur(id),
    FOREIGN KEY (id_client) REFERENCES client(id),
    FOREIGN KEY (id_sejour) REFERENCES sejour(id)
);
CREATE TABLE IF NOT EXISTS ligne_facture (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_facture TEXT NOT NULL,
    id_logement TEXT NOT NULL,
    libelle TEXT NOT NULL,
    montant REAL NOT NULL CHECK (montant >= 0),
    FOREIGN KEY (numero_facture) REFERENCES facture(numero),
    FOREIGN KEY (id_logement) REFERENCES logement(id)
);
CREATE TABLE IF NOT EXISTS tel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_emetteur INTEGER,
    id_client INTEGER,
    numero TEXT NOT NULL,
    usage_tel TEXT CHECK (usage_tel IN ('personnel', 'professionnel', 'mobile')),
    FOREIGN KEY (id_emetteur) REFERENCES emetteur(id),
    FOREIGN KEY (id_client) REFERENCES client(id),
    CHECK (
        (id_emetteur IS NOT NULL AND id_client IS NULL)
        OR (id_emetteur IS NULL AND id_client IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_ligne_facture_numero
    ON ligne_facture(numero_facture);
CREATE INDEX IF NOT EXISTS idx_ligne_facture_logement
    ON ligne_facture(id_logement);
CREATE INDEX IF NOT EXISTS idx_tel_emetteur
    ON tel(id_emetteur);
CREATE INDEX IF NOT EXISTS idx_tel_client
    ON tel(id_client);
CREATE INDEX IF NOT EXISTS idx_sejour_client
    ON sejour(id_client);
CREATE INDEX IF NOT EXISTS idx_sejour_logement
    ON sejour(id_logement);
CREATE INDEX IF NOT EXISTS idx_environnement_logement
    ON environnement_logement(id_logement);
CREATE INDEX IF NOT EXISTS idx_activite_logement
    ON activite_proximite(id_logement);
CREATE INDEX IF NOT EXISTS idx_facture_sejour
    ON facture(id_sejour);