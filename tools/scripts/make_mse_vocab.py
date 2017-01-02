#! /usr/bin/python
#
"""
a script that reads an MSE vocabulary encoded in a Excel spreadsheet and writes
it out as an XML Schema.
"""
import openpyxl as xl
import os, sys, re
from argparse import ArgumentParser
from collections import OrderedDict

prog=None
description = \
"""convert an MSE vocabulary to an Excel spreadsheet"""

epilog=None

FORWARD = \
"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="{tns}" 
           xmlns="http://www.w3.org/2001/XMLSchema" 
           xmlns:xs="http://www.w3.org/2001/XMLSchema" 
           xmlns:tv="http://schema.nist.gov/xml/tieredvocab/1.0wd" 
           xmlns:mse="{tns}"
           xmlns:am="http://schema.nist.gov/xml/mgi.schema.annot" 
           elementFormDefault="unqualified" 
           attributeFormDefault="unqualified" version="{version}">
"""

AFTERWARD = \
"""
</xs:schema>
"""

# This template must have one line with {value} in it
L2ENUM = \
 """ 
   <xs:simpleType name="{name}_{propName}">
     <xs:annotation>
       <xs:documentation>
         Allowed values for {lev1} vocabulary terms describing {prop}
       </xs:documentation>
     </xs:annotation>

     <xs:restriction base="mse:{propName}">
       <xs:enumeration value="{value}"/>
     </xs:restriction>
   </xs:simpleType>
 """

L0TYPE = \
"""
   <xs:simpleType name="{name}" abstract="true">
     <xs:annotation>
       <xs:documentation>
         a property that captures {prop} vocabulary
       </xs:documentation>
     </xs:annotation>
     <xs:restriction base="xs:token"/>
   </xs:simpleType>
