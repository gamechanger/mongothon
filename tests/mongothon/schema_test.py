from mongothon.schema import Schema, IndexSpec
from mock import Mock
import unittest

class TestSchema(unittest.TestCase):
    def test_indexes(self):
        Schema({}, indexes=[IndexSpec('myindex', [('key', 1)])])
