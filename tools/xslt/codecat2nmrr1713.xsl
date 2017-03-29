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
         <xsl:call-template name="approachMethods">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
         </xsl:call-template>
         
         <xsl:apply-templates select="../rm:role/rm:software/rm:scale">
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

   <xsl:template match="rm:scale[.='None given']"/>

   <xsl:template match="rm:scale">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <computeScale>
         <xsl:value-of select="$subsp"/>
         <xsl:apply-templates select="." mode="term"/>
         <xsl:value-of select="$sp"/>
      </computeScale>
   </xsl:template>
   <xsl:template match="rm:scale[contains(.,'Electronic')]" mode="term">
      <electronic>electronic</electronic>
   </xsl:template>
   <xsl:template match="rm:scale[contains(.,'Atomic')]" mode="term">
      <nanoscale>atomic scale (nanoscale)</nanoscale>
   </xsl:template>
   <xsl:template match="rm:scale[contains(.,'Microscale')]" mode="term">
      <microscale>microscale</microscale>
   </xsl:template>
   <xsl:template match="rm:scale[contains(.,'Mesoscale')]" mode="term">
      <mesoscale>mesoscale</mesoscale>
   </xsl:template>
   <xsl:template match="rm:scale[contains(.,'Macroscale')]" mode="term">
      <macroscale>macroscale</macroscale>
   </xsl:template>
   <xsl:template match="rm:scale[contains(.,'Structural')]" mode="term">
      <structural>structural</structural>
   </xsl:template>
   <xsl:template match="rm:scale[contains(.,'Multiscale')]" mode="term">
      <multiscale>multiscale</multiscale>
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

