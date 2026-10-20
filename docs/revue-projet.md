# Revue de projet — Ville refuge climatique

Groupe n°3 — La Clusaz. Support pour la revue du Rendu 4 : d'abord le besoin
de l'énoncé et ce qu'on y répond, puis où chaque technique du cours est mise
en œuvre, puis le déroulé de la démo.

## 1. Le besoin et notre réponse

| Énoncé | Dans le projet |
|---|---|
| Un territoire précis, piloté par une collectivité | La Clusaz ([choix-de-la-ville.md](choix-de-la-ville.md)) |
| Les fournisseurs décrivent leur logement | Formulaire, ou texte libre transformé en JSON par le LLM ILaaS |
| La plateforme affiche les propositions | Page `/logements`, fiche de chaque logement en HTML et en version imprimable |
| Mise en relation propriétaire / réfugié | Séjour rattaché à un logement et à un client, facture du séjour |
| Informations liées au statut de refuge climatique | Température moyenne l'été, altitude, exposition à la canicule, services, météo, activités à proximité |
| Le réfugié reçoit une facture | Facture XML du séjour, affichée en HTML et en texte imprimable |

## 2. Les techniques du cours dans le projet

| Cours | Où | Ce qu'on montre |
|---|---|---|
| JSON + JSON Schema | `schema/logement.schema.json`, `schema/facture.schema.json` | `required`, `enum`, `minimum`, `pattern`, `definitions` et `$ref` : la facture référence le schéma du logement |
| XML + DTD | `schema/facture.dtd`, `schema/base_de_donnees.dtd` | Éléments, attributs `ID`/`IDREF`, entité paramètre `%personne;`, DTD externe incluse par entité ; le XML généré déclare sa DTD (`<!DOCTYPE>`) |
| XSD | `schema/facture.xsd`, `schema/base_de_donnees.xsd` | Types nommés réutilisés (`personneType`, `adresseType`), énumérations, restriction (`montant` ≥ 0), `simpleContent`, `xs:include` |
| Validation par programme | `services/validation.py`, `services/documents.py`, `make verifier` | Validation JSON Schema à l'insertion ; validation DTD et XSD des exemples et du XML généré |
| XPath | README, export `/factures.xml` | Requêtes avec prédicats, axes (`ancestor::`), fonctions (`count`, `sum`) sur le fichier de toute la base |
| XSLT | `xslt/facture.xsl`, `xslt/facture-texte.xsl` | Une règle (`xsl:template`) par élément, enchaînées par `apply-templates` depuis la racine ; deux sorties différentes (`method="html"`, `method="text"`) pour le même XML ; appel de la feuille depuis le XML (`<?xml-stylesheet?>`) |
| Transformation du JSON par programme | `services/fiche_logement.py`, `pages/fiche_logement.html` | Comme recommandé en cours pour JSON : pas de XSLT, le programme parcourt l'objet et produit le HTML et le texte |
| RDFa | `pages/proprietaire.html`, `pages/fiche_logement.html` | `vocab`, `typeof`, `property` avec schema.org (`Person`, `PostalAddress`, `Accommodation`) |
| Liens entre documents | Toutes les pages | Facture → logement → propriétaire → ses logements ; JSON, XML, HTML et texte du même document reliés entre eux |
| Documents depuis la BDD / LLM | `database/`, `services/ilaas.py` | Même structure logique (le JSON) pour plusieurs présentations physiques ; texte libre structuré par un LLM |

## 3. Déroulé de la démo

1. `make populate COUNT=100` : base peuplée, `peuplement.sql` écrit.
2. `make verifier` : les exemples passent le JSON Schema, la DTD et le XSD.
3. **Formulaire** : bouton « Aléatoire », envoi, lecture du JSON produit et des liens vers les documents.
4. **Facture** : le XML (avec DTD et feuille de style), la version HTML, la version texte. Montrer que ce sont deux feuilles XSLT sur le même XML.
5. **Logement** : la fiche HTML et la fiche texte, produites par le programme à partir du JSON `/api/logements/<id>`.
6. **Propriétaire** : page RDFa, test avec le validateur schema.org, lien vers ses logements.
7. **XML global** : téléchargement, puis quelques requêtes XPath du README dans un testeur en ligne.
8. **Texte libre** (si la clé ILaaS est disponible).

## 4. Ce qui reste à faire

- Rendre le logement indépendant de la facture : aujourd'hui une facture crée
  son logement, son émetteur et son client. Il faut pouvoir publier un
  logement seul (formulaire, script, texte libre), puis créer un séjour, puis
  générer la facture à partir du séjour.
- Ne plus dupliquer les personnes à chaque facture.
- Ajouter la commission de la plateforme comme ligne de facture.
- Les tarifs sont encore ceux d'une location longue durée (loyer mensuel,
  dépôt, frais d'agence) ; un prix par nuit serait plus cohérent avec des
  séjours de quelques jours.
