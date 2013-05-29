from mongothon import Schema
from mongothon.schema import ValidationException, SchemaFormatException, Mixed
from mongothon.validators import one_of, lte, gte
import unittest
from mock import patch
from datetime import datetime
from sample import blog_post_schema, name_schema, stubnow, valid_doc
from bson.objectid import ObjectId

class TestSchemaVerificationTest(unittest.TestCase):

    def assert_spec_invalid(self, spec, path):
        for strict in [True, False]:
            with self.assertRaises(SchemaFormatException) as cm:
                Schema(spec, strict).verify()
            self.assertEqual(path, cm.exception.path)

    def test_requires_field_spec_dict(self):
        self.assert_spec_invalid({"author": 45}, 'author')

    def test_missing_type(self):
        self.assert_spec_invalid({"author": {}}, 'author')

    def test_type_not_supported(self):
        self.assert_spec_invalid({"author": {'type':tuple}}, 'author')

    def test_supported_types(self):
        field_types = [ObjectId, basestring, int, long, float, bool, datetime, Mixed, Mixed(int, ObjectId)]
        for field_type in field_types:
            Schema({'some_field': {"type":field_type}}).verify()

    def test_required_should_be_a_boolean(self):
        self.assert_spec_invalid(
            {
                "author": {'type': int, 'required': 23}
            },
            'author')

    def test_single_validation_function(self):
        Schema({'some_field': {'type':int, "validates":one_of(['a', 'b'])}}).verify()

    def test_multiple_validation_functions(self):
        Schema({'some_field': {'type':int, "validates":[gte(1), lte(10)]}}).verify()

    def test_invalid_validation(self):
        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":'wrong'}},
            'some_field')

    def test_invalid_validation_in_validation_list(self):
        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":[gte(1), 'wrong']}},
            'some_field')

    def test_incorrect_validator_arg_spec(self):
        def bad_validator():
            pass

        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":bad_validator}},
            'some_field')

        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":[bad_validator, gte(1)]}},
            'some_field')

    def test_unsupported_keys(self):
        self.assert_spec_invalid(
            {
                "somefield": {"type":int, "something":"wrong"},
                "otherfield": {"type":int}
            },
            'somefield')

    def test_default_value_of_correct_type(self):
        Schema({'num_wheels':{'type':int, 'default':4}}).verify()

    def test_default_value_of_incorrect_type(self):
        self.assert_spec_invalid(
            {'num_wheels':{'type':int, 'default':'wrong'}},
            'num_wheels')

    def test_default_value_accepts_function(self):
        def default_fn():
            return 4

        Schema({'num_wheels':{'type':int, 'default':default_fn}}).verify()


    def test_valid_schema_with_nesting(self):
        blog_post_schema.verify()

    def test_unsupported_type_in_nested_schema(self):
        self.assert_spec_invalid(
            {
                "content": {'type': Schema({
                    "somefield": {"type": tuple}
                })}
            },
            'content.somefield')

    def test_invalid_nested_collection_with_multiple_schemas(self):
        self.assert_spec_invalid(
            {
                "items": [Schema({"somefield": {"type": int}}), Schema({"other": {"type": int}})]
            },
            'items')

    def test_unsupported_type_in_nested_collection(self):
        self.assert_spec_invalid(
            {
                "items": [Schema({"somefield": {"type": tuple}})]
            },
            'items.somefield')

    def test_nested_schema_cannot_have_default(self):
        self.assert_spec_invalid(
            {
                "content": {'type': Schema({
                    "somefield": {"type": int}
                }), "default": {}}
            },
            'content')

    def test_nested_collection_of_ints(self):
        Schema({
            "numbers": [int]
        }).verify()


    @patch('logging.warning')
    def test_strict_mode_off_allows_fields_not_in_schema(self, warning):
        schema = Schema({'expected_field': {'type': int}}, strict=False)
        schema.validate({'unexpected_field': 44})
        warning.assert_called_once_with('Unexpected document field not present in schema: unexpected_field')


class TestMixedType(unittest.TestCase):
    def test_instance_requires_at_least_two_types(self):
        with self.assertRaises(Exception):
            Mixed(int)
        Mixed(int, basestring)

    def test_instance_only_accepts_valid_types(self):
        with self.assertRaises(Exception):
            Mixed(int, set)

    def test_matches_enclosed_type(self):
        mixed = Mixed(int, basestring)
        self.assertTrue(
            mixed.is_instance_of_enclosed_type("test"))
        self.assertFalse(
            mixed.is_instance_of_enclosed_type(123.45))


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.document = valid_doc()

    def assert_document_paths_invalid(self, document, paths):
        with self.assertRaises(ValidationException) as cm:
            blog_post_schema.validate(document)
        self.assertListEqual(paths, cm.exception.errors.keys())

    def test_valid_document(self):
        blog_post_schema.validate(self.document)

    def test_missing_required_field(self):
        del self.document['author']
        self.assert_document_paths_invalid(self.document, ['author'])

    def test_incorrect_type(self):
        self.document['author'] = 33
        self.assert_document_paths_invalid(self.document, ['author'])

    def test_mixed_type(self):
        self.document['misc'] = "a string"
        blog_post_schema.validate(self.document)
        self.document['misc'] = 32
        blog_post_schema.validate(self.document)

    def test_mixed_type_instance_incorrect_type(self):
        self.document['linked_id'] = 123.45
        self.assert_document_paths_invalid(self.document, ['linked_id'])

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

    def test_embedded_collection_item_of_incorrect_type(self):
        self.document['tags'].append(55)
        self.assert_document_paths_invalid(self.document, ['tags.3'])

    def test_validation_failure(self):
        self.document['category'] = 'gardening'  # invalid category
        self.assert_document_paths_invalid(self.document, ['category'])

    def test_disallows_fields_not_in_schema(self):
        self.document['something'] = "extra"
        self.assert_document_paths_invalid(self.document, ['something'])


