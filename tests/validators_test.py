from validators import one_of
import unittest

class TestOneOf(unittest.TestCase):
    def setUp(self):
        self.validator = one_of('peas', 'carrots')

    def test_valid(self):
        self.assertIsNone(self.validator('peas'))
        self.assertIsNone(self.validator('carrots'))
        
    def test_invalid(self):
        self.assertIs(
            "'sweetcorn' is not in the list ('peas', 'carrots')", 
            self.validator('sweetcorn'))
