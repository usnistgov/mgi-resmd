<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rm="http://schema.nist.gov/xml/res-md/1.0wd-02-2017"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns="http://schema.nist.gov/xml/res-md/1.0wd-02-2017"
                exclude-result-prefixes="rm"
                version="1.0">
                
<!-- Stylesheet for converting mgi-resmd records from v12 of the mse_vocab to
     v170321 -->

   <xsl:output method="xml" encoding="UTF-8" indent="no" />
   <xsl:variable name="autoIndent" select="'  '"/>
   <xsl:preserve-space elements="*"/>

   <!--
     -  If true, insert carriage returns and indentation to produce a neatly 
     -  formatted output.  If false, any spacing between tags in the source
     -  document will be preserved.  
     -->
   <xsl:param name="prettyPrint" select="true()"/>

   <!--
     -  the per-level indentation.  Set this to a sequence of spaces when
     -  pretty printing is turned on.
     -->
   <xsl:param name="indent" select="'  '"/>

   <!--
     -  the maximum number of characters to allow in a single-line text
     -  element value
     -->
   <xsl:param name="maxtextlen" select="50"/>


   <xsl:variable name="cr"><xsl:text>
</xsl:text></xsl:variable>

   <!-- ==========================================================
     -  General templates
     -  ========================================================== -->

   <xsl:template match="/">
      <xsl:apply-templates select="*">
         <xsl:with-param name="sp">
            <xsl:if test="$prettyPrint">
              <xsl:value-of select="$cr"/>
            </xsl:if>
         </xsl:with-param>
         <xsl:with-param name="step">
            <xsl:if test="$prettyPrint">
              <xsl:value-of select="$indent"/>
            </xsl:if>
         </xsl:with-param>
      </xsl:apply-templates>
   </xsl:template>

   <xsl:template match="*[*]" priority="-0.5">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <xsl:element name="{name()}">
         <xsl:apply-templates select="@*" />

         <xsl:apply-templates select="*">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>

         <xsl:value-of select="$sp"/>
      </xsl:element>      
   </xsl:template>

   <xsl:template match="*[child::text() and not(*)]|*[not(child::node())]"
                 priority="-0.5">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:variable name="txt">
         <xsl:value-of select="child::node()"/>
      </xsl:variable>
      

      <xsl:value-of select="$sp"/>
      <xsl:element name="{name()}">
         <xsl:apply-templates select="@*" />

         <xsl:choose>
            <xsl:when test="true() or contains($txt, $cr) or @* or 
                            string-length($txt) &lt; $maxtextlen">
               <xsl:value-of select="$txt"/>
            </xsl:when>
            <xsl:otherwise>
               <xsl:value-of select="$subsp"/>
               <xsl:value-of select="$txt"/>
               <xsl:value-of select="$sp"/>
            </xsl:otherwise>
         </xsl:choose>
      </xsl:element>
   </xsl:template>

   <xsl:template match="@*">
      <xsl:attribute name="{name()}">
         <xsl:value-of select="."/>
      </xsl:attribute>
   </xsl:template>

   <xsl:template match="rm:applicability" priority="1">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>
      <xsl:param name="subsubsp" select="concat($subsp,$step)"/>

      <xsl:value-of select="$sp"/>
      <applicability xsl:exclude-result-prefixes="xsi">
         <xsl:if test="rm:experimentalMethod">

            <xsl:value-of select="$subsp"/>
            <dataOrigin>
               <xsl:value-of select="$subsubsp"/>
               <experiments>experiments</experiments>
               <xsl:value-of select="$subsp"/>
            </dataOrigin>
         </xsl:if>
         <xsl:if test="rm:computationalMethod">
            <xsl:value-of select="$subsp"/>
            <dataOrigin>
               <xsl:value-of select="$subsubsp"/>
               <simulations>simulations</simulations>
               <xsl:value-of select="$subsp"/>
            </dataOrigin>
         </xsl:if>

         <xsl:apply-templates select="rm:materialType">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>

         <xsl:apply-templates select="rm:structuralFeature">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>
         <xsl:apply-templates select="rm:propertyAddressed[rm:microstructural]"
                              mode="microstruct">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>

         <xsl:apply-templates select="rm:propertyAddressed">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>
         <xsl:if test="rm:propertyAddressed/rm:microstructural[
                                                           not(contains(.,':'))]">
            <xsl:value-of select="$sp"/>
            <propertyAddressed>
               <xsl:value-of select="$subsp"/>
               <structural>structural</structural>
               <xsl:value-of select="$sp"/>
            </propertyAddressed>
         </xsl:if>
         
         <xsl:apply-templates select="rm:experimentalMethod">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>
         <xsl:apply-templates select="rm:computationalMethod">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>
         <xsl:apply-templates select="rm:synthesisProcessing">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>

         <xsl:value-of select="$sp"/>
      </applicability>
   </xsl:template>

   <xsl:template match="rm:morphologies[contains(.,': 1D')]">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <morphologies>morphologies: one-dimensional</morphologies>
   </xsl:template>
   <xsl:template match="rm:morphologies[contains(.,': 2D')]">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <morphologies>morphologies: two-dimensional</morphologies>
   </xsl:template>
   <xsl:template match="rm:morphologies[contains(.,': nanoparticle / nanotube')]">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <morphologies>morphologies: nanoparticles or nanotubes</morphologies>
   </xsl:template>
   <xsl:template match="rm:morphologies[contains(.,': particles / colloids')]">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <morphologies>morphologies: particles or colloids</morphologies>
   </xsl:template>

   <xsl:template match="rm:chemical[contains(.,': molecular weights')]">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <chemical>chemical: molecular masses and distributions</chemical>
   </xsl:template>

   <xsl:template match="rm:electrical[contains(.,': dielectric constant')]">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <electrical>electrical: dielectric constant and spectra</electrical>
   </xsl:template>
   <xsl:template match="rm:mechanical[contains(.,': creep strength')]">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <mechanical>mechanical: creep</mechanical>
   </xsl:template>

   <xsl:template match="rm:Monte-Carlo_methods">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <Monte_Carlo_methods>Monte Carlo methods</Monte_Carlo_methods>
   </xsl:template>
   <xsl:template match="rm:reverse_Monte-Carlo">
      <xsl:param name="sp"/>
      <xsl:value-of select="$sp"/>
      <reverse_Monte_Carlo>reverse Monte Carlo</reverse_Monte_Carlo>
   </xsl:template>

   <xsl:template match="rm:experimentalMethod" priority="1">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <characterizationMethod>
         <xsl:apply-templates select="*">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>
         <xsl:value-of select="$sp"/>
      </characterizationMethod>
   </xsl:template>

   <xsl:template match="rm:propertyAddressed[rm:microstructural]">
   </xsl:template>

   <xsl:template match="rm:propertyAddressed[
                                   contains(rm:microstructural,': density')]"
                 priority="2">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <propertyAddressed>
          <xsl:value-of select="$subsp"/>
          <thermodynamic>thermodynamic: density</thermodynamic>
      </propertyAddressed>
   </xsl:template>

   <xsl:template match="rm:propertyAddressed[rm:microstructural]"
                 mode="microstruct">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <structuralFeature>
          <xsl:value-of select="$subsp"/>
          <microstructures>
             <xsl:text>microstructures: </xsl:text>
             <xsl:value-of select="substring-after(rm:microstructural[1],': ')"/>
          </microstructures>
      </structuralFeature>
   </xsl:template>

   <xsl:template match="rm:propertyAddressed[
                                   contains(rm:microstructural,': density')]"
                 mode="microstruct">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>
   </xsl:template>

   <xsl:template match="rm:Calphad">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <CALPHAD>CALPHAD</CALPHAD>
   </xsl:template>

   <xsl:template match="rm:publisher">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <publisher><xsl:value-of select="."/></publisher>
   </xsl:template>

   <xsl:template match="rm:Resource">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <Resource>
         <xsl:apply-templates select="@*" />

         <xsl:apply-templates select="*">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>

         <xsl:value-of select="$sp"/>
      </Resource>
   </xsl:template>

</xsl:stylesheet>
