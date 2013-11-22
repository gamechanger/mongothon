from mongothon import Document
import unittest


class TestDocument(unittest.TestCase):

    def get_spec(self):
        return {
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

    def test_creates_nested_document_tree(self):
        document = Document(self.get_spec())
        self.assertIsInstance(document['content'], Document)
        self.assertIsInstance(document['comments'][0], Document)

    def test_reports_circular_references(self):
        spec = self.get_spec()
        spec['circular'] = spec
        with self.assertRaises(ValueError):
            Document(spec)

