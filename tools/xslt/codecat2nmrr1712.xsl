<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:nr16="urn:nist.gov/nmrr.res/1.0wd"
                xmlns:rm="http://schema.nist.gov/xml/res-md/1.0wd-02-2017"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns="http://schema.nist.gov/xml/res-md/1.0wd-02-2017"
                exclude-result-prefixes="nr16"
                version="1.0">
                
<!-- Stylesheet for converting mgi-resmd records to datacite records -->

   <xsl:output method="xml" encoding="UTF-8" indent="no" />
   <xsl:variable name="autoIndent" select="'  '"/>
   <xsl:preserve-space elements="*"/>

   <!--
     -  a value to set the resource type to
     -->
   <xsl:param name="resourceType"/>

   <!--
     -  default local ID
     -->
   <xsl:param name="defLocalID"/>

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

   <xsl:template match="@*" priority="-0.5">
      <xsl:attribute name="{name()}">
         <xsl:value-of select="."/>
      </xsl:attribute>
   </xsl:template>

   <xsl:template match="nr16:Resource">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:variable name="locid">
         <xsl:choose>
            <xsl:when test="string-length(@localid) > 0">
               <xsl:value-of select="@localid"/>
            </xsl:when>
            <xsl:otherwise>
               <xsl:value-of select="$defLocalID"/>
            </xsl:otherwise>
         </xsl:choose>
      </xsl:variable>

      <Resource status="{@status}" localid="{$locid}">
        <xsl:apply-templates select="nr16:identity">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:curation">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:content">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:call-template name="setRole">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:call-template>
        <xsl:apply-templates select="nr16:applicability[contains(@xsi:type,'MaterialsScience')]">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:access">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:value-of select="$sp"/>
      </Resource>
   </xsl:template>

   <xsl:template match="nr16:identity">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <identity>
        <xsl:apply-templates select="nr16:title" >         
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:shortName" >         
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:version" >         
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:identifier" >         
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:logoURL" >         
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:value-of select="$sp"/>
      </identity>
   </xsl:template>

   <xsl:template match="nr16:title">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <title>
         <xsl:value-of select="."/>
      </title>
   </xsl:template>

   <xsl:template match="nr16:shortName">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <altTitle type="Abbreviation">
         <xsl:value-of select="normalize-space(.)"/>
      </altTitle>
   </xsl:template>

   <xsl:template match="nr16:version">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <version>
         <xsl:value-of select="normalize-space(.)"/>
      </version>
   </xsl:template>

   <xsl:template match="nr16:identifier">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <identifier>
         <xsl:value-of select="normalize-space(.)"/>
      </identifier>
   </xsl:template>

   <xsl:template match="nr16:logoURL">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <logo>
         <xsl:value-of select="normalize-space(.)"/>
      </logo>
   </xsl:template>

   <xsl:template match="nr16:curation">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <providers>
        <xsl:apply-templates select="nr16:publisher">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:creator">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:contributor">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:date">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:contact">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:value-of select="$sp"/>
      </providers>
   </xsl:template>

   <xsl:template match="nr16:publisher">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <publisher>
         <xsl:value-of select="normalize-space(.)"/>
      </publisher>
   </xsl:template>

   <xsl:template match="nr16:creator">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <creator>
         <xsl:value-of select="$subsp"/>
         <name><xsl:value-of select="normalize-space(.)"/></name>
         <xsl:value-of select="$sp"/>
      </creator>
   </xsl:template>

   <xsl:template match="nr16:contributor">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <contributor role="ProjectMember">
         <xsl:value-of select="$subsp"/>
         <name><xsl:value-of select="normalize-space(.)"/></name>
         <xsl:value-of select="$sp"/>
      </contributor>
   </xsl:template>

   <xsl:template match="nr16:date">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:variable name="role">
         <xsl:choose>
             <xsl:when test="@role='created'">Created</xsl:when>
             <xsl:when test="@role='released'">Available</xsl:when>
             <xsl:when test="@role='established'">Created</xsl:when>
             <xsl:otherwise>Updated</xsl:otherwise>
         </xsl:choose>
      </xsl:variable>

      <xsl:value-of select="$sp"/>
      <date role="{$role}" xsi:type="DciteDate">
         <xsl:value-of select="normalize-space(.)"/>
      </date>
   </xsl:template>

   <xsl:template match="nr16:contact">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <contact>
        <xsl:apply-templates select="nr16:name">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:postalAddress">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:emailAddress">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:phoneNumber">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:timezone">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:value-of select="$sp"/>
      </contact>
   </xsl:template>

   <xsl:template match="nr16:contact/*">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <xsl:element name="{local-name(.)}">
         <xsl:value-of select="normalize-space(.)"/>
      </xsl:element>
   </xsl:template>

   <xsl:template match="nr16:contact/nr16:postalAddress">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:variable name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <postalAddress>
        <xsl:value-of select="$subsp"/>
        <addressLine>
           <xsl:value-of select="normalize-space(.)"/>
        </addressLine>
        <xsl:value-of select="$sp"/>
      </postalAddress>
   </xsl:template>

   <xsl:template match="nr16:content">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <content>
        <xsl:apply-templates select="nr16:description">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>

        <xsl:choose>
           <xsl:when test="nr16:subject">
              <xsl:apply-templates select="nr16:subject">
                <xsl:with-param name="sp" select="concat($sp,$step)"/>
                <xsl:with-param name="step" select="$step"/>
              </xsl:apply-templates>
           </xsl:when>
           <xsl:otherwise><subject>software</subject></xsl:otherwise>
        </xsl:choose>

        <xsl:apply-templates select="nr16:referenceURL">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:referenceCitation">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:primaryAudience">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:value-of select="$sp"/>
      </content>
   </xsl:template>

   <xsl:template match="nr16:content/*">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <xsl:element name="{local-name(.)}">
         <xsl:value-of select="normalize-space(.)"/>
      </xsl:element>
   </xsl:template>

   <xsl:template match="nr16:referenceURL" priority="1">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <landingPage>
        <xsl:value-of select="normalize-space(.)"/>
      </landingPage>
   </xsl:template>

   <xsl:template match="nr16:referenceCitation" priority="1">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <xsl:element name="reference">
         <xsl:if test="@pid">
           <xsl:attribute name="pid">
              <xsl:value-of select="@pid"/>
           </xsl:attribute>
         </xsl:if>
         <xsl:value-of select="normalize-space(.)"/>
      </xsl:element>
   </xsl:template>

   <xsl:template name="setRole">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:choose>
         <xsl:when test="nr16:content/nr16:type">
            <xsl:for-each select="nr16:content/nr16:type">
               <xsl:call-template name="resourceType">
                 <xsl:with-param name="sp" select="$sp"/>
                 <xsl:with-param name="step" select="$step"/>
               </xsl:call-template>
            </xsl:for-each>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="rt">
               <xsl:choose>
                  <xsl:when test="$resourceType!=''">
                     <xsl:value-of select="$resourceType"/>
                  </xsl:when>
                  <xsl:otherwise>Organization: Project</xsl:otherwise>
               </xsl:choose>
            </xsl:variable>
            <xsl:call-template name="resourceType">
              <xsl:with-param name="sp" select="$sp"/>
              <xsl:with-param name="step" select="$step"/>
              <xsl:with-param name="ctype" select="$rt"/>
            </xsl:call-template>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <xsl:template name="resourceType">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>
      <xsl:param name="ctype">
         <xsl:choose>
            <xsl:when test="$resourceType!=''">
               <xsl:value-of select="$resourceType"/>
            </xsl:when>
            <xsl:otherwise><xsl:value-of select="."/></xsl:otherwise>
         </xsl:choose>
      </xsl:param>

      <xsl:param name="type">
         <xsl:choose>
            <xsl:when test="$ctype='Repository'">Collection: Repository</xsl:when>
            <xsl:when test="$ctype='Database'">Dataset: Database</xsl:when>
            <xsl:when test="$ctype='Dataset'">Dataset</xsl:when>
            <xsl:when test="$ctype='DataCollection'">Collection</xsl:when>
            <xsl:when test="$ctype='Informational'">Web Site: Informational</xsl:when>
            <xsl:when test="$ctype='Organization'">Organization: Institution</xsl:when>
            <xsl:when test="$ctype='Project'">Organization: Project</xsl:when>
            <xsl:when test="$ctype='ProjectArchive'">Collection: Project Archive</xsl:when>
            <xsl:when test="$ctype='Service'">Service: API</xsl:when>
            <xsl:when test="$ctype='Software'">Software</xsl:when>
            
         </xsl:choose>
      </xsl:param>

      <xsl:param name="xsitype">
         <xsl:choose>
            <xsl:when test="starts-with($type, 'Collection')">DataCollection</xsl:when>
            <xsl:when test="starts-with($type, 'Dataset')">Dataset</xsl:when>
            <xsl:when test="starts-with($type, 'Web Site')">WebSite</xsl:when>
            <xsl:when test="starts-with($type, 'Service')">ServiceAPI</xsl:when>
            <xsl:when test="starts-with($type, 'Organization')">Organization</xsl:when>
            <xsl:when test="starts-with($type, 'Software')">Software</xsl:when>
         </xsl:choose>
      </xsl:param>

      <xsl:value-of select="$sp"/>
      <role xsi:type="{$xsitype}">
        <xsl:value-of select="$subsp"/>
        <type><xsl:value-of select="$type"/></type>

        <!-- role-specific metadata -->
        <xsl:choose>
           <xsl:when test="$type='Software'">
              <xsl:apply-templates select="//nr16:access/nr16:software">
                <xsl:with-param name="sp" select="concat($sp,$step)"/>
                <xsl:with-param name="step" select="$step"/>
              </xsl:apply-templates>
           </xsl:when>
        </xsl:choose>
        
        <xsl:value-of select="$sp"/>
      </role>   
   </xsl:template>

   <xsl:template match="nr16:access/nr16:software">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <software>
         <xsl:apply-templates select="*">
           <xsl:with-param name="sp" select="concat($subsp,$step)"/>
           <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>

         <xsl:apply-templates select="//nr16:applicability/nr16:approach">
           <xsl:with-param name="sp" select="concat($subsp,$step)"/>
           <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>
         <xsl:apply-templates select="//nr16:applicability/nr16:methodAlgorithm">
           <xsl:with-param name="sp" select="concat($subsp,$step)"/>
           <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>
         <xsl:apply-templates select="//nr16:applicability/nr16:scale">
           <xsl:with-param name="sp" select="concat($subsp,$step)"/>
           <xsl:with-param name="step" select="$step"/>
         </xsl:apply-templates>

         <xsl:value-of select="$sp"/>
      </software>   
   </xsl:template>

   <xsl:template match="nr16:applicability[contains(@xsi:type,'MaterialsScience')]">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <applicability xsi:type="MaterialsScience">
        <xsl:apply-templates select="nr16:materialType">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:structuralMorphology">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:propertyClass">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:experimentalDataAcquisitionMethod">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:computationalDataAcquisitionMethod">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:synthesisProcessing">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
         
        <xsl:value-of select="$sp"/>
      </applicability>
   </xsl:template>

   <xsl:template match="nr16:materialType">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <materialType>
        <xsl:value-of select="$subsp"/>
        <xsl:apply-templates select="." mode="value"/>
        <xsl:value-of select="$sp"/>
      </materialType>
   </xsl:template>

   <!-- these values are no longer supported -->
   <xsl:template match="nr16:materialType[.='non-specific']"/>
   <xsl:template match="nr16:materialType[.='superconductor']"/>
   <xsl:template match="nr16:materialType[.='nanomaterials']"/>
   <xsl:template match="nr16:materialType[.='composite']"/>
   <xsl:template match="nr16:materialType[.='inorganic']"/>

   <xsl:template match="nr16:materialType[.='metal']" mode="value">
      <metals_and_alloys>metals and alloys</metals_and_alloys>
   </xsl:template>
   <xsl:template match="nr16:materialType[.='semiconductor']" mode="value">
      <semiconductors>semiconductors</semiconductors>
   </xsl:template>
   <xsl:template match="nr16:materialType[.='polymer']" mode="value">
      <polymers>polymers</polymers>
   </xsl:template>
   <xsl:template match="nr16:materialType[.='biomaterial']" mode="value">
      <biomaterials>biomaterials</biomaterials>
   </xsl:template>
   <xsl:template match="nr16:materialType[.='organic']" mode="value">
      <organic_compounds>organic compounds</organic_compounds>
   </xsl:template>
   <xsl:template match="nr16:materialType[.='oxide']" mode="value">
      <ceramics>ceramics: oxides</ceramics>
   </xsl:template>
   <xsl:template match="nr16:materialType[.='ceramic']" mode="value">
      <ceramics>ceramics</ceramics>
   </xsl:template>
   <xsl:template match="nr16:materialType" mode="value">
      <!-- this will not validate -->
      <xsl:variable name="plural" select="concat(.,'s')"/>
      <xsl:element name="{$plural}">
         <xsl:value-of select="$plural"/>
      </xsl:element>
   </xsl:template>

   <xsl:template match="nr16:structuralMorphology">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <structuralFeature>
        <xsl:value-of select="$subsp"/>
        <xsl:apply-templates select="." mode="value"/>
        <xsl:value-of select="$sp"/>
      </structuralFeature>
   </xsl:template>

   <!-- these values are no longer supported -->
   <xsl:template match="nr16:structuralMorphology[.='non-specific']"/>
   <xsl:template match="nr16:structuralMorphology[.='bulk']"/>
   <xsl:template match="nr16:structuralMorphology[.='interphase']"/>

   <xsl:template match="nr16:structuralMorphology[.='crystalline']" mode="value">
      <microstructures>microstructures: single crystal</microstructures>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='amorphous']" mode="value">
      <morphologies>morphologies: amorphous</morphologies>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='fluid']" mode="value">
      <phases>phases: liquid</phases>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='quasi-periodic']" mode="value">
      <microstructures>microstructures: quasicrystalline</microstructures>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='1D']" mode="value">
      <morphologies>morphologies: 1D</morphologies>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='2D']" mode="value">
      <morphologies>morphologies: 2D</morphologies>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='film']" mode="value">
      <morphologies>morphologies: thin film</morphologies>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='nanotube']" mode="value">
      <morphologies>morphologies: nanoparticle / nanotube</morphologies>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='fiber']" mode="value">
      <composites>composites: fiber-reinforced</composites>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='composite']" mode="value">
      <composites>composites</composites>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='interfacial']" mode="value">
      <interfacial>interfacial</interfacial>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='line defect']" mode="value">
      <defects>defects: dislocations</defects>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology[.='point defect']" mode="value">
      <defects>defects: point defects</defects>
   </xsl:template>
   <xsl:template match="nr16:structuralMorphology" mode="value">
      <!-- this will not validate -->
      <xsl:variable name="plural" select="concat(.,'s')"/>
      <xsl:element name="{$plural}">
         <xsl:value-of select="$plural"/>
      </xsl:element>
   </xsl:template>
   
   <xsl:template match="nr16:propertyClass">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <propertyAddressed>
        <xsl:value-of select="$subsp"/>
        <xsl:apply-templates select="." mode="value"/>
        <xsl:value-of select="$sp"/>
      </propertyAddressed>
   </xsl:template>

   <!-- these values are no longer supported -->
   <xsl:template match="nr16:propertyClass[.='non-specific']"/>
   <xsl:template match="nr16:propertyClass[.='simulated']"/>

   <xsl:template match="nr16:propertyClass[.='optical']" mode="value">
      <optical>optical</optical>
   </xsl:template>
   <xsl:template match="nr16:propertyClass[.='mechanical']" mode="value">
      <mechanical>mechanical</mechanical>
   </xsl:template>
   <xsl:template match="nr16:propertyClass[.='thermodynamic']" mode="value">
      <thermodynamic>thermodynamic</thermodynamic>
   </xsl:template>
   <xsl:template match="nr16:propertyClass[.='structural']" mode="value">
      <structural>structural</structural>
   </xsl:template>
   <xsl:template match="nr16:propertyClass[.='transport']" mode="value">
      <transport>transport</transport>
   </xsl:template>
   <xsl:template match="nr16:propertyClass[.='defect']" mode="value">
      <microstructural>microstructural: defect structures</microstructural>
   </xsl:template>
   <xsl:template match="nr16:propertyClass" mode="value">
      <!-- this will not validate -->
      <xsl:variable name="plural" select="concat(.,'s')"/>
      <xsl:element name="{$plural}">
         <xsl:value-of select="$plural"/>
      </xsl:element>
   </xsl:template>

   <xsl:template match="nr16:experimentalDataAcquisitionMethod">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <experimentalMethod>
        <xsl:value-of select="$subsp"/>
        <xsl:apply-templates select="." mode="value"/>
        <xsl:value-of select="$sp"/>
      </experimentalMethod>
   </xsl:template>

   <!-- these values are no longer supported -->
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='non-specific']"/>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='load frame testing']"/>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='impact testing']"/>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='other']"/>

   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='electron microscopy']" mode="value">
      <microscopy>microscopy</microscopy>
   </xsl:template>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='atom probe microscopy']" mode="value">
      <microscopy>microscopy</microscopy>
   </xsl:template>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='optical microscopy']" mode="value">
      <microscopy>microscopy: optical microscopy</microscopy>
   </xsl:template>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='scattering-diffraction']" mode="value">
      <scattering_and_diffraction>scattering and diffraction</scattering_and_diffraction>
   </xsl:template>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='calorimetry']" mode="value">
      <thermochemical>thermochemical: calorimetry</thermochemical>
   </xsl:template>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='spectroscopy']" mode="value">
      <spectrometry>spectrometry</spectrometry>
   </xsl:template>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='indentation']" mode="value">
      <mechanical>mechanical: nanoindentation</mechanical>
   </xsl:template>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod[.='dilatometry']" mode="value">
      <dilatometry>dilatometry</dilatometry>
   </xsl:template>
   <xsl:template match="nr16:experimentalDataAcquisitionMethod" mode="value">
      <!-- this will not validate -->
      <xsl:variable name="plural" select="concat(.,'s')"/>
      <xsl:element name="{$plural}">
         <xsl:value-of select="$plural"/>
      </xsl:element>
   </xsl:template>

   <xsl:template match="nr16:computationalDataAcquisitionMethod">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <computationalMethod>
        <xsl:value-of select="$subsp"/>
        <xsl:apply-templates select="." mode="value"/>
        <xsl:value-of select="$sp"/>
      </computationalMethod>
   </xsl:template>

   <!-- these values are no longer supported -->
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='non-specific']"/>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='numerical simulations']"/>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='computational thermodynamics']"/>

   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='density functional theory calculation']" mode="value">
      <density_functional_theory_or_electronic_structure>density functional theory or electronic structure</density_functional_theory_or_electronic_structure>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='molecular dynamics simulation']" mode="value">
      <molecular_dynamics>molecular dynamics</molecular_dynamics>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='multiscale simulations']" mode="value">
      <multiscale_simulations>multiscale simulations</multiscale_simulations>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='finite element analysis']" mode="value">
      <finite_element_analysis>finite element analysis</finite_element_analysis>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='statistical mechanics']" mode="value">
      <statistical_mechanics>statistical mechanics</statistical_mechanics>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='dislocation dynamics']" mode="value">
      <dislocation_dynamics>dislocation dynamics</dislocation_dynamics>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='phase field calculation']" mode="value">
      <phase-field_calculations>phase-field calculations</phase-field_calculations>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='crystal plasticity calculation']" mode="value">
      <crystal_plasticity>crystal plasticity</crystal_plasticity>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='monte-carlo simulation']" mode="value">
      <Monte-Carlo_methods>Monte-Carlo methods</Monte-Carlo_methods>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod[.='boundary tracking/level set']" mode="value">
      <boundary_tracking_or_level_set>boundary tracking or level set</boundary_tracking_or_level_set>
   </xsl:template>
   <xsl:template match="nr16:computationalDataAcquisitionMethod" mode="value">
      <!-- this will not validate -->
      <xsl:variable name="plural" select="concat(.,'s')"/>
      <xsl:element name="{$plural}">
         <xsl:value-of select="$plural"/>
      </xsl:element>
   </xsl:template>

   <xsl:template match="nr16:sampleProcessing">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <synthesisProcessing>
        <xsl:value-of select="$subsp"/>
        <xsl:apply-templates select="." mode="value"/>
        <xsl:value-of select="$sp"/>
      </synthesisProcessing>
   </xsl:template>

   <!-- these values are no longer supported -->
   <xsl:template match="nr16:sampleProcessing[.='non-specific']"/>
   <xsl:template match="nr16:sampleProcessing[.='exfoliation']"/>

   <xsl:template match="nr16:sampleProcessing[.='casting']" mode="value">
      <casting>casting</casting>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='annealing']" mode="value">
      <annealing_and_homogenization>annealing and homogenization</annealing_and_homogenization>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='vapor deposition']" mode="value">
      <deposition_and_coating>deposition and coating: physical vapor deposition</deposition_and_coating>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='milling']" mode="value">
      <forming>forming: milling</forming>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='extrusion']" mode="value">
      <forming>forming: extrusion</forming>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='pressing']" mode="value">
      <forming>forming: hot pressing</forming>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='melt blending']" mode="value">
      <annealing_and_homogenization>annealing and homogenization: melt mixing</annealing_and_homogenization>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='polymerisation']" mode="value">
      <reactive>reactive: in-situ polymerization</reactive>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='curing']" mode="value">
      <reactive>reactive: curing</reactive>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing[.='evaporation']" mode="value">
      <deposition_and_coating>deposition and coating: evaporation</deposition_and_coating>
   </xsl:template>
   <xsl:template match="nr16:sampleProcessing" mode="value">
      <!-- this will not validate -->
      <xsl:variable name="plural" select="concat(.,'s')"/>
      <xsl:element name="{$plural}">
         <xsl:value-of select="$plural"/>
      </xsl:element>
   </xsl:template>

   <xsl:template match="nr16:access">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <access>
        <xsl:apply-templates select="nr16:policy">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:portal">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:serviceAPI">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        
        <xsl:value-of select="$sp"/>
      </access>
   </xsl:template>

   <xsl:template match="nr16:policy">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <policy>
        <xsl:apply-templates select="nr16:rights">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:terms">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:copyright">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:cost">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>

        <xsl:value-of select="$sp"/>
      </policy>
   </xsl:template>

   <xsl:template match="nr16:rights">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <restriction>
         <xsl:value-of select="."/>
      </restriction>
   </xsl:template>

   <xsl:template match="nr16:terms">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <termsURL>
         <xsl:value-of select="."/>
      </termsURL>
   </xsl:template>

   <xsl:template match="nr16:portal">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <method xsi:type="PortalMethod">
        <xsl:apply-templates select="nr16:title">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:description">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:homeURL">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>

        <xsl:value-of select="$sp"/>
      </method>
   </xsl:template>

   <xsl:template match="nr16:homeURL">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <accessURL use="full">
         <xsl:value-of select="."/>
      </accessURL>
   </xsl:template>

   <xsl:template match="nr16:serviceAPI">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <method xsi:type="ServiceAPIMethod">
        <xsl:apply-templates select="nr16:title">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:description">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        
        <xsl:value-of select="$subsp"/>
        <details>
           <xsl:value-of select="$subsp"/>
           <xsl:value-of select="$step"/>
           <type>Service: API</type>
           <xsl:apply-templates select="nr16:baseURL">
             <xsl:with-param name="sp" select="concat($subsp,$step)"/>
             <xsl:with-param name="step" select="$step"/>
           </xsl:apply-templates>
           <xsl:value-of select="$subsp"/>
        </details>

        <xsl:value-of select="$sp"/>
      </method>
   </xsl:template>

   <xsl:template match="nr16:documentationURL">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <accessURL>
         <xsl:value-of select="."/>
      </accessURL>
   </xsl:template>

   <xsl:template match="nr16:baseURL">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <baseURL>
         <xsl:value-of select="."/>
      </baseURL>
   </xsl:template>

   <xsl:template match="nr16:download">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>
      <xsl:param name="subsp" select="concat($sp,$step)"/>

      <xsl:value-of select="$sp"/>
      <method xsi:type="ServiceAPIMethod">
        <xsl:apply-templates select="nr16:title">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:description">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        <xsl:apply-templates select="nr16:accessURL">
          <xsl:with-param name="sp" select="concat($sp,$step)"/>
          <xsl:with-param name="step" select="$step"/>
        </xsl:apply-templates>
        
        <xsl:value-of select="$sp"/>
      </method>
   </xsl:template>

   <xsl:template match="nr16:accessURL">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <xsl:element name="accessURL">
         <xsl:if test="@use">
           <xsl:attribute name="use">
             <xsl:value-of select="@use"/>
           </xsl:attribute>
         </xsl:if>
         <xsl:value-of select="."/>
      </xsl:element>
   </xsl:template>

   <xsl:template match="nr16:description|nr16:title">
      <xsl:param name="sp"/>
      <xsl:param name="step"/>

      <xsl:value-of select="$sp"/>
      <xsl:element name="{local-name(.)}">
         <xsl:value-of select="normalize-space(.)"/>
      </xsl:element>
   </xsl:template>



</xsl:stylesheet>
