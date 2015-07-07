from mongothon.schema import Schema
from mock import Mock
import unittest

class TestSchema(unittest.TestCase):
    def test_indexes(self):
        Schema({}, indexes=[{'name': 'myindex', 'key': 'foo'}])
