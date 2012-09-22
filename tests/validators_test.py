from validators import one_of, gte, lte
import unittest

class TestOneOf(unittest.TestCase):
    def setUp(self):
        self.validator = one_of('peas', 'carrots')

    def test_valid(self):
        self.assertIsNone(self.validator('peas'))
        self.assertIsNone(self.validator('carrots'))
        
    def test_invalid(self):
        self.assertEqual(
            "'sweetcorn' is not in the list ('peas', 'carrots')", 
            self.validator('sweetcorn'))

class TestGte(unittest.TestCase):
    def setUp(self):
        self.validator = gte(3)

    def test_valid(self):
        self.assertIsNone(self.validator(3))
        self.assertIsNone(self.validator(4))
        
    def test_invalid(self):
        self.assertEqual(
            "2 is less than the minimum value of 3", 
            self.validator(2))

class TestLte(unittest.TestCase):
    def setUp(self):
        self.validator = lte(3)

    def test_valid(self):
        self.assertIsNone(self.validator(3))
        self.assertIsNone(self.validator(2))
        
    def test_invalid(self):
        self.assertEqual(
            "4 is greater than the maximum value of 3", 
            self.validator(4))