"""


if not prog:
    prog = os.path.basename(sys.argv[0])
    if prog.endswith(".py"):
        prog = prog[:-3]
if not prog:
    prog = "make_mse_vocab"

def define_opts(progname=None):

    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('file', metavar='VOCAB_XLS', type=str, nargs=1,
                        help="Excel file to convert")
    parser.add_argument('-v', '--set-version', type=str, dest='version',
                        default='', help="set the version for the output schema")
    parser.add_argument('-c', '--use-camelcase', action='store_true',
                        dest='camel',
                        help="use camel case for generated type names")
    parser.add_argument('-n', '--namespace', type=str, dest='ns', metavar='NS',
                        default='https://www.nist.gov/od/sch/mse-vocab/1.0wd',
                        help='set the schema namespace to NS')
    parser.add_argument('-t', '--run-test', type=str, dest='test',metavar='TEST',
                        default=None, help='run the test named TEST')
    return parser

def get_vocab_data(filename):
    wb = xl.load_workbook(filename=filename)
    sheets = wb.get_sheet_names()
    if len(sheets) < 1:
        raise VocabFormatError("No sheets found in Excel spreadsheet")
    return wb.get_sheet_by_name(sheets[0])

class VocabFormatError(Exception):
    """
    an error indicating unexpected formatting in the input vocabulary file.
    """
    def __init__(self, msg=None, rowdata=None, lineno=None):
        self.row = rowdata
        self.lineno = lineno
        if not msg:
            msg = "Input spreadsheet formatting error" 
        super(VocabFormatError, self).__init__(msg)

    def __str__(self):
        msg = self.message
        if isinstance(self.lineno, int):
            msg += " at " + str(self.lineno)
        if self.row is not None:
            msg += ":\n   " + str([cell.value for cell in self.row[:3]])
        return msg

PAREN_RE = re.compile(r"[\(\)]")
OPENP_RE = re.compile(r"\(")
SLASH_RE = re.compile(r"/")
def us_delim(term):
    if term.endswith('(s)'):
        term = term[:-3]
    term = SLASH_RE.sub("", PAREN_RE.sub("", term))
    return "_".join(term.split())

def camel_case(term):
    if term.endswith('(s)'):
        term = term[:-3]
    term = SLASH_RE.sub("", PAREN_RE.sub("", OPENP_RE.sub("_", term)))
    return "".join([word.capitalize() for word in term.split()])

class TermSet(object):
    """
    a container for the set of terms that can be used to describe a Property
    """
    def __init__(self, lev1, lev0=None, lev2=None, to_name=us_delim):
        self.label = lev1
        self.lev1 = lev1
        if self.lev1.endswith('(s)'):
            self.lev1 = self.lev1[:-3]
        self.name = to_name(self.lev1)
        self.prop = lev0
        self.propName = to_name(self.prop)
        self.lev2 = []
        if lev2 is not None:
            self.add_subterm(lev2)

    def add_subterm(self, lev2):
        """
        add a new level-2 qualifying term
        """
        if lev2.endswith('(s)'):
            lev2 = lev2[:-3]
        if lev2 not in self.lev2:
            self.lev2.append(lev2)


    def to_enum_type(self, format, data=None):
        """
        create the xs:simpleType definition that captures the level 2 
        allowed values
        """
        if data is None:
            data = {}
        tdata = { "lev1": self.label, "name": self.name,
                  "prop": self.prop, "propName": self.propName }
        tdata.update(data)

        return make_enum_type(self.lev2, self.label, format, tdata)

def make_enum_type(terms, lev1, format, data):
    """
    create the xs:simpleType definition that captures the level 2 
    allowed values
    """

    # first extract the enumeration-{value} line
    lines = format.splitlines()
    enumline = filter(lambda n: "{value}" in n[1], enumerate(lines))
    if len(enumline) > 0:
        lineno = enumline[0][0]
        enumline = enumline[0][1]
        lines.pop(lineno)

        #
        elines = []
        for val in reversed(terms):
            edata = data.copy()
            if val:
                # format: "Thermodynamic: Melting temperature"
                edata['value'] = "{0}: {1}".format(lev1, val)
            else:
                # format: "Thermodynamic"
                edata['value'] = lev1
            lines.insert(lineno, enumline.format(**edata))
            
    format = "\n".join(lines)
    return format.format(**data)
                

class Property(object):
    """
    a set of vocabulary corresponding to a level-0 term.
    """
    # to_name = us_delim
    
    def __init__(self, name, lev1=None, lev2=None, to_name=us_delim):
        self.to_name = to_name
        self.prop = name
        self.lev1 = OrderedDict()

        if name.endswith('(s)'):
            name = name[:-3]
        self.name = to_name(name)

        if lev1:
            self.add_term(lev1, lev2)
        elif lev2:
            raise VocabFormatError("Level 2 term is missing Level 1 parent")

    def add_term(self, lev1, lev2=""):
        if lev2 == ".":
            lev2 = ""
        if lev1.endswith('(s)'):
            lev1 = lev1[:-3]
        if lev1 in self.lev1:
            self.lev1[lev1].add_subterm(lev2)
        else:
            self.lev1[lev1] = TermSet(lev1, self.prop, lev2, self.to_name)

    def add_term_row(self, row, lineno=None):
        cells = [cell.value for cell in row[:3]]
        if cells[2] is None:
            cells[2] = ""
        if len(filter(lambda c: c is None, cells)) > 0:
            raise VocabFormatError("Empty cells where data expected", row,lineno)
        cells = [cell.strip() for cell in cells]
        try:
            self.add_term(cells[1], cells[2])
        except VocabFormatError, ex:
            ex.row = row
            ex.lineno = lineno
            raise

    def to_prop_type(self, format, data=None):
        """
        create the base property xs:complexType
        """
        if data is None:
            data = {}
        tdata = { "name": self.name, "prop": self.prop, 
                  "propType": self.name }
        tdata.update(data)

        return format.format(**tdata)

    def write_schema(self, out):
        out.write(self.to_prop_type(L0TYPE))
        for key in self.lev1:
            out.write(self.lev1[key].to_enum_type(L2ENUM)) 
        
    
def main(opts):

    to_name = (opts.camel and camel_case) or us_delim
    ws = get_vocab_data(opts.file[0])

    # read in the data from the spreadsheet
    props = OrderedDict()
    line = 1
    for cells in ws.iter_rows():
        if len(cells) > 2 and cells[1].value is not None:
            if cells[0].value is None:
                raise VocabFormatError("Empty property name", cells, line)
            pname = cells[0].value.strip()
            if pname in props:
                prop = props[pname]
            else:
                prop = Property(pname, to_name=to_name)
                props[pname] = prop
            prop.add_term_row(cells, line)
        line += 1

    # write out schema
    write_schema_doc(sys.stdout, props,
                     {"tns": opts.ns, "version": opts.version})

def write_schema_doc(out, props, hdrdata):
    write_forward(out, hdrdata)
    for prop in props.itervalues():
        write_prop(out, prop)
    write_afterward(out, hdrdata)

def write_forward(out, data):
    out.write(FORWARD.format(**data))

def write_afterward(out, data):
    out.write(AFTERWARD.format(**data))

def write_prop(out, prop):
    prop.write_schema(out)

def test_termset_enum(opts):
    ts = TermSet("Ceramics", lev0="Material Type")
    ts.add_subterm("Perovskite")
    ts.add_subterm("")
    sys.stdout.write(ts.to_enum_type(L2ENUM, {"prop": "Material type"}))

def test_prop_type(opts):
    p = Property("Material Type")
    sys.stdout.write(p.to_prop_type(L0TYPE))

def test_to_schema(opts):
    p = Property("Material Type")
    p.add_term("Ceramics", ".")
    p.add_term("Ceramics", "Perovskite")
    p.add_term("Metals and alloys")
    p.add_term("Metamaterials")
    p.write_schema(sys.stdout)

def test_doc(opts):
    p = Property("Material Type")
    p.add_term("Ceramics", ".")
    p.add_term("Ceramics", "Perovskite")
    p.add_term("Metals and alloys")
    p.add_term("Metamaterials")
    write_schema_doc(sys.stdout, {p.prop: p},
                     {"tns": opts.ns, "version": opts.version})


test = { "termset_enum": test_termset_enum,
         "prop_type": test_prop_type,
         "schema": test_to_schema,
         "all": test_doc,
         "doc": test_doc
     }

if __name__ == '__main__':
    try:
        opts = define_opts(prog).parse_args(sys.argv[1:])
        if opts.test:
            try:
                test = test[opts.test]
            except KeyError, e:
                raise RuntimeError(opts.test + ": Not a recognized test")
            test(opts)
        else:
            main(opts)
    except (RuntimeError, VocabFormatError), ex:
        sys.stderr.write(prog+": "+str(ex)+"\n")
        sys.exit(1)
