<?xml version="1.0" encoding="UTF-8"?>
<!--
    Facture XML d'un séjour → version imprimable en texte brut.

    Même organisation que facture.xsl (une règle par élément), mais la sortie
    est du texte : chaque règle écrit des lignes de 60 caractères.
-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="text" encoding="UTF-8"/>
    <xsl:strip-space elements="*"/>

    <xsl:decimal-format name="fr" decimal-separator="," grouping-separator=" "/>

    <xsl:variable name="saut" select="'&#10;'"/>
    <xsl:variable name="double" select="'============================================================'"/>
    <xsl:variable name="simple" select="'------------------------------------------------------------'"/>
    <xsl:variable name="blancs" select="'                                                            '"/>

    <xsl:template match="/">
        <xsl:apply-templates select="facture"/>
    </xsl:template>

    <xsl:template match="facture">
        <xsl:value-of select="concat($double, $saut)"/>
        <xsl:text>              FACTURE DE SÉJOUR - REFUGE CLIMATIQUE&#10;</xsl:text>
        <xsl:value-of select="concat($double, $saut)"/>
        <xsl:value-of select="concat('Numéro : ', @numero, $saut)"/>
        <xsl:value-of select="concat('Date   : ', @date, $saut, $saut)"/>

        <xsl:apply-templates select="emetteur | client"/>
        <xsl:apply-templates select="sejour"/>
        <xsl:apply-templates select="offre_logement/logement"/>
        <xsl:apply-templates select="details_paiement"/>
        <xsl:apply-templates select="total"/>
        <xsl:value-of select="concat($double, $saut)"/>
    </xsl:template>

    <xsl:template match="emetteur | client">
        <xsl:choose>
            <xsl:when test="self::emetteur">ÉMETTEUR (propriétaire)</xsl:when>
            <xsl:otherwise>CLIENT (réfugié climatique)</xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="concat($saut, '  ', prenom, ' ', nom, $saut)"/>
        <xsl:apply-templates select="adresse"/>
        <xsl:value-of select="concat('  ', email, $saut)"/>
        <xsl:apply-templates select="tel"/>
        <xsl:value-of select="$saut"/>
    </xsl:template>

    <xsl:template match="adresse">
        <xsl:value-of select="concat('  ', rue, $saut)"/>
        <xsl:value-of select="concat('  ', code_postal, ' ', ville, $saut)"/>
    </xsl:template>

    <xsl:template match="tel">
        <xsl:value-of select="concat('  Tél. ', @usage, ' : ', ., $saut)"/>
    </xsl:template>

    <xsl:template match="sejour">
        <xsl:value-of select="concat('SÉJOUR ', @idSejour, ' (')"/>
        <xsl:apply-templates select="statut"/>
        <xsl:value-of select="concat(')', $saut)"/>
        <xsl:value-of select="concat('  Du ', date_debut, ' au ', date_fin, $saut, $saut)"/>
    </xsl:template>

    <xsl:template match="statut">
        <xsl:choose>
            <xsl:when test=". = 'en_attente'">en attente</xsl:when>
            <xsl:when test=". = 'confirme'">confirmé</xsl:when>
            <xsl:when test=". = 'annule'">annulé</xsl:when>
            <xsl:when test=". = 'termine'">terminé</xsl:when>
            <xsl:otherwise><xsl:value-of select="."/></xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="logement">
        <xsl:value-of select="concat('LOGEMENT ', @idLogement, ' - ', type_bien)"/>
        <xsl:if test="@meuble = 'oui'"> meublé</xsl:if>
        <xsl:value-of select="$saut"/>
        <xsl:value-of select="concat('  ', adresse/rue, ', ', adresse/code_postal, ' ', adresse/ville, $saut)"/>
        <xsl:value-of select="concat('  ', description, $saut)"/>
        <xsl:apply-templates select="environnement_logement"/>
        <xsl:apply-templates select="activites_proximite"/>
        <xsl:value-of select="$saut"/>
    </xsl:template>

    <xsl:template match="environnement_logement">
        <xsl:value-of select="concat('  Refuge climatique :', $saut)"/>
        <xsl:if test="temperature_moyenne_ete">
            <xsl:value-of select="concat('    - ', temperature_moyenne_ete, ' °C en moyenne')"/>
            <xsl:text> l'été&#10;</xsl:text>
        </xsl:if>
        <xsl:if test="altitude">
            <xsl:value-of select="concat('    - altitude ', altitude, ' m', $saut)"/>
        </xsl:if>
        <xsl:apply-templates select="indice_canicule"/>
    </xsl:template>

    <xsl:template match="indice_canicule">
        <xsl:text>    - exposition à la canicule </xsl:text>
        <xsl:choose>
            <xsl:when test=". = 'faible'">faible</xsl:when>
            <xsl:when test=". = 'modere'">modérée</xsl:when>
            <xsl:when test=". = 'eleve'">élevée</xsl:when>
            <xsl:otherwise><xsl:value-of select="."/></xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="$saut"/>
    </xsl:template>

    <xsl:template match="activites_proximite">
        <xsl:value-of select="concat('  Activités à proximité :', $saut)"/>
        <xsl:apply-templates select="activite"/>
    </xsl:template>

    <xsl:template match="activite">
        <xsl:value-of select="concat('    - ', nom, ' (', type_activite)"/>
        <xsl:if test="distance_km">
            <xsl:value-of select="concat(', ', distance_km, ' km')"/>
        </xsl:if>
        <xsl:value-of select="concat(')', $saut)"/>
    </xsl:template>

    <xsl:template match="details_paiement">
        <xsl:value-of select="concat($simple, $saut)"/>
        <xsl:call-template name="ligne-montant">
            <xsl:with-param name="libelle" select="'Libellé'"/>
            <xsl:with-param name="montant" select="'Montant'"/>
        </xsl:call-template>
        <xsl:value-of select="concat($simple, $saut)"/>
        <xsl:apply-templates select="ligne_facture"/>
        <xsl:value-of select="concat($simple, $saut)"/>
    </xsl:template>

    <xsl:template match="ligne_facture">
        <xsl:call-template name="ligne-montant">
            <xsl:with-param name="libelle" select="concat(libelle, ' (', @refLogement, ')')"/>
            <xsl:with-param name="montant" select="concat(format-number(montant, '# ##0,00', 'fr'), ' €')"/>
        </xsl:call-template>
    </xsl:template>

    <xsl:template match="total">
        <xsl:call-template name="ligne-montant">
            <xsl:with-param name="libelle" select="'TOTAL'"/>
            <xsl:with-param name="montant" select="concat(format-number(., '# ##0,00', 'fr'), ' ', @devise)"/>
        </xsl:call-template>
    </xsl:template>

    <!-- Libellé à gauche sur 44 caractères, montant aligné à droite sur 16 -->
    <xsl:template name="ligne-montant">
        <xsl:param name="libelle"/>
        <xsl:param name="montant"/>
        <xsl:value-of select="substring(concat($libelle, $blancs), 1, 44)"/>
        <xsl:value-of select="substring($blancs, 1, 16 - string-length($montant))"/>
        <xsl:value-of select="concat($montant, $saut)"/>
    </xsl:template>
</xsl:stylesheet>
