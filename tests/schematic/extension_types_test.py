from schematic.extension_types import Mixed
import unittest

class TestMixedType(unittest.TestCase):
    def test_instance_requires_at_least_two_types(self):
        with self.assertRaises(Exception):
            Mixed(int)
        Mixed(int, basestring)

    def test_is_instance(self):
        mixed = Mixed(int, basestring)
        self.assertIsInstance("test", mixed)

    def test_is_not_instance(self):
        mixed = Mixed(int, basestring)
        self.assertNotIsInstance(123.45, mixed)


