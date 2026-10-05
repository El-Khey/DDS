<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>

    <xsl:template match="/facture">
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
                    <a class="action-link">
                        <xsl:attribute name="href">
                            <xsl:text>/api/factures/</xsl:text>
                            <xsl:value-of select="@numero"/>
                        </xsl:attribute>
                        Données JSON
                    </a>
                    <a class="action-link">
                        <xsl:attribute name="href">
                            <xsl:text>/factures/</xsl:text>
                            <xsl:value-of select="@numero"/>
                            <xsl:text>.xml</xsl:text>
                        </xsl:attribute>
                        Document XML
                    </a>
                </nav>

                <main class="invoice">
                    <header class="invoice-header">
                        <div>
                            <p class="invoice-kicker">Offre de logement</p>
                            <h1>Facture</h1>
                            <p class="invoice-number"><xsl:value-of select="@numero"/></p>
                        </div>
                        <div class="invoice-date">
                            <span>Date d'émission</span>
                            <strong><xsl:value-of select="@date"/></strong>
                        </div>
                    </header>

                    <section class="parties" aria-label="Émetteur et client">
                        <article class="party-card">
                            <p class="section-label">Émetteur</p>
                            <h2><xsl:value-of select="emetteur/nom"/></h2>
                            <address>
                                <xsl:value-of select="emetteur/adresse/rue"/><br/>
                                <xsl:value-of select="emetteur/adresse/code_postal"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="emetteur/adresse/ville"/>
                            </address>
                            <a>
                                <xsl:attribute name="href">
                                    <xsl:text>mailto:</xsl:text>
                                    <xsl:value-of select="emetteur/email"/>
                                </xsl:attribute>
                                <xsl:value-of select="emetteur/email"/>
                            </a>
                        </article>

                        <article class="party-card">
                            <p class="section-label">Client</p>
                            <h2>
                                <xsl:value-of select="client/prenom"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="client/nom"/>
                            </h2>
                            <address>
                                <xsl:value-of select="client/adresse/rue"/><br/>
                                <xsl:value-of select="client/adresse/code_postal"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="client/adresse/ville"/>
                            </address>
                            <a>
                                <xsl:attribute name="href">
                                    <xsl:text>mailto:</xsl:text>
                                    <xsl:value-of select="client/email"/>
                                </xsl:attribute>
                                <xsl:value-of select="client/email"/>
                            </a>
                        </article>
                    </section>

                    <section class="invoice-section">
                        <div class="section-heading">
                            <div>
                                <p class="section-label">Bien concerné</p>
                                <h2>Offre de logement</h2>
                            </div>
                            <span class="type-badge"><xsl:value-of select="offre_logement/type_bien"/></span>
                        </div>
                        <p class="description"><xsl:value-of select="offre_logement/description"/></p>

                        <div class="housing-list">
                            <xsl:for-each select="offre_logement/logement">
                                <article class="housing-card">
                                    <div>
                                        <strong>
                                            <xsl:value-of select="adresse/rue"/>,
                                            <xsl:text> </xsl:text>
                                            <xsl:value-of select="adresse/code_postal"/>
                                            <xsl:text> </xsl:text>
                                            <xsl:value-of select="adresse/ville"/>
                                        </strong>
                                        <p>Référence : <xsl:value-of select="@idLogement"/></p>
                                    </div>
                                    <span class="furnished">
                                        Meublé : <xsl:value-of select="@meuble"/>
                                    </span>
                                </article>
                            </xsl:for-each>
                        </div>
                    </section>

                    <section class="invoice-section payment-section">
                        <p class="section-label">Montants</p>
                        <h2>Détails du paiement</h2>
                        <div class="table-wrapper">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Libellé</th>
                                        <th>Montant</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <xsl:for-each select="details_paiement/ligne_facture">
                                        <tr>
                                            <td><xsl:value-of select="libelle"/></td>
                                            <td class="amount">
                                                <xsl:value-of select="format-number(number(montant), '0.00')"/>
                                                <xsl:text> €</xsl:text>
                                            </td>
                                        </tr>
                                    </xsl:for-each>
                                </tbody>
                            </table>
                        </div>

                        <div class="invoice-total">
                            <span>Total</span>
                            <strong>
                                <xsl:value-of select="format-number(number(total), '0.00')"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="total/@devise"/>
                            </strong>
                        </div>
                    </section>
                </main>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
