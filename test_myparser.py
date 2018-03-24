# encoding=utf-8
import unittest
import myparser
import re
import sys
from contextlib import contextmanager
from StringIO import StringIO


@contextmanager
def mock_sysout():
    try:
        out, sys.stdout = sys.stdout, StringIO()
        yield sys.stdout
    finally:
        sys.stdout = out


class MyParserTest(unittest.TestCase):

    def test_xsd_init_failed(self):
        with self.assertRaises(myparser.MyXmlParserXSDInitExc):
            with myparser.MyXmlParser('file1.xml', 'file1.xsd') as p:
                pass

    def test_xml_load_failed(self):
        with self.assertRaises(myparser.MyXmlParserXmlParseExc):
            with myparser.MyXmlParser('file1.xml') as p:
                pass

    def test_xml_root_element(self):
        with myparser.MyXmlParser('xml/example1.xml') as p:
            self.assertEqual(p.root().name, 'shopcart')

    def test_xml_xpath(self):  
        for f in ['xml/example1.xml', 'xml/example2.xml']:
            with myparser.MyXmlParser(f) as p:
                node_f = lambda node: (node.name, node.getContent())
                self.assertEqual(
                    [node_f(n) for n in p.xpath('//item/desc')],
                    [('desc', 'LED TV Somsang TV123'), ('desc', 'WiFi Router 良好的網絡')]
                )

                node_f = lambda node: (node.name, node.getContent(), node.prop('cur'))
                self.assertEqual(
                    [node_f(n) for n in p.xpath('//item/price')],
                    [('price', '500', 'USD'), ('price', '30.00', 'EUR')]
                )

    def test_node2str(self):
        for f in ['xml/example1.xml', 'xml/example2.xml']:
            with myparser.MyXmlParser(f) as p:
                node = p.xpath('//item[@uid="2"]')
                self.assertEqual(len(node), 1)
                self.assertEqual(
                    ''.join(re.split('\n\s+', p.node2str(node[0]))),
                    '<item uid="2"><id>ABCD1235</id><desc>WiFi Router 良好的網絡</desc>'
                    '<quantity>1</quantity><price cur="EUR">30.00</price></item>'
                )

    def test_xml_tree(self):
        for f in ['xml/example1.xml', 'xml/example2.xml']:
            with myparser.MyXmlParser(f) as p:
                node = p.xpath('//item[@uid="2"]')
                self.assertEqual(len(node), 1)
                with mock_sysout() as s_out:
                    p.tree(node[0])
                    self.assertEqual(
                        ''.join(s_out.getvalue().split('\n')),
                        '<item> [element]{0}text [text]{0}<id> [element]{1}text [text]{0}text [text]{0}'
                        '<desc> [element]{1}text [text]{0}text [text]{0}<quantity> [element]{1}text [text]'
                        '{0}text [text]{0}<price> [element]{1}text [text]{0}text [text]'.format(
                            ' ' * 4, ' ' * 8,
                        )
                    )

    def test_xsd_validation(self):
        for f in ['xml/example1.xml', 'xml/example2.xml']:
            try:
                with myparser.MyXmlParser(f, 'xml/example.xsd'):
                    pass
            except Exception as ex:
                # Check that no one exception occurs
                self.assertTrue(False)

        # All files passed
        self.assertTrue(True)

        # Check XSD fail
        with self.assertRaises(myparser.MyXmlParserXsdValidationExc) as exc:
            with myparser.MyXmlParser('xml/example3.xml', 'xml/example.xsd'):
                pass

        self.assertEqual(exc.exception.message['warnings'], [])
        self.assertEqual(
            exc.exception.message['errors'],
            [
                "Element 'shopcart': The attribute 'orderid' is required but missing.\n",
                "Element 'item': The attribute 'uid' is required but missing.\n",
                "Element 'price', attribute 'foo': The attribute 'foo' is not allowed.\n",
                "Element 'price': The attribute 'cur' is required but missing.\n",
                "Element 'quantity': This element is not expected. Expected is ( desc ).\n",
                "Element 'foo': This element is not expected. Expected is ( item ).\n"
            ]
        )


if __name__ == '__main__':
    unittest.main()
