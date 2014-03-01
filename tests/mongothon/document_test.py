from mongothon.document import Document, DocumentList
import unittest


class TestDocument(unittest.TestCase):

    def test_equals_dict(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEquals(doc, {'a': 'b', 'c': 'd'})

    def test_init_without_initial(self):
        doc = Document()
        self.assertEquals({}, doc)

    def test_set_get(self):
        doc = Document({'a': 'b'})
        self.assertEquals('b', doc['a'])
        doc['a'] = 'c'
        self.assertEquals('c', doc['a'])

    def test_update(self):
        doc = Document()
        doc.update({'a': 'b', 'c': 'd'})
        self.assertEquals({'a': 'b', 'c': 'd'}, doc)

    def test_setdefault(self):
        doc = Document({'a': 'b'})
        self.assertEquals(doc.setdefault('c', {'d': 'e'}), {'d': 'e'})
        self.assertIsInstance(doc['c'], Document)

    def test_init_with_nested_dict(self):
        doc = Document({'a': {'b': 'c'}})
        self.assertEquals({'a': {'b': 'c'}}, doc)
        self.assertIsInstance(doc['a'], Document)
        self.assertEquals(doc['a']['b'], 'c')

    def test_copies_initial_dict(self):
        spec = {'a': {'b': 'c'}}
        doc = Document(spec)
        spec['d'] = 'e'
        self.assertEquals({'a': {'b': 'c'}}, doc)

    def test_set_dict_as_item(self):
        doc = Document()
        doc['a'] = {'b': 'c'}
        self.assertEquals({'a': {'b': 'c'}}, doc)
        self.assertIsInstance(doc['a'], Document)
        self.assertEquals(doc['a']['b'], 'c')

    def test_init_with_nested_list_and_dict(self):
        doc = Document({'a': [{'b': 'c'}]})
        self.assertEquals({'a': [{'b': 'c'}]}, doc)
        self.assertIsInstance(doc['a'], DocumentList)
        self.assertIsInstance(doc['a'][0], Document)
        self.assertEquals(doc['a'][0]['b'], 'c')

    def test_append_dict_to_list(self):
        doc = Document({'a': []})
        doc['a'].append({'b': 'c'})
        self.assertEquals({'a': [{'b': 'c'}]}, doc)
        self.assertIsInstance(doc['a'][0], Document)
        self.assertEquals(doc['a'][0]['b'], 'c')

    def test_delete_from_document(self):
        doc = Document({'a': 'b', 'c': 'd'})
        del doc['c']
        self.assertEquals(doc, {'a': 'b'})

    def test_delete_from_document_list(self):
        doc = Document({'a': [{'b': 'c'}]})
        del doc['a'][0]
        self.assertEquals(doc, {'a': []})

    def test_extend_doc_list(self):
        doc = Document({'a': [{'b': 'c'}]})
        doc['a'].extend([{'d': 'e'}, {'f': 'g'}])
        self.assertEquals(doc, {'a': [{'b': 'c'}, {'d': 'e'}, {'f': 'g'}]})
        self.assertIsInstance(doc['a'][1], Document)
        self.assertIsInstance(doc['a'][2], Document)

    def test_doc_list_slice_assignment(self):
        doc = Document({'a': [{'b': 'c'}]})
        doc['a'][1:2] = [{'d': 'e'}, {'f': 'g'}]
        self.assertEquals(doc, {'a': [{'b': 'c'}, {'d': 'e'}, {'f': 'g'}]})
        self.assertIsInstance(doc['a'][1], Document)
        self.assertIsInstance(doc['a'][2], Document)

    def test_doc_list_insert(self):
        doc = Document({'a': [{'b': 'c'}, {'d': 'e'}]})
        doc['a'].insert(1, {'f': 'g'})
        self.assertEquals(doc, {'a': [{'b': 'c'}, {'f': 'g'}, {'d': 'e'}]})
        self.assertIsInstance(doc['a'][1], Document)
