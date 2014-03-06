from mongothon.document import Document, DocumentList
import pickle
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

    def test_changed(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.changed)
        doc['a'] = 'e'
        self.assertEqual({'a': 'e'}, doc.changed)
        self.assertEqual({}, doc.added)
        self.assertEqual({}, doc.deleted)

    def test_changed_exposes_wrapped_value(self):
        doc = Document({'a': {'c': 'd'}})
        self.assertEqual({}, doc.changed)
        doc['a'] = {'e': 'f'}
        self.assertEqual({'a': {'e': 'f'}}, doc.changed)
        self.assertIsInstance(doc.changed['a'], Document)

    def test_changed_ignores_noop(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.changed)
        doc['a'] = 'b'
        self.assertEqual({}, doc.changed)
        self.assertEqual({}, doc.added)
        self.assertEqual({}, doc.deleted)

    def test_changed_keeps_original_previous_value(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.changed)
        doc['a'] = 'e'
        doc['a'] = 'f'
        self.assertEqual({'a': ('b', 'f')}, doc.changes)
        self.assertEqual({}, doc.added)
        self.assertEqual({}, doc.deleted)

    def test_changed_ignores_resetting_original_value(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.changed)
        doc['a'] = 'e'
        doc['a'] = 'b'
        self.assertEqual({}, doc.changed)
        self.assertEqual({}, doc.added)
        self.assertEqual({}, doc.deleted)

    def test_ignores_del_then_add_same_field(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.changed)
        del doc['a']
        doc['a'] = 'b'
        self.assertEqual({}, doc.changed)
        self.assertEqual({}, doc.added)
        self.assertEqual({}, doc.deleted)

    def test_del_then_add_same_field_with_different_value_is_a_change(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.changed)
        del doc['a']
        doc['a'] = 'e'
        self.assertEqual({'a': 'e'}, doc.changed)
        self.assertEqual({}, doc.added)
        self.assertEqual({}, doc.deleted)

    def test_add_then_del_field(self):
        doc = Document({'c': 'd'})
        self.assertEqual({}, doc.changed)
        doc['a'] = 'b'
        del doc['a']
        self.assertEqual({}, doc.changed)
        self.assertEqual({}, doc.added)
        self.assertEqual({}, doc.deleted)

    def test_change_then_del_field(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.changed)
        doc['a'] = 'e'
        del doc['a']
        self.assertEqual({}, doc.changed)
        self.assertEqual({}, doc.added)
        self.assertEqual({'a': 'b'}, doc.deleted)

    def test_changes(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.changes)
        doc['a'] = 'e'
        self.assertEqual({'a': ('b', 'e')}, doc.changes)

    def test_added(self):
        doc = Document({'a': 'b'})
        self.assertEqual({}, doc.added)
        doc['c'] = 'd'
        doc['a'] = 'e'
        self.assertEqual({'c': 'd'}, doc.added)
        self.assertEqual({'a': 'e'}, doc.changed)

    def test_add_then_change(self):
        doc = Document({'a': 'b'})
        self.assertEqual({}, doc.added)
        doc['c'] = 'd'
        doc['c'] = 'e'
        self.assertEqual({'c': 'e'}, doc.added)
        self.assertEqual({}, doc.changed)
        self.assertEqual({}, doc.deleted)


    def test_deleted(self):
        doc = Document({'a': 'b', 'c': 'd'})
        self.assertEqual({}, doc.deleted)
        del doc['c']
        doc['a'] = 'e'
        self.assertEqual({'c': 'd'}, doc.deleted)

    def test_reset_all_changes(self):
        doc = Document({
            'a': 'b',
            'c': 'd',
            'e': [
                {'f': 'g'},
                {'h': 'i'}
            ]
        })
        doc['a'] = 'j'
        doc['e'].append({'k': 'l'})
        doc['e'][0]['f'] = 'm'
        self.assertTrue(doc.changed)
        self.assertTrue(doc['e'][0].changed)
        doc.reset_all_changes()
        self.assertEquals({}, doc.changed)
        self.assertEquals({}, doc['e'][0].changed)
        self.assertEquals({}, doc.deleted)

    def test_pickleable(self):
        doc = Document({
            'a': 'b',
            'c': 'd',
            'e': [
                {'f': 'g'},
                {'h': 'i'}
            ]
        })
        codeced = pickle.loads(pickle.dumps(doc))
        self.assertEquals(doc, codeced)
        self.assertFalse(codeced.added)
        self.assertFalse(codeced.changed)
        self.assertFalse(codeced.deleted)

    def test_to_dict(self):
        doc = Document({
            'a': 'b',
            'c': 'd',
            'e': [
                {'f': 'g'},
                {'h': 'i'}
            ]
        })
        output = doc.to_dict()
        self.assertEquals(doc, output)
        self.assertIsInstance(output, dict)
        self.assertIsInstance(output['e'], list)
        self.assertIsInstance(output['e'][0], dict)
        self.assertNotIsInstance(output, Document)
        self.assertNotIsInstance(output['e'], DocumentList)
        self.assertNotIsInstance(output['e'][0], Document)



class TestDocumentList(unittest.TestCase):
    def test_equals_list(self):
        dlist = DocumentList(['a', 'b'])
        self.assertEquals(['a', 'b'], dlist)

    def test_set_item(self):
        dlist = DocumentList(['a', 'b'])
        dlist[1] = 'c'
        self.assertEquals(['a', 'c'], dlist)

    def test_set_slice(self):
        dlist = DocumentList(['a', 'b', 'c', 'd'])
        dlist[1:3] = ['e', 'f']
        self.assertEquals(['a', 'e', 'f', 'd'], dlist)

    def test_wraps_dicts_in_document(self):
        dlist = DocumentList([{'a': 'b'}, {'a': 'c'}])
        self.assertIsInstance(dlist[0], Document)

    def test_extend(self):
        dlist = DocumentList([{'a': 'b'}, {'a': 'c'}])
        dlist.extend([{'a': 'd'}, {'a': 'e'}])
        self.assertIsInstance(dlist[3], Document)
        self.assertEquals(dlist, [{'a': 'b'}, {'a': 'c'}, {'a': 'd'}, {'a': 'e'}])

    def test_append(self):
        dlist = DocumentList([{'a': 'b'}, {'a': 'c'}])
        dlist.append({'a': 'd'})
        self.assertIsInstance(dlist[2], Document)
        self.assertEquals(dlist, [{'a': 'b'}, {'a': 'c'}, {'a': 'd'}])

    def test_insert(self):
        dlist = DocumentList([{'a': 'b'}, {'a': 'c'}])
        dlist.insert(1, {'a': 'd'})
        self.assertIsInstance(dlist[1], Document)
        self.assertEquals(dlist, [{'a': 'b'}, {'a': 'd'}, {'a': 'c'}])

    def test_remove(self):
        dlist = DocumentList([{'a': 'b'}, {'a': 'c'}])
        dlist.remove({'a': 'b'})
        self.assertEquals(dlist, [{'a': 'c'}])

    def test_pop(self):
        dlist = DocumentList([{'a': 'b'}, {'a': 'c'}])
        dlist.pop()
        self.assertEquals(dlist, [{'a': 'b'}])

    def test_pop_with_index(self):
        dlist = DocumentList([{'a': 'b'}, {'a': 'c'}])
        dlist.pop(0)
        self.assertEquals(dlist, [{'a': 'c'}])

