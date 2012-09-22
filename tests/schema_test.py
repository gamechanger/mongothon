from schema import Schema, ValidationException, SchemaFormatException
from validators import one_of, lte, gte
import unittest
from datetime import datetime

comment = Schema({
    "commenter":    {"type": basestring, "required": True},
    "email":        {"type": basestring, "required": False},
    "comment":      {"type": basestring, "required": True},
})


blog_post = Schema({
    "author":   {"type": basestring, "required": True},
    "content":  {"type": Schema({
        "title":        {"type": basestring, "required": True},
        "text":         {"type": basestring, "required": True},
    }), "required": True},
    "category": {"type": basestring, "validates":one_of("cooking", "politics")},
    "comments": [comment]
})

class SchemaVerification(unittest.TestCase):

    def assert_spec_invalid(self, spec, path):
        with self.assertRaises(SchemaFormatException) as cm:
            Schema(spec).verify()
        self.assertEqual(path, cm.exception.path)


    def test_requires_field_spec_dict(self):
        self.assert_spec_invalid({"author": 45}, 'author')
        
    def test_missing_type(self):
        self.assert_spec_invalid({"author": {}}, 'author')

    def test_type_not_supported(self):
        self.assert_spec_invalid({"author": {'type':tuple}}, 'author')

    def test_supported_types(self):
        field_types = [basestring, int, long, float, bool, datetime]
        for field_type in field_types:
            Schema({'some_field': {"type":field_type}}).verify()
            
    def test_required_should_be_a_boolean(self):
        self.assert_spec_invalid(
            {
                "author": {'type':int ,'required':23}
            }, 
            'author')

    def test_single_validation_function(self):
        Schema({'some_field': {'type':int, "validates":one_of(['a', 'b'])}}).verify()

    def test_multiple_validation_functions(self):
        Schema({'some_field': {'type':int, "validates":[gte(1), lte(10)]}}).verify()

    def test_invalid_validation(self):
        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":'wrong'}},
            'some_field')      

    def test_invalid_validation_in_validation_list(self):
        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":[gte(1), 'wrong']}},
            'some_field')  

    def test_unsupported_keys(self):
        self.assert_spec_invalid(
            {
                "somefield": {"type":int, "something":"wrong"},
                "otherfield": {"type":int}
            }, 
            'somefield')

    def test_valid_schema_with_nesting(self):
        blog_post.verify()

    def test_unsupported_type_in_nested_schema(self):
        self.assert_spec_invalid(
            {
                "content": {'type': Schema({
                    "somefield" : {"type": tuple}
                })}
            },
            'content.somefield')

    def test_invalid_nested_collection_with_multiple_schemas(self):
        self.assert_spec_invalid(
            {
                "items": [Schema({"somefield" : {"type": int}}), Schema({"other" : {"type": int}})]
            },
            'items')

    def test_unsupported_type_in_nested_collection(self):
        self.assert_spec_invalid(
            {
                "items": [Schema({"somefield" : {"type": tuple}})]
            },
            'items.somefield')


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.document = {
            "author": "John Humphreys",
            "content": {
                "title": "How to make cookies",
                "text": "First start by pre-heating the oven..."
            },
            "category": "cooking",
            "comments": [
                {
                    "commenter": "Julio Cesar",
                    "email": "jcesar@test.com",
                    "comment": "Great post dude!"
                },
                {
                    "commenter": "Michael Andrews",
                    "comment": "My wife loves these."
                }
            ]
        }

    def assert_document_paths_invalid(self, document, paths):
        with self.assertRaises(ValidationException) as cm:
            blog_post.validate(document)
        self.assertListEqual(paths, cm.exception.errors.keys())

    def test_valid_document(self):
        blog_post.validate(self.document)

    def test_missing_required_field(self):
        del self.document['author']
        self.assert_document_paths_invalid(self.document, ['author'])
        
    def test_incorrect_type(self):
        self.document['author'] = 33
        self.assert_document_paths_invalid(self.document, ['author'])
        
    def test_missing_embedded_document(self):
        del self.document['content']
        self.assert_document_paths_invalid(self.document, ['content'])

    def test_missing_required_field_in_embedded_document(self):
        del self.document['content']['title']
        self.assert_document_paths_invalid(self.document, ['content.title'])

    def test_missing_required_field_in_embedded_collection(self):
        del self.document['comments'][0]['commenter']
        self.assert_document_paths_invalid(self.document, ['comments.0.commenter'])

    def test_multiple_missing_fields(self):
        del self.document['content']['title']
        del self.document['comments'][1]['commenter']
        del self.document['author']
        self.assert_document_paths_invalid(
            self.document, 
            ['content.title', 'comments.1.commenter', 'author'])

    def test_validation_failure(self):
        self.document['category'] = 'gardening' #invalid category
        self.assert_document_paths_invalid(self.document, ['category'])


        