class TestDefaultApplication(unittest.TestCase):
    def setUp(self):
        self.document = {
            "author": {
                "first":    "John",
                "last":     "Humphreys"
            },
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

    def test_apply_default_function(self):
        blog_post_schema.apply_defaults(self.document)
        self.assertEqual(stubnow(), self.document['creation_date'])

    def test_apply_default_value(self):
        blog_post_schema.apply_defaults(self.document)
        self.assertEqual(0, self.document['likes'])

    def test_apply_default_value_in_nested_document(self):
        blog_post_schema.apply_defaults(self.document)
        self.assertEqual(1, self.document['content']['page_views'])

    def test_apply_default_value_in_nested_collection(self):
        blog_post_schema.apply_defaults(self.document)
        self.assertEqual(0, self.document['comments'][0]['votes'])
        self.assertEqual(0, self.document['comments'][1]['votes'])

    def test_default_value_does_not_overwrite_existing(self):
        self.document['likes'] = 35
        self.document['creation_date'] = datetime(1980, 5, 3)
        blog_post_schema.apply_defaults(self.document)
        self.assertEqual(35, self.document['likes'])
        self.assertEqual(datetime(1980, 5, 3), self.document['creation_date'])


class TestVirtualFieldDefinition(unittest.TestCase):
    def test_virtual_getter(self):
        name_schema.virtual("full_name_schema",
            getter=lambda doc: "%s %s" % (doc['first'], doc['last']))
        doc = {"first": "John", "last": "Smith"}
        self.assertTrue(name_schema.virtuals['full_name_schema'].has_getter())
        self.assertEqual("John Smith", name_schema.virtuals['full_name_schema'].on_get(doc))

    def test_field_getter_redefinition(self):
        name_schema.virtual("full_name_schema", getter=lambda doc: "%s %s" % (doc['last'], doc['first']))
        name_schema.virtual("full_name_schema", getter=lambda doc: "%s %s" % (doc['first'], doc['last']))
        doc = {"first": "John", "last": "Smith"}
        self.assertTrue(name_schema.virtuals['full_name_schema'].has_getter())
        self.assertEqual("John Smith", name_schema.virtuals['full_name_schema'].on_get(doc))

    def test_virtual_setter(self):
        def full_name_schema_setter(value, doc):
            doc['first'] = value.split(' ')[0]
            doc['last'] = value.split(' ')[1]
        name_schema.virtual("full_name_schema", setter=full_name_schema_setter)
        doc = {"first": "John", "last": "Smith"}
        self.assertTrue(name_schema.virtuals['full_name_schema'].has_setter())
        name_schema.virtuals['full_name_schema'].on_set("Bob Jones", doc)
        self.assertEqual("Bob", doc['first'])
        self.assertEqual("Jones", doc['last'])

    def test_setter_redefinition(self):
        def backward_setter(value, doc):
            doc['last'] = value.split(' ')[0]
            doc['first'] = value.split(' ')[1]

        def full_name_schema_setter(value, doc):
            doc['first'] = value.split(' ')[0]
            doc['last'] = value.split(' ')[1]

        name_schema.virtual("full_name_schema", setter=backward_setter)
        name_schema.virtual("full_name_schema", setter=full_name_schema_setter)
        doc = {"first": "John", "last": "Smith"}
        name_schema.virtuals['full_name_schema'].on_set("Bob Jones", doc)
        self.assertEqual("Bob", doc['first'])
        self.assertEqual("Jones", doc['last'])

    def test_detects_invalid_getter_signature(self):
        def getter_no_args():
            pass

        def getter_two_args(romy, michelle):
            pass

        self.assertRaises(ValueError, name_schema.virtual, "thing", getter=getter_no_args)
        self.assertRaises(ValueError, name_schema.virtual, "thing", getter=getter_two_args)

    def test_detects_invalid_setter_signature(self):
        def setter_one_arg(maverick):
            pass

        def setter_three_args(good, bad, ugly):
            pass

        self.assertRaises(ValueError, name_schema.virtual, "thing", setter=setter_one_arg)
        self.assertRaises(ValueError, name_schema.virtual, "thing", setter=setter_three_args)

