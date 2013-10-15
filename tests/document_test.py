from mongothon import Document
import unittest

class TestDocument(unittest.TestCase):

    def _get_document(self):
        spec = {
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
            ],
            "tags": ["recipe", "cookies"]
        }

        return Document(spec)

    def test_create_with_invalid_key_names(self):
        with self.assertRaises(Exception):
            Document({'contains space': 34})

        with self.assertRaises(Exception):
            Document({'': 45})

    def test_creates_nested_document_tree(self):
        document = self._get_document()
        self.assertIsInstance(document['content'], Document)
        self.assertIsInstance(document['comments'][0], Document)

