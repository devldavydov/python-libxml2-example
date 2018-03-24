import libxml2
import logging
import sys
from contextlib import contextmanager
from HTMLParser import HTMLParser


# logging init
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger(__name__)


# libxml2 init
def _libxml2_error_handler(ctxt, err):
    log.error('libxml2: %s %s', ctxt, err)

def _libxml2_entity_loader(url, id, ctxt):
    return None

libxml2.registerErrorHandler(_libxml2_error_handler, None)
libxml2.setEntityLoader(_libxml2_entity_loader)


# custom exceptions
class MyXmlParserBaseExc(Exception):
    """Base parser exception"""
    pass

class MyXmlParserXSDInitExc(MyXmlParserBaseExc):
    """XSD initialization exception"""
    pass

class MyXmlParserXmlParseExc(MyXmlParserBaseExc):
    """XML file parse exception"""
    pass

class MyXmlParserXsdValidationExc(MyXmlParserBaseExc):
    """XSD validation exception"""
    pass

class MyXmlParserXPathCtxtExc(MyXmlParserBaseExc):
    """XPath context exception"""
    pass


# parser
class MyXmlParser(object):
    """Example parser class"""

    def __init__(self, xml_file, xsd_file=None):
        """Constructor"""
        self.xml = xml_file
        self.xsd = xsd_file
        self.xsd_err_l = []
        self.xsd_wrn_l = []
        self.xml_doc = None

    def __enter__(self):
        """Parser context enter"""
        self.xsd = None if not self.xsd else self._init_xsd(self.xsd)
        self.xml_doc = self._parse()
        if self.xsd:
            self._validate()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Parser context exit"""
        if self.xml_doc:
            self.xml_doc.freeDoc()

    def _init_xsd(self, xsd_file):
        """XSD Schema initialization"""
        try:
            schema = libxml2.schemaNewParserCtxt(xsd_file).schemaParse().schemaNewValidCtxt()
            schema.setValidityErrorHandler(self._xsd_validation_err, self._xsd_validation_wrn)
            return schema
        except Exception as ex:
            log.error('XSD initialization failed')
            raise MyXmlParserXSDInitExc(ex)

    def _xsd_validation_err(self, msg, arg):
        """XSD validation error handler"""
        self.xsd_err_l.append(msg)

    def _xsd_validation_wrn(self, msg, arg):
        """XSD validation warning handler"""
        self.xsd_wrn_l.append(msg)

    def _parse(self):
        """Parse xml file"""
        try:
            with open(self.xml, 'r') as f:
                return libxml2.parseDoc(f.read())
        except Exception as ex:
            log.error('XML file parse error')
            raise MyXmlParserXmlParseExc(ex)

    def _validate(self):
        """Validate XML against XSD"""
        try:
            assert not self.xsd.schemaValidateDoc(self.xml_doc)     # success = 0
        except Exception as ex:
            log.error('XSD validation failed')
            raise MyXmlParserXsdValidationExc({'errors': self.xsd_err_l, 'warnings': self.xsd_wrn_l})

    @contextmanager
    def _xpath_ctxt(self):
        """XPath context wrapper"""
        ctxt = None
        try:
            ctxt = self.xml_doc.xpathNewContext()
            # ctxt.xpathRegisterNs('<namespace name>', '<namespace schema uri>')
            yield ctxt
        except Exception as ex:
            log.error('XPath context error', exc_info=True)
            raise MyXmlParserXPathCtxtExc(ex)
        finally:
            if ctxt:
                ctxt.xpathFreeContext()

    def root(self):
        """Return XML root element"""
        return self.xml_doc.getRootElement()

    def node2str(self, xml_node):
        """XML Node to string"""
        xml_str = HTMLParser().unescape(str(xml_node))
        return xml_str.encode('utf-8') if isinstance(xml_str, unicode) else xml_str

    def xpath(self, query):
        """XPath query"""
        with self._xpath_ctxt() as ctxt:
            return ctxt.xpathEval(query)

    def tree(self, xml_node, lpad=0):
        """Get recursive tree from node"""
        s = ' ' * lpad + ('<{0}>' if xml_node.type == 'element' else '{0}') + ' [{1}]'
        print s.format(xml_node.name, xml_node.type)

        chld = xml_node.children
        while chld is not None:
            self.tree(chld, lpad + 4)
            chld = chld.next
