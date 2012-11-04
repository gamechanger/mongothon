from mongothon.validators import one_of, gte, lte, gt, lt, between, length, match, is_email, is_url
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


class TestLen(unittest.TestCase):
    def setUp(self):
        self.validator = length(3, 5)

    def test_valid(self):
        self.assertIsNone(self.validator('abc'))
        self.assertIsNone(self.validator('abcd')
        self.assertIsNone(self.validator('abcde'))

    def test_invalid(self):
        self.assertEqual('String must be at least 3 characters in length', self.validator('ab'))
        self.assertEqual('String must be at most 5 characters in length', self.validator('abcdef'))
        
    def test_max_length_with_keyword(self):
        validator = length(max=5)
        self.assertIsNone(validator('abcde'))
        self.assertEqual('String must be at most 5 characters in length', validator('abcdef'))


class TestMatch(unittest.TestCase):
    def setUp(self):
        self.validator = match("^[a-z]+$")

    def test_valid(self):
        self.assertIsNone(self.validator('abcde'))

    def test_invalid(self):
        self.assertEqual("String must match regex", self.validator('ABCde'))


class TestIsEmail(unittest.TestCase):
    def setUp(self):
        self.validator = is_email()

    def test_valid(self):
        self.assertIsNone(self.validator('s.balmer@hotmail.com'))

    def test_invalid(self):
        self.assertEqual(
            "notanemail is not a valid email address", 
            self.validator("notanemail"))


class TestIsUrl(unittest.TestCase):
    def setUp(self):
        self.validator = is_url()

    def test_valid(self):
        self.assertIsNone(self.validator('http://www.github.com'))

    def test_invalid(self):
        self.assertEqual(
            "notaurl is not a valid URL", 
            self.validator("notaurl"))