<!--  ++++++++++++++++++++++++++++++++ -->

   <xsl:template match="rm:software">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:apply-templates select="rm:codeLanguage">
         <xsl:with-param name="sp" select="$sp"/>
         <xsl:with-param name="step" select="$step"/>
      </xsl:apply-templates>

      <xsl:for-each select="rm:opSystemName">
         <xsl:variable name="pos" select="position()"/>
         
         <xsl:value-of select="$sp"/>
         <supportedSystem>
           <xsl:value-of select="$subsp"/>
           <osName><xsl:value-of select="."/></osName>
           <xsl:if test="../rm:opSystemVersion[position()=$pos]">
              <xsl:value-of select="$subsp"/>
              <osVersion>
              <xsl:value-of select="../rm:opSystemVersion[position()=$pos]"/>
              </osVersion>
           </xsl:if>
           <xsl:value-of select="$sp"/>
         </supportedSystem>
      </xsl:for-each>

      <xsl:if test="string-length(normalize-space(
                       //rm:access/rm:policy/rm:termsURL)) &gt; 0 and 
                    not(starts-with(normalize-space(
                       //rm:access/rm:policy/rm:termsURL), 'http'))">
         <xsl:value-of select="$sp"/>
         <licenseName>
            <xsl:choose>
              <xsl:when test="contains(//rm:access/rm:policy/rm:termsURL,'http://') or 
                              contains(//rm:access/rm:policy/rm:termsURL,'https://')">
                <xsl:value-of select="substring-before(//rm:access/rm:policy/rm:termsURL,'http')"/>
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="//rm:access/rm:policy/rm:termsURL"/>
              </xsl:otherwise>
            </xsl:choose>
         </licenseName>
      </xsl:if>

      <xsl:apply-templates select="rm:approach[not(contains(.,'None'))]">
         <xsl:with-param name="sp" select="$sp"/>
         <xsl:with-param name="step" select="$step"/>
      </xsl:apply-templates>
      <xsl:apply-templates select="rm:methodAlgorithm">
         <xsl:with-param name="sp" select="$sp"/>
         <xsl:with-param name="step" select="$step"/>
      </xsl:apply-templates>

      <xsl:apply-templates select="rm:documentation">
         <xsl:with-param name="sp" select="$sp"/>
         <xsl:with-param name="step" select="$step"/>
      </xsl:apply-templates>
      <xsl:for-each select="rm:implementation[@href] | rm:inputsOutputs[@href]">
         <xsl:value-of select="$sp"/>
         <documentation>
            <xsl:value-of select="$subsp"/>
            <url><xsl:value-of select="@href"/></url>
            <xsl:value-of select="$subsp"/>
            <caption>
              <xsl:choose>
                <xsl:when test="string-length(normalize-space(.)) &gt; 0">
                  <xsl:value-of select="."/>
                </xsl:when>
                <xsl:when test="local-name()='implementation'">
                  <xsl:text>Running the code</xsl:text>
                </xsl:when>
                <xsl:when test="local-name()='inputsOutputs'">
                  <xsl:text>Inputs and Outputs</xsl:text>
                </xsl:when>                
              </xsl:choose>
            </caption>
            <xsl:value-of select="$sp"/>
         </documentation>
      </xsl:for-each>

      <xsl:if test="rm:validation[starts-with(normalize-space(.),'http')]">
         <xsl:value-of select="$sp"/>
         <validationInfo>
            <xsl:value-of select="$subsp"/>
            <url>
            <xsl:value-of select="normalize-space(rm:validation[starts-with(normalize-space(.),'http')])"/>
            </url>
         </validationInfo>
      </xsl:if>

      <xsl:apply-templates select="rm:exportControls[starts-with(
                                                   normalize-space(.),'http')]">
         <xsl:with-param name="sp" select="$sp"/>
         <xsl:with-param name="step" select="$step"/>
      </xsl:apply-templates>

      <xsl:if test="rm:inputsOutputs[string-length(normalize-space(.))>0]">
         <xsl:value-of select="$sp"/>
         <inputsOutputs>
             <xsl:for-each select="rm:inputsOutputs[string-length(normalize-space(.))>0]">
                <xsl:value-of select="."/>
                <xsl:if test="position()!=last()">
                   <xsl:text>

 </xsl:text>
                </xsl:if>
             </xsl:for-each>
         </inputsOutputs>
      </xsl:if>

      <xsl:if test="rm:implementation[not(@href)] | rm:validationData |
                    rm:validation[not(starts-with(normalize-space(.),'http'))]">
         <xsl:value-of select="$sp"/>
         <useNotes>
            <xsl:if test="rm:implementation[not(@href)]">
               <xsl:value-of select="rm:implementation"/>
            </xsl:if>
            <xsl:if test="rm:validationData |
                    rm:validation[not(starts-with(normalize-space(.),'http'))]">
               <xsl:text>
</xsl:text>
               <xsl:text>Validation information: </xsl:text>
               <xsl:value-of select="rm:validation[not(starts-with(normalize-space(.),'http'))]"/>
               <xsl:text>   </xsl:text>
               <xsl:value-of select="rm:validationData"/>
            </xsl:if>
         </useNotes>
      </xsl:if>
   </xsl:template>

   <xsl:template match="rm:exportControls">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:if test="contains(.,'http://') or contains(.,'https://')">
        <xsl:value-of select="$sp"/>
        <exportControlStatement>
           <xsl:value-of select="$subsp"/>
           <url>
             <xsl:value-of select="substring-after(., 
                                        substring-before(.,'http'))"/>
           </url>
           <xsl:if test="not(starts-with(.,'http'))">
              <xsl:value-of select="$subsp"/>
              <caption>
                 <xsl:value-of select="substring-before(.,'http')"/>
              </caption>
           </xsl:if>
           <xsl:value-of select="$sp"/>
        </exportControlStatement>
      </xsl:if>
   </xsl:template>

   <xsl:template match="rm:approach">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <feature>
         <xsl:choose>
            <xsl:when test=".='Multiple'">
               <xsl:text>includes multiple algorithmic approaches</xsl:text>
            </xsl:when>
            <xsl:when test=".='Diffusive'">
               <xsl:text>algorithmic approach includes a diffusive algrorithm</xsl:text>
            </xsl:when>
            <xsl:when test=".='Hartree Fock Method'">
               <xsl:text>algorithmic approach includes </xsl:text>
               <xsl:text>the Hartree Fock Method</xsl:text>
            </xsl:when>
            <xsl:when test=".='Phase Field'">
               <xsl:text>algorithmic approach includes </xsl:text>
               <xsl:text>Phase-Field Modeling</xsl:text>
            </xsl:when>
            <xsl:when test=".='FEM'">
               <xsl:text>algorithmic approach includes </xsl:text>
               <xsl:text>Finite Element Modeling (FEM)</xsl:text>
            </xsl:when>
            <xsl:when test=".='DFT'">
               <xsl:text>algorithmic approach includes </xsl:text>
               <xsl:text>Density Functional Theory (DFT)</xsl:text>
            </xsl:when>
            <xsl:when test=".='CDFT'">
               <xsl:text>algorithmic approach includes </xsl:text>
               <xsl:text>Constrained Density Functional Theory (CDFT)</xsl:text>
            </xsl:when>
            <xsl:when test=".!='None given'">
               <xsl:text>algorithmic approach includes </xsl:text>
               <xsl:value-of select="."/>
            </xsl:when>
         </xsl:choose>
      </feature>
   </xsl:template>

   <xsl:template match="rm:methodAlgorithm">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <feature>
         <xsl:text>supported algorithm: </xsl:text>
         <xsl:value-of select="."/>
      </feature>
   </xsl:template>

   <xsl:template match="rm:documentation">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:if test="@href or string-length(normalize-space(.)) &gt; 0">
         <xsl:value-of select="$sp"/>
         <documentation>
            <xsl:if test="@href">
               <xsl:value-of select="$subsp"/>
               <url><xsl:value-of select="@href"/></url>
            </xsl:if>
            <xsl:if test="string-length(normalize-space(.)) &gt; 0">
               <xsl:value-of select="$subsp"/>
               <caption><xsl:value-of select="."/></caption>
            </xsl:if>
            <xsl:value-of select="$sp"/>
         </documentation>
      </xsl:if>
   </xsl:template>

   <xsl:template match="rm:policy">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <policy>
        <xsl:choose>
           <xsl:when test="rm:restriction|rm:cost">
              <xsl:apply-templates select="rm:restriction">
                 <xsl:with-param name="sp" select="concat($sp,$step)"/>
                 <xsl:with-param name="step" select="$step"/>
              </xsl:apply-templates>
              <xsl:apply-templates select="rm:cost">
                 <xsl:with-param name="sp" select="concat($sp,$step)"/>
                 <xsl:with-param name="step" select="$step"/>
              </xsl:apply-templates>
           </xsl:when>
           <xsl:otherwise>
              <xsl:value-of select="$sp"/>
              <restriction>public</restriction>
           </xsl:otherwise>
        </xsl:choose>

        <xsl:apply-templates select="rm:rights">
           <xsl:with-param name="sp" select="concat($sp,$step)"/>
           <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <!-- turn rm:disclaimer into rights -->
        <xsl:if test="../rm:software/rm:disclaimer">
           <xsl:value-of select="$sp"/>
           <rights>
              <xsl:for-each select="../rm:software/rm:disclaimer">
                 <xsl:value-of select="."/>
                  <xsl:if test="position()!=last()">
                     <xsl:text>

 </xsl:text>
                  </xsl:if>
              </xsl:for-each>
           </rights>
        </xsl:if>

        <xsl:apply-templates select="rm:termsURL">
           <xsl:with-param name="sp" select="concat($sp,$step)"/>
           <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>

        <xsl:apply-templates select="rm:copyright">
           <xsl:with-param name="sp" select="concat($sp,$step)"/>
           <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:value-of select="$sp"/>
      </policy>

   </xsl:template>

   <xsl:template match="rm:termsURL">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:choose>
         <xsl:when test="starts-with(normalize-space(.),'http')">
            <xsl:value-of select="$sp"/>
            <termsURL><xsl:value-of select="."/></termsURL>
         </xsl:when>
         <xsl:when test="contains(., 'http')">
            <xsl:value-of select="$sp"/>
            <termsURL>
              <xsl:value-of select="substring-after(., 
                                        substring-before(.,'http'))"/>
            </termsURL>
         </xsl:when>         
      </xsl:choose>
   </xsl:template>

   <xsl:template match="rm:cost">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:if test="contains(.,'Free')">
         <xsl:if test="not(../rm:rights[normalize-space(.)='public'])">
            <xsl:value-of select="$sp"/>
            <restriction>public</restriction>
         </xsl:if>
      </xsl:if>
      <xsl:if test="contains(.,'Paid') or contains(.,'$')">
         <xsl:if test="not(../rm:rights[normalize-space(.)='fee-required'])">
            <xsl:value-of select="$sp"/>
            <restriction>fee-required</restriction>
         </xsl:if>
      </xsl:if>
   </xsl:template>

   <xsl:template match="rm:disclaimer"></xsl:template>

   <xsl:template match="rm:copyright[.='None stated']"/>

   <xsl:template match="rm:copyright">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <copyright>
         <xsl:value-of select="$subsp"/>
         <crholder>
            <xsl:value-of select="."/>
         </crholder>
         <xsl:if test="@href">
            <xsl:value-of select="$subsp"/>
            <crref>
               <xsl:value-of select="@href"/>
            </crref>
         </xsl:if>
         <xsl:value-of select="$sp"/>
      </copyright>
   </xsl:template>

   <xsl:template name="approachMethods">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:if test="//rm:software/rm:approach[.='FEM'] or
                 //rm:software/rm:methodAlgorithm[contains(.,'FEM') or 
                                                  contains(.,'FEA') or 
                                                  contains(.,'Finite Element')]">
         <xsl:if test="not(//rm:applicability/rm:computationalMethod/rm:finite_element_analysis)">
         <xsl:value-of select="$sp"/>
         <computationalMethod>
            <xsl:value-of select="$subsp"/>
            <finite_element_analysis>
               <xsl:text>finite element analysis</xsl:text>
            </finite_element_analysis>
            <xsl:value-of select="$sp"/>
         </computationalMethod>
         </xsl:if>
      </xsl:if>

      <xsl:if test="//rm:software/rm:approach[.='Quantum Monte Carlo']">
         <xsl:if test="not(//rm:applicability/rm:computationalMethod/rm:Monte_Carlo_methods)">
         <xsl:value-of select="$sp"/>
         <computationalMethod>
            <xsl:value-of select="$subsp"/>
            <Monte_Carlo_methods>
               <xsl:text>Monte Carlo methods</xsl:text>
            </Monte_Carlo_methods>
            <xsl:value-of select="$sp"/>
         </computationalMethod>
         </xsl:if>
      </xsl:if>

      <xsl:if test="//rm:software/rm:approach[.='DFT' or .='CDFT'] or 
                    //rm:software/methodAlgorithm[contains(.,'DFT')]">
         <xsl:if test="not(//rm:applicability/rm:computationalMethod/*[contains(.,'density functional theory')])">
           <xsl:value-of select="$sp"/>
           <computationalMethod>
              <xsl:value-of select="$subsp"/>
              <density_functional_theory_or_electronic_structure>
                 <xsl:text>density functional theory or electronic structure</xsl:text>
              </density_functional_theory_or_electronic_structure>
              <xsl:value-of select="$sp"/>
           </computationalMethod>
         </xsl:if>
      </xsl:if>
   </xsl:template>

</xsl:stylesheet>
