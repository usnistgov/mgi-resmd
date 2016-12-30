#! /usr/bin/python
#
"""
a script that reads an MSE vocabulary encoded in a Excel spreadsheet and writes
it out as an XML Schema.
"""
import openpyxl as xl
import os, sys
from argparse import ArgumentParser
from collections import OrderedDict

prog=None
description = \
"""convert an MSE vocabulary to an Excel spreadsheet"""

epilog=None

FORWARD = \
"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="{ns}" 
           xmlns="http://www.w3.org/2001/XMLSchema" 
           xmlns:xs="http://www.w3.org/2001/XMLSchema" 
           xmlns:tv="http://schema.nist.gov/xml/tieredvocab/1.0wd" 
           xmlns:vt="http://schema.nist.gov/xml/vocabtest" 
           xmlns:am="http://schema.nist.gov/xml/mgi.schema.annot" 
           elementFormDefault="unqualified" 
           attributeFormDefault="unqualified" version="{version}">

   <xs:import namespace="http://schema.nist.gov/xml/tieredvocab/1.0wd"
              schemaLocation="https://raw.githubusercontent.com/RayPlante/mgi-resmd/tieredvocab/schemas/xml/tiered-vocab.xsd"/>
"""

AFTERWARD = \
"""
</xs:schema>
"""

# This template must have one line with {value} in it
L2TYPE = \
"""
   <xs:simpleType name="{name}">
     <xs:restriction base="xs:token">
       <xs:enumeration value="{value}"/>
     </xs:restriction>
   </xs:simpleType>
"""

L1TYPE = \
"""
   <xs:complexType name="{name}">
     <xs:annotation>
       <xs:documentation>
         {lev1} vocabulary terms describing {prop}
       </xs:documentation>
     </xs:annotation>

     <xs:complexContent>
       <xs:restriction base="mse:{propName}">
         <xs:sequence>
           <xs:element name="t" type="mse:{propType}"
                       minOccurs="1" maxOccurs="1" fixed="{value}"/>
           <xs:element name="t2" type="mse:{lev1Type}"
                       minOccurs="0" maxOccurs="1"/>
         </xs:sequence>
       </xs:restriction>

     </xs:complexContent>
   </xs:complexType>
"""

L0TYPE = \
"""
   <xs:complexType name="{name}" abstract="true">
     <xs:annotation>
       <xs:documentation>
         a Property that captures {prop}
       </xs:documentation>
     </xs:annotation>

     <xs:complexContent>
       <xs:restriction base="tv:TwoTieredVocabulary">
         <xs:sequence>
           <xs:element name="t" type="mse:{propType}"
                       minOccurs="1" maxOccurs="1"/>
           <xs:element name="t2" type="xs:token"
                       minOccurs="0" maxOccurs="1"/>
         </xs:sequence>
       </xs:restriction>
     </xs:complexContent>
   </xs:complexType>
"""


if not prog:
    prog = os.path.basename(sys.argv[0])
    if prog.endswith(".py"):
        prog = prog[:-3]
if not prog:
    prog = "make_mse_vocab"

def define_opts(progname=None):

    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('file', metavar='VOCAB_XSL', type=str, nargs=1,
                        help="Excel file to convert")
    parser.add_argument('-v', '--set-version', type=str, dest='version',
                        help="set the version for the output schema")
    parser.add_argument('-c', '--use-camelcase', action='store_true',
                        dest='camel',
                        help="set the version for the output schema")
    parser.add_argument('-n', '--namespace', type=str, dest='ns', metavar='NS',
                        default='https://www.nist.gov/od/sch/mse-vocab/v1.0wd',
                        help='set the schema namespace to NS')
    return parser

def get_vocab_data(filename):
    wb = xl.load_workbook(filename=filename)
    return wb.get_sheet_by_name('Data')

class VocabFormatError(Exception):
    """
    an error indicating unexpected formatting in the input vocabulary file.
    """
    def __init__(self, msg=None, rowdata=None, lineno=None):
        self.row = rowdata
        self.lineno = lineno
        if not msg:
            msg = "Input spreadsheet formatting error" 
        super(self, VocabFormatError).__init__(msg)

    def __str__(self):
        msg = self.message
        if isinstance(self.lineno, int):
            msg += " at " + str(self.lineno)
        if self.rowdata is not None:
            msg += ":\n   " + str(self.rowdata)
        return msg

class TermSet(object):
    """
    a container for the set of terms that can be used to describe a Property
    """
    def __init__(self, lev1, lev0=None, lev2=None):
        self.label = lev1
        self.name = camel_case(lev1)
        self.prop = lev0
        self.lev2 = set()
        if lev2 is not None:
            self.add_subterm(lev2)

    def add_subterm(self, lev2):
        self.lev2.add(lev2)

def us_delim(term):
    return "_".join(term.split())

def camel_case(term):
    return "".join([word.capitalize() for word in term.split()])

class Property(object):
    """
    a set of vocabulary corresponding to a level-0 term.
    """
    def __init__(self, name, lev1=None, lev2=None):
        self.lev0 = name
        self.lev1 = {}

        if name.endswith('(s)'):
            name = name[:-3]
        self.name = camel_case(name)

        if lev1:
            self.add_term(lev1, lev2)
        elif lev2:
            raise VocabFormatError("Level 2 term is missing Level 1 parent")

    def add_term(self, lev1, lev2=""):
        if lev2 == ".":
            lev2 == ""
        if lev1 in self.lev1:
            self.lev1[lev1].add_subterm(lev2)
        else:
            self.lev1[lev1] = TermSet(lev1, self.lev0, self.lev2)

    def add_term_row(self, cells, lineno=None):
        try:
            self.add_term(cells[1], cells[2])
        except VocabFormatError, ex:
            ex.row = cells
            ex.lineno = lineno
            raise
    
def main(opts):

    ws = get_vocab_data(opts.file[0])

    # read in the data from the spreadsheet
    props = OrderedDict()
    line = 1
    for cells in ws.iter_rows():
        if len(cells) > 2:
            if cells[0] in props:
                prop = props[cells[0]]
            else:
                prop = Property(cells[0])
                props[cells[0]] = prop
            prop.add_term_row(cells, line)
        line += 1

    # write out schema
    write_forward(sys.stdout, {"tns": opts.ns, "version": opts.version})
    for prop in props.itervalues():
        write_prop(sys.stdout, prop)
    write_afterward(sys.stdout)

def write_forward(out, data):
    out.write(FORWARD.format(**data))

def write_afterward(out, data):
    out.write(AFTERWARD)

def write_prop(out, prop):
    out.write(prop.to_schema())

opts = None
if __name__ == '__main__':
    try:
        opts = define_opts(prog).parse_args(sys.argv[1:])
        main(opts)
    except RuntimeError, ex:
        sys.stderr.write("Error: "+str(ex))
