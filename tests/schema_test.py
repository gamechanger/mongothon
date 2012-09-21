from schema import Schema, ValidationException
from validators import one_of
import unittest

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


        
