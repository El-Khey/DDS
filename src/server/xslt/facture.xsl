<?xml version="1.0" encoding="UTF-8"?>
<!--
    Facture XML d'un séjour → page HTML.

    La règle racine "/" lance la règle "facture", qui enchaîne les autres
    règles avec xsl:apply-templates : une règle par élément de la facture.
-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    <xsl:strip-space elements="*"/>

    <!-- Montants au format français : 1 234,56 -->
    <xsl:decimal-format name="fr" decimal-separator="," grouping-separator=" "/>

    <xsl:template match="/">
        <xsl:apply-templates select="facture"/>
    </xsl:template>

    <xsl:template match="facture">
        <html lang="fr">
            <head>
                <meta charset="UTF-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1"/>
                <title>Facture <xsl:value-of select="@numero"/></title>
                <link rel="stylesheet" href="/public/css/facture.css"/>
            </head>
            <body>
                <nav class="invoice-actions" aria-label="Actions sur la facture">
                    <a class="action-link action-link-primary" href="/">← Retour aux factures</a>
                    <a class="action-link" href="/factures/{@numero}.txt">Version imprimable</a>
                    <a class="action-link" href="/factures/{@numero}.xml">Document XML</a>
                    <a class="action-link" href="/api/factures/{@numero}">Données JSON</a>
                </nav>

                <main class="invoice">
                    <header class="invoice-header">
                        <div>
                            <p class="invoice-kicker">Refuge climatique · facture de séjour</p>
                            <h1>Facture</h1>
                            <p class="invoice-number"><xsl:value-of select="@numero"/></p>
                        </div>
                        <div class="invoice-date">
                            <span>Date d'émission</span>
                            <strong><xsl:value-of select="@date"/></strong>
                        </div>
                    </header>

                    <section class="parties" aria-label="Émetteur et client">
                        <xsl:apply-templates select="emetteur | client"/>
                    </section>

                    <xsl:apply-templates select="sejour"/>
                    <xsl:apply-templates select="offre_logement"/>
                    <xsl:apply-templates select="details_paiement"/>
                </main>
            </body>
        </html>
    </xsl:template>

    <!-- Émetteur et client ont la même présentation -->
    <xsl:template match="emetteur | client">
        <article class="party-card">
            <p class="section-label">
                <xsl:choose>
                    <xsl:when test="self::emetteur">Émetteur · propriétaire</xsl:when>
                    <xsl:otherwise>Client · réfugié climatique</xsl:otherwise>
                </xsl:choose>
            </p>
            <h2>
                <xsl:value-of select="prenom"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="nom"/>
            </h2>
            <xsl:apply-templates select="adresse"/>
            <a href="mailto:{email}"><xsl:value-of select="email"/></a>
            <xsl:apply-templates select="tel"/>
        </article>
    </xsl:template>

    <xsl:template match="adresse">
        <address>
            <xsl:value-of select="rue"/><br/>
            <xsl:value-of select="code_postal"/>
            <xsl:text> </xsl:text>
            <xsl:value-of select="ville"/>
        </address>
    </xsl:template>

    <xsl:template match="tel">
        <p class="phone">
            <xsl:text>Tél. </xsl:text>
            <xsl:value-of select="@usage"/>
            <xsl:text> : </xsl:text>
            <xsl:value-of select="."/>
        </p>
    </xsl:template>

    <xsl:template match="sejour">
        <section class="invoice-section">
            <div class="section-heading">
                <div>
                    <p class="section-label">Séjour <xsl:value-of select="@idSejour"/></p>
                    <h2>Période d'hébergement</h2>
                </div>
                <xsl:apply-templates select="statut"/>
            </div>
            <dl class="facts">
                <div>
                    <dt>Arrivée</dt>
                    <dd><xsl:value-of select="date_debut"/></dd>
                </div>
                <div>
                    <dt>Départ</dt>
                    <dd><xsl:value-of select="date_fin"/></dd>
                </div>
                <div>
                    <dt>Montant du séjour</dt>
                    <dd>
                        <xsl:value-of select="format-number(montant_total, '# ##0,00', 'fr')"/>
                        <xsl:text> €</xsl:text>
                    </dd>
                </div>
            </dl>
        </section>
    </xsl:template>

    <xsl:template match="statut">
        <span class="type-badge">
            <xsl:choose>
                <xsl:when test=". = 'en_attente'">En attente</xsl:when>
                <xsl:when test=". = 'confirme'">Confirmé</xsl:when>
                <xsl:when test=". = 'annule'">Annulé</xsl:when>
                <xsl:when test=". = 'termine'">Terminé</xsl:when>
                <xsl:otherwise><xsl:value-of select="."/></xsl:otherwise>
            </xsl:choose>
        </span>
    </xsl:template>

    <xsl:template match="offre_logement">
        <section class="invoice-section">
            <p class="section-label">Bien concerné</p>
            <h2>Offre de logement</h2>
            <div class="housing-list">
                <xsl:apply-templates select="logement"/>
            </div>
        </section>
    </xsl:template>

    <xsl:template match="logement">
        <article class="housing-card">
            <div class="housing-main">
                <div>
                    <span class="type-badge"><xsl:value-of select="type_bien"/></span>
                    <xsl:if test="@meuble = 'oui'">
                        <span class="furnished">meublé</span>
                    </xsl:if>
                    <p class="housing-address">
                        <xsl:value-of select="adresse/rue"/>
                        <xsl:text>, </xsl:text>
                        <xsl:value-of select="adresse/code_postal"/>
                        <xsl:text> </xsl:text>
                        <xsl:value-of select="adresse/ville"/>
                    </p>
                    <p class="description"><xsl:value-of select="description"/></p>
                </div>
                <p class="housing-ref">
                    <xsl:text>Référence </xsl:text>
                    <a href="/logements/{@idLogement}.html"><xsl:value-of select="@idLogement"/></a>
                </p>
            </div>
            <xsl:apply-templates select="environnement_logement"/>
            <xsl:apply-templates select="activites_proximite"/>
        </article>
    </xsl:template>

    <xsl:template match="environnement_logement">
        <p class="subsection-label">Refuge climatique</p>
        <dl class="facts">
            <xsl:if test="temperature_moyenne_ete">
                <div>
                    <dt>Température moyenne l'été</dt>
                    <dd><xsl:value-of select="temperature_moyenne_ete"/> °C</dd>
                </div>
            </xsl:if>
            <xsl:if test="altitude">
                <div>
                    <dt>Altitude</dt>
                    <dd><xsl:value-of select="altitude"/> m</dd>
                </div>
            </xsl:if>
            <xsl:apply-templates select="indice_canicule"/>
        </dl>
        <xsl:if test="services_disponibles">
            <p class="note"><strong>Services : </strong><xsl:value-of select="services_disponibles"/></p>
        </xsl:if>
        <xsl:if test="informations_meteo">
            <p class="note"><strong>Météo : </strong><xsl:value-of select="informations_meteo"/></p>
        </xsl:if>
    </xsl:template>

    <xsl:template match="indice_canicule">
        <div>
            <dt>Exposition à la canicule</dt>
            <dd>
                <xsl:choose>
                    <xsl:when test=". = 'faible'">Faible</xsl:when>
                    <xsl:when test=". = 'modere'">Modérée</xsl:when>
                    <xsl:when test=". = 'eleve'">Élevée</xsl:when>
                    <xsl:otherwise><xsl:value-of select="."/></xsl:otherwise>
                </xsl:choose>
            </dd>
        </div>
    </xsl:template>

    <xsl:template match="activites_proximite">
        <p class="subsection-label">Activités à proximité</p>
        <ul class="activities">
            <xsl:apply-templates select="activite"/>
        </ul>
    </xsl:template>

    <xsl:template match="activite">
        <li>
            <strong><xsl:value-of select="nom"/></strong>
            <xsl:text> · </xsl:text>
            <xsl:value-of select="type_activite"/>
            <xsl:if test="distance_km">
                <xsl:text>, à </xsl:text>
                <xsl:value-of select="distance_km"/>
                <xsl:text> km</xsl:text>
            </xsl:if>
        </li>
    </xsl:template>

    <xsl:template match="details_paiement">
        <section class="invoice-section payment-section">
            <p class="section-label">Montants</p>
            <h2>Détails du paiement</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Libellé</th>
                            <th>Logement</th>
                            <th>Montant</th>
                        </tr>
                    </thead>
                    <tbody>
                        <xsl:apply-templates select="ligne_facture"/>
                    </tbody>
                </table>
            </div>
            <xsl:apply-templates select="../total"/>
        </section>
    </xsl:template>

    <xsl:template match="ligne_facture">
        <tr>
            <td><xsl:value-of select="libelle"/></td>
            <td><xsl:value-of select="@refLogement"/></td>
            <td class="amount">
                <xsl:value-of select="format-number(montant, '# ##0,00', 'fr')"/>
                <xsl:text> €</xsl:text>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="total">
        <div class="invoice-total">
            <span>Total</span>
            <strong>
                <xsl:value-of select="format-number(., '# ##0,00', 'fr')"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="@devise"/>
            </strong>
        </div>
    </xsl:template>
</xsl:stylesheet>
