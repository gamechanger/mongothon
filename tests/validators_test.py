from validators import one_of, gte, lte, gt, lt, between
import unittest


class TestOneOf(unittest.TestCase):
    def test_valid(self):
        self.validator = one_of('peas', 'carrots')
        self.assertIsNone(self.validator('peas'))
        self.assertIsNone(self.validator('carrots'))
        
    def test_invalid(self):
        self.validator = one_of('peas', 'carrots')
        self.assertEqual(
            "'sweetcorn' is not in the list ('peas', 'carrots')", 
            self.validator('sweetcorn'))

    def test_valid_array(self):
        self.validator = one_of(['peas', 'carrots'])
        self.assertIsNone(self.validator('peas'))
        self.assertIsNone(self.validator('carrots'))
        
    def test_invalid_array(self):
        self.validator = one_of(['peas', 'carrots'])
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


class TestBetween(unittest.TestCase):
    def setUp(self):
        self.validator = between(3, 5)

    def test_valid(self):
        self.assertIsNone(self.validator(3))
        self.assertIsNone(self.validator(4))
        self.assertIsNone(self.validator(5))
        
    def test_invalid(self):
        self.assertEqual(
            "6 is greater than the maximum value of 5", 
            self.validator(6))

        self.assertEqual(
            "2 is less than the minimum value of 3", 
            self.validator(2))


class TestGt(unittest.TestCase):
    def setUp(self):
        self.validator = gt(3)

    def test_valid(self):
        self.assertIsNone(self.validator(4))
        
    def test_invalid(self):
        self.assertEqual(
            "Value must be greater than 3", 
            self.validator(3))


class TestLt(unittest.TestCase):
    def setUp(self):
        self.validator = lt(3)

    def test_valid(self):
        self.assertIsNone(self.validator(2))
        
    def test_invalid(self):
        self.assertEqual(
            "Value must be less than 3", 
            self.validator(3))
