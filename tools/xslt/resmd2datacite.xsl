<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:dc="http://datacite.org/schema/kernel-3"
                xmlns:rsm="http://schema.nist.gov/xml/res-md/1.0wd" 
                xmlns:rdc="http://schema.nist.gov/xml/resmd-datacite/1.0wd"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns="http://datacite.org/schema/kernel-3"
                exclude-result-prefixes="dc rsm rdc xsi" 
                version="1.0">
                
<!-- Stylesheet for converting mgi-resmd records to datacite records -->

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
   <xsl:param name="indent">
      <xsl:for-each select="/*/*[2]">
         <xsl:call-template name="getindent"/>
      </xsl:for-each>
   </xsl:param>

   <xsl:param name="dataciteNS">http://datacite.org/schema/kernel-3</xsl:param>

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


   <xsl:template match="/*[identity]">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:element name="resource" namespace="{$dataciteNS}">
     
       <xsl:apply-templates select="identity" mode="identifier">
         <xsl:with-param name="sp" select="concat($sp,$step)"/>
         <xsl:with-param name="step" select="$step"/>
       </xsl:apply-templates>

       <xsl:apply-templates select="curation" mode="creators">       
         <xsl:with-param name="sp" select="concat($sp,$step)"/>
         <xsl:with-param name="step" select="$step"/>
       </xsl:apply-templates>

       <xsl:apply-templates select="identity" mode="titles">       
         <xsl:with-param name="sp" select="concat($sp,$step)"/>
         <xsl:with-param name="step" select="$step"/>
       </xsl:apply-templates>

       <xsl:apply-templates select="curation/publisher">       
         <xsl:with-param name="sp" select="concat($sp,$step)"/>
         <xsl:with-param name="step" select="$step"/>
       </xsl:apply-templates>

       <xsl:apply-templates select="curation/publicationYear">       
         <xsl:with-param name="sp" select="concat($sp,$step)"/>
         <xsl:with-param name="step" select="$step"/>
       </xsl:apply-templates>

       <xsl:apply-templates select="content" mode="subjects">       
         <xsl:with-param name="sp" select="concat($sp,$step)"/>
         <xsl:with-param name="step" select="$step"/>
       </xsl:apply-templates>

       <xsl:value-of select="$sp"/>
     </xsl:element>
   </xsl:template>

   <xsl:template match="identity" mode="identifier">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:value-of select="$sp"/>
     <xsl:choose>
       <xsl:when test="identifier[@type='DOI']">
         <identifier doiType="DOI">
           <xsl:value-of select="identifier[@type='DOI']"/>
         </identifier>
       </xsl:when>
       <xsl:otherwise>
         <identifier doiType="URL">
           <xsl:value-of select="../@localid"/>
         </identifier>
       </xsl:otherwise>
     </xsl:choose>

   </xsl:template>

   <xsl:template match="curation" mode="creators">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:value-of select="$sp"/>
     <creators>
        <xsl:if test="creator">
          <xsl:apply-templates select="creator" mode="creators">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
          </xsl:apply-templates>       
          <xsl:value-of select="$sp"/>
        </xsl:if>
     </creators>
   </xsl:template>

   <xsl:template match="creator" mode="creators">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:variable name="subsp" select="concat($sp,$step)"/>

     <xsl:value-of select="$sp"/>
     <creator>
       <xsl:value-of select="$subsp"/>
       <creatorName>
          <xsl:apply-templates select="name" mode="flipName"/>
       </creatorName>
       <xsl:if test="name/@pid">
          <xsl:variable name="scheme">
             <xsl:call-template name="getidscheme">
                <xsl:with-param name="pid" select="name/@pid"/>
             </xsl:call-template>
          </xsl:variable>
          <xsl:variable name="uri">
             <xsl:call-template name="getiduri">
                <xsl:with-param name="id" select="$scheme"/>
             </xsl:call-template>
          </xsl:variable>
          
          <xsl:value-of select="$subsp"/>
          <xsl:element name="nameIdentifier">
             <xsl:attribute name="nameIdentifierScheme">
                <xsl:value-of select="$scheme"/>
             </xsl:attribute>
             <xsl:if test="$uri">
                <xsl:attribute name="schemeURI">
                   <xsl:value-of select="$uri"/>
                </xsl:attribute>
             </xsl:if>
             <xsl:value-of select="name/@pid"/>
          </xsl:element>
       </xsl:if>
       <xsl:value-of select="$sp"/>
     </creator>
   </xsl:template>

   <xsl:template match="curation" mode="contributors">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:value-of select="$sp"/>
     <contributors>
        <xsl:if test="contributor">
          <xsl:apply-templates select="contributor" mode="creators">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
          </xsl:apply-templates>       
          <xsl:value-of select="$sp"/>
        </xsl:if>
     </contributors>
   </xsl:template>

   <xsl:template match="creator" mode="creators">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:variable name="subsp" select="concat($sp,$step)"/>

     <xsl:value-of select="$sp"/>
     <creator>
       <xsl:value-of select="$subsp"/>
       <creatorName>
          <xsl:apply-templates select="name" mode="flipName"/>
       </creatorName>
       <xsl:if test="name/@pid">
          <xsl:variable name="scheme">
             <xsl:call-template name="getidscheme">
                <xsl:with-param name="pid" select="name/@pid"/>
             </xsl:call-template>
          </xsl:variable>
          <xsl:variable name="uri">
             <xsl:call-template name="getiduri">
                <xsl:with-param name="id" select="$scheme"/>
             </xsl:call-template>
          </xsl:variable>
          
          <xsl:value-of select="$subsp"/>
          <xsl:element name="nameIdentifier">
             <xsl:attribute name="nameIdentifierScheme">
                <xsl:value-of select="$scheme"/>
             </xsl:attribute>
             <xsl:if test="$uri">
                <xsl:attribute name="schemeURI">
                   <xsl:value-of select="$uri"/>
                </xsl:attribute>
             </xsl:if>
             <xsl:value-of select="name/@pid"/>
          </xsl:element>
       </xsl:if>
       <xsl:value-of select="$sp"/>
     </creator>
   </xsl:template>

   <xsl:template match="identity" mode="titles">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:variable name="subsp" select="concat($sp,$step)"/>

     <xsl:value-of select="$sp"/>
     <titles>
       <xsl:apply-templates select="title" mode="titles">
         <xsl:with-param name="sp" select="concat($sp,$step)"/>
         <xsl:with-param name="step" select="$step"/>
       </xsl:apply-templates>

       <xsl:apply-templates select="altTitle" mode="titles">
         <xsl:with-param name="sp" select="concat($sp,$step)"/>
         <xsl:with-param name="step" select="$step"/>
       </xsl:apply-templates>

       <xsl:value-of select="$sp"/>
     </titles>      
   </xsl:template>

   <xsl:template match="title" mode="titles">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:value-of select="$sp"/>
     <title>
        <xsl:value-of select="normalize-space(.)"/>
     </title>
   </xsl:template>

   <xsl:template match="altTitle" mode="titles">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:value-of select="$sp"/>
     <xsl:element name="title">
        <xsl:attribute name="titleType">
           <xsl:value-of select="@type"/>
        </xsl:attribute>
        <xsl:if test="@xml:lang">
           <xsl:attribute name="xml:lang">
              <xsl:value-of select="@xml:lang"/>
           </xsl:attribute>
        </xsl:if>

        <xsl:value-of select="normalize-space(.)"/>

     </xsl:element>
   </xsl:template>

   <xsl:template match="publisher">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:value-of select="$sp"/>
     <publisher>
        <xsl:value-of select="normalize-space(.)"/>
     </publisher>
   </xsl:template>

   <xsl:template match="publicationYear">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:value-of select="$sp"/>
     <publicationYear>
        <xsl:value-of select="."/>
     </publicationYear>
   </xsl:template>

   <xsl:template match="content" mode="subjects">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:value-of select="$sp"/>
     <subjects>
        <xsl:if test="subject">
          <xsl:apply-templates select="subject" mode="subjects">
            <xsl:with-param name="sp" select="concat($sp,$step)"/>
            <xsl:with-param name="step" select="$step"/>
          </xsl:apply-templates>       
          <xsl:value-of select="$sp"/>
        </xsl:if>
     </subjects>
   </xsl:template>

   <xsl:template match="subject" mode="subjects">
     <xsl:param name="sp"/>
     <xsl:param name="step"/>

     <xsl:variable name="subsp" select="concat($sp,$step)"/>

     <xsl:value-of select="$sp"/>
     <xsl:element name="subject">
        <xsl:if test="@scheme">
           <xsl:attribute name="subjectScheme">
              <xsl:value-of select="@scheme"/>
           </xsl:attribute>
        </xsl:if>
        <xsl:if test="@schemeURI">
           <xsl:attribute name="schemeURI">
              <xsl:value-of select="@schemeURI"/>
           </xsl:attribute>
        </xsl:if>
        <xsl:if test="@xml:lang">
           <xsl:attribute name="xml:lang">
              <xsl:value-of select="@xml:lang"/>
           </xsl:attribute>
        </xsl:if>

        <xsl:value-of select="normalize-space(.)"/>

     </xsl:element>
   </xsl:template>


   <!-- ==========================================================
     -  Utility templates
     -  ========================================================== -->

   <!--
     -  determine the indentation preceding the context element
     -->
   <xsl:template name="getindent">
      <xsl:variable name="prevsp">
         <xsl:for-each select="preceding-sibling::text()">
            <xsl:if test="position()=last()">
               <xsl:value-of select="."/>
            </xsl:if>
         </xsl:for-each>
      </xsl:variable>

      <xsl:choose>
         <xsl:when test="contains($prevsp,$cr)">
            <xsl:call-template name="afterLastCR">
               <xsl:with-param name="text" select="$prevsp"/>
            </xsl:call-template>
         </xsl:when>
         <xsl:when test="$prevsp">
            <xsl:value-of select="$prevsp"/>
         </xsl:when>
         <xsl:otherwise><xsl:text>    </xsl:text></xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <!--
     -  return the text that appears after the last carriage return
     -  in the input text
     -  @param text  the input text to process
     -->
   <xsl:template name="afterLastCR">
      <xsl:param name="text"/>
      <xsl:choose>
         <xsl:when test="contains($text,$cr)">
            <xsl:call-template name="afterLastCR">
               <xsl:with-param name="text" select="substring-after($text,$cr)"/>
            </xsl:call-template>
         </xsl:when>
         <xsl:otherwise><xsl:value-of select="$text"/></xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <!--
     -  indent the given number of levels.  The amount of indentation will 
     -  be nlev times the value of the global $indent.
     -  @param nlev   the number of indentations to insert.
     -  @param sp     the string representing the per-indentation space;
     -                  defaults to the value of $indent
     -->
   <xsl:template name="doindent">
      <xsl:param name="nlev" select="2"/>
      <xsl:param name="sp" select="$indent"/>

      <xsl:if test="$nlev &gt; 0">
         <xsl:value-of select="$sp"/>
         <xsl:if test="$nlev &gt; 1">
            <xsl:call-template name="doindent">
               <xsl:with-param name="nlev" select="$nlev - 1"/>
               <xsl:with-param name="sp" select="$sp"/>
            </xsl:call-template>
         </xsl:if>
      </xsl:if>
   </xsl:template>

   <!--
     -  convert all input characters to lower case
     -  @param in  the string to convert
     -->
   <xsl:template name="lower">
      <xsl:param name="in"/>
      <xsl:value-of select="translate($in,
                                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                                      'abcdefghijklmnopqrstuvwxyz')"/>
   </xsl:template>

   <!--
     -  convert the first character to an upper case
     -  @param in  the string to convert
     -->
   <xsl:template name="capitalize">
      <xsl:param name="in"/>
      <xsl:value-of select="translate(substring($in,1,1),
                                      'abcdefghijklmnopqrstuvwxyz',
                                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ')"/>
      <xsl:value-of select="substring($in,2)"/>
   </xsl:template>

   <!--
     -  convert all input characters to lower case and then capitalize
     -  @param in  the string to convert
     -->
   <xsl:template name="lowerandcap">
      <xsl:param name="in"/>
      <xsl:call-template name="capitalize">
         <xsl:with-param name="in">
            <xsl:call-template name="lower">
               <xsl:with-param name="in" select="$in"/>
            </xsl:call-template>
         </xsl:with-param>
      </xsl:call-template>
   </xsl:template>

   <!--
     -  measure the indentation inside a node
     -  @param text   a text node containing the indentation
     -->
   <xsl:template name="measIndent">
      <xsl:param name="text"/>

      <xsl:variable name="indnt">
         <xsl:call-template name="afterLastCR">
            <xsl:with-param name="text" select="$text"/>
         </xsl:call-template>
      </xsl:variable>

      <xsl:value-of select="string-length($indnt)"/>
   </xsl:template>

   <!--
     -  attempt to return the extra indentation applied to children 
     -    of the current context node.  If a positive indentation cannot
     -    be returned, return the default indentation.
     -->
   <xsl:template match="*" mode="getIndentStep">
      <xsl:variable name="prevind">
         <xsl:call-template name="measIndent">
            <xsl:with-param name="text">
               <xsl:call-template name="getindent"/>
            </xsl:with-param>
         </xsl:call-template>
      </xsl:variable>
      <xsl:variable name="childind">
         <xsl:call-template name="measIndent">
            <xsl:with-param name="text">
               <xsl:for-each select="*[1]">
                  <xsl:call-template name="getindent"/>
               </xsl:for-each>
            </xsl:with-param>
         </xsl:call-template>
      </xsl:variable>
      <xsl:variable name="diff" select="$childind - $prevind"/>

      <xsl:choose>
         <xsl:when test="number($childind) &gt; number($prevind) and 
                         number($prevind) &gt; 0">
            <xsl:call-template name="doindent">
               <xsl:with-param name="nlev" select="$diff"/>
               <xsl:with-param name="sp" select="' '"/>
            </xsl:call-template>
         </xsl:when>
         <xsl:otherwise><xsl:value-of select="$indent"/></xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <xsl:template match="*" mode="flipName">
      <xsl:choose>
         <xsl:when test="@sur">
            <!-- use @sur, @given, @middle -->
            <xsl:value-of select="@sur"/>
            <xsl:text>, </xsl:text>
            <xsl:if test="@given">
               <xsl:value-of select="@given"/>
               <xsl:if test="@middle">
                  <xsl:text> </xsl:text>
                  <xsl:value-of select="@middle"/>
               </xsl:if>
            </xsl:if>
         </xsl:when>
         <xsl:when test="contains(.,',')">
            <!-- guessing already in proper last,-first format -->
            <xsl:value-of select="."/>
         </xsl:when>
         <xsl:otherwise>
            <!-- auto flip -->
            <xsl:apply-templates select="." mode="autoflipName"/>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <xsl:template match="*" mode="autoflipName">
      <xsl:variable name="split">
         <xsl:call-template name="splitname">
            <xsl:with-param name="name" select="."/>
            <xsl:with-param name="marker" select="']['"/>
         </xsl:call-template>
      </xsl:variable>

      <xsl:value-of select="substring-after($split,'][')"/>
      <xsl:value-of select="', '"/>
      <xsl:value-of select="substring-before($split,'][')"/>
   </xsl:template>

   <xsl:template name="lastword">
      <xsl:param name="text"/>
      <xsl:param name="delim" select="' '"/>

      <xsl:variable name="txt" select="normalize-space($text)"/>

      <xsl:choose>
         <xsl:when test="contains($txt, $delim)">
            <xsl:call-template name="lastword">
               <xsl:with-param name="text"
                               select="substring-after($txt, $delim)"/>
               <xsl:with-param name="delim" select="$delim"/>
            </xsl:call-template>
         </xsl:when>
         <xsl:otherwise><xsl:value-of select="$txt"/></xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <xsl:template name="countwords">
      <xsl:param name="text"/>
      <xsl:param name="delim" select="' '"/>
      <xsl:param name="count" select="0"/>

      <xsl:variable name="txt" select="normalize-spaces($text)"/>

      <xsl:choose>
         <xsl:when test="contains($txt, $delim)">
            <xsl:call-template name="lastword">
               <xsl:with-param name="text"
                               select="substring-after($txt, $delim)"/>
               <xsl:with-param name="delim" select="$delim"/>
               <xsl:with-param name="count" select="$count+1"/>
            </xsl:call-template>
         </xsl:when>
         <xsl:otherwise><xsl:value-of select="$count"/></xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <xsl:template name="splitname">
      <xsl:param name="name"/>
      <xsl:param name="sur"/>
      <xsl:param name="delim" select="' '"/>
      <xsl:param name="marker" select="']['" />

      <xsl:variable name="fn" select="normalize-space($name)"/>
      <xsl:variable name="ln" select="normalize-space($sur)"/>

      <xsl:choose>
         <xsl:when test="contains($fn, $delim)">
           <xsl:variable name="back">
              <xsl:call-template name="lastword">
                 <xsl:with-param name="text" select="$fn"/>
              </xsl:call-template>
           </xsl:variable>

           <xsl:choose>
              <xsl:when test="string-length($ln)=0">
                 <xsl:call-template name="splitname">
                    <xsl:with-param name="name"
                                    select="substring-before($fn, 
                                                         concat($delim,$back))"/>
                    <xsl:with-param name="sur" select="$back"/>
                    <xsl:with-param name="delim" select="$delim"/>
                    <xsl:with-param name="marker" select="$marker"/>
                 </xsl:call-template>
              </xsl:when>
              <xsl:when test="contains('abcdefghijklmnopqrstuvwxyz',
                                       substring($back,1,1))">
                 <!-- last word preceded by non-capitalized word; include
                      it as part of the last name -->
                 <xsl:call-template name="splitname">
                    <xsl:with-param name="name"
                                    select="substring-before($fn, 
                                                         concat($delim,$back))"/>
                    <xsl:with-param name="sur"
                                    select="concat($back,$delim,$ln)"/>
                    <xsl:with-param name="delim" select="$delim"/>
                    <xsl:with-param name="marker" select="$marker"/>
                 </xsl:call-template>
              </xsl:when>
              <xsl:otherwise>
                 <xsl:value-of select="concat($fn,$marker,$ln)"/>
              </xsl:otherwise>
           </xsl:choose>
         </xsl:when>
         <xsl:when test="string-length($ln)=0">
            <xsl:value-of select="concat($marker,$fn)"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:value-of select="concat($fn,$marker,$ln)"/>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <xsl:template name="getidscheme">
      <xsl:param name="pid"/>
      <xsl:variable name="id" select="normalize-space($pid)"/>
      <xsl:choose>
         <xsl:when test="starts-with($id,'doi:') or 
                         starts-with($id,'http://doi.org/')">DOI</xsl:when>
         <xsl:when test="contains($id,'ark:') or 
                         contains($id,'ARK:')">ARK</xsl:when>
         <xsl:when test="starts-with($id,'orcid:') or 
                         starts-with($id,'ORCID:') or 
                         starts-with($id,'http://orchid.org/')">ORCID</xsl:when>
         <xsl:when test="starts-with($id,'isni:') or 
                         starts-with($id,'ISNI:') or 
                         contains($id,'isni.org/')">ISNI</xsl:when>
         <xsl:when test="starts-with($id,'hdl:') or 
                         starts-with($id,'HDL:') or 
                         contains($id,'handle.net/')">HDL</xsl:when>
         <xsl:when test="starts-with($id,'http:') or 
                         starts-with($id,'https:')">URL</xsl:when>
         <xsl:when test="starts-with($id,'ivo:')">IVOID</xsl:when>
         <xsl:otherwise>unknown</xsl:otherwise>
      </xsl:choose>
   </xsl:template>

   <xsl:template name="getiduri">
      <xsl:param name="id"/>
      <xsl:choose>
         <xsl:when test="$id='HDL'">http://handle.net</xsl:when>
         <xsl:when test="$id='DOI'">http://doi.org</xsl:when>
         <xsl:when test="$id='ORCID'">http://orcid.org</xsl:when>
         <xsl:when test="$id='ISNI'">http://www.isni.org</xsl:when>
         <xsl:otherwise></xsl:otherwise>
      </xsl:choose>
   </xsl:template>

</xsl:stylesheet>
