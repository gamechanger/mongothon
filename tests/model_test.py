from mongothon import create_model
import unittest
from mock import Mock, ANY, call
from mongothon import Document
from mongothon import Schema
from mongothon.validators import one_of
from bson import ObjectId

car_schema = Schema({
    "make":                 {"type": basestring, "required": True},
    "model":                {"type": basestring, "required": True},
    "trim":                 {"type": Schema({
        "ac":               {"type": bool, "default": True},
        "doors":            {"type": int, "required": True, "default": 4}
    }), "required": True},
    "wheels":   [Schema({
        "position":         {"type": basestring, "required": True, "validates": one_of('FR', 'FL', 'RR', 'RL')},
        "tire":             {"type": basestring},
        "diameter":         {"type": int}
    })],
    "options": [basestring]
})

def set_description(value, doc):
    doc.make, doc.model = value.split(' ')

car_schema.virtual("description", 
    getter=lambda doc: "%s %s" % (doc.make, doc.model),
    setter=set_description)


doc = {
    "make":     "Peugeot",
    "model":    "406",
    "trim":     {
        "ac":       False,
        "doors":    5
    },
    "wheels":   [
        {
            "position": "FR",
            "tire":     "Pirelli",
            "diameter": 22
        },
        {
            "position": "FL",
            "tire":     "Pirelli",
            "diameter": 22
        },
        {
            "position": "RR",
            "tire":     "Michelin",
            "diameter": 24
        },
        {
            "position": "RL",
            "tire":     "Michelin",
            "diameter": 24
        }
    ],
    "options": ['heated seats', 'leather steering wheel']
}


class FakeCursor(object):
    def __init__(self, contents):
        self._contents = contents
        self._next = 0

    def __getitem__(self, index):
        return self._contents[index]

    def __getattr__(self, name):
        def return_self(*args, **kwargs):
            return self

        if name in ['rewind', 'clone', 'add_option', 'remove_option',
                    'limit', 'batch_size', 'skip', 'max_scan', 'sort',
                    'hint', 'where']:
            return return_self

    def __iter__(self):
        return self

    def next(self):
        if self._next >= len(self._contents):
            raise StopIteration

        self._next += 1
        return self._contents[self._next - 1]

    def count(self):
        return len(self._contents)


class TestModel(unittest.TestCase):

    def setUp(self):
        self.mock_collection = Mock()
        self.Car = create_model(car_schema, self.mock_collection)
        self.car = self.Car(doc)

    def test_can_be_treated_as_a_dict(self):
        self.assertIsInstance(self.car, dict)
        self.car['make'] = 'volvo'
        self.assertEquals('volvo', self.car['make'])

    def test_can_be_treated_as_a_document(self):
        self.assertIsInstance(self.car, Document)
        self.car['make'] = 'volvo'
        self.assertEquals('volvo', self.car.make)

    def test_validation_of_valid_doc(self):
        self.car.validate()

    def test_validation_respects_defaults(self):
        # this would cause validation to fail without a default being applied
        del self.car.trim['doors']
        self.car.validate()

    def test_validation_does_not_apply_defaults_to_instance(self):
        del self.car.trim['doors']
        self.car.validate()
        self.assertFalse('doors' in self.car.trim)

    def test_apply_defaults(self):
        del self.car.trim['doors']
        self.car.apply_defaults()
        self.assertEquals(4, self.car.trim.doors)

    def test_save_applies_defaults(self):
        del self.car.trim['doors']
        self.car.save()
        self.assertEqual(4, self.car.trim.doors)

    def test_save_rolls_back_defaults_if_save_fails(self):
        del self.car.trim['doors']
        self.mock_collection.save = Mock(side_effect=Exception('IO error'))
        try:
            self.car.save()
        except:
            self.assertFalse('doors' in self.car.trim)

    def test_save_passes_arguments_to_collection(self):
        self.car.save(manipulate=False, safe=True, check_keys=False)
        self.mock_collection.save.assert_called_with(ANY, manipulate=False, safe=True, check_keys=False)

    def test_delete_document(self):
        oid = ObjectId()
        self.car._id = oid
        self.car.delete()
        self.mock_collection.remove.assert_called_with(oid)

    def test_insert(self):
        self.Car.insert(doc)
        self.mock_collection.insert.assert_called_with(doc)

    def test_update(self):
        self.Car.update({'make': 'Peugeot'}, {'model': '106'}, upsert=True)
        self.mock_collection.update.assert_called_with({'make': 'Peugeot'}, {'model': '106'}, upsert=True)

    def test_count(self):
        self.mock_collection.count.return_value = 45
        self.assertEquals(45, self.Car.count())

    def test_find_one(self):
        self.mock_collection.find_one.return_value = doc
        loaded_car = self.Car.find_one({'make': 'Peugeot'})
        self.assertEquals(doc, loaded_car)
        self.mock_collection.find_one.assert_called_with({'make': 'Peugeot'})

    def test_find(self):
        cursor = FakeCursor([{'make': 'Peugeot', 'model': '405'}, {'make': 'Peugeot', 'model': '205'}])
        self.mock_collection.find.return_value = cursor
        cars = self.Car.find({'make': 'Peugeot'}, limit=2)
        self.assertIsInstance(cars[0], self.Car)
        self.assertEqual(2, cars.count())
        for car in cars:
            self.assertIsInstance(car, self.Car)

    def test_find_by_id(self):
        self.mock_collection.find_one.return_value = doc
        oid = ObjectId()
        loaded_car = self.Car.find_by_id(str(oid))
        self.assertEquals(doc, loaded_car)
        self.mock_collection.find_one.assert_called_with({'_id': oid})

    def assert_returns_wrapped_cursor(self, attr_name):
        cursor = FakeCursor([{'make': 'Peugeot', 'model': '405'}, {'make': 'Peugeot', 'model': '205'}])
        self.mock_collection.find.return_value = cursor
        cars = getattr(self.Car.find({'make': 'Peugeot'}), attr_name)()
        self.assertIsInstance(cars[0], self.Car)

    def test_limit_cursor(self):
        self.assert_returns_wrapped_cursor('limit')

    def test_rewind_cursor(self):
        self.assert_returns_wrapped_cursor('rewind')

    def test_clone_cursor(self):
        self.assert_returns_wrapped_cursor('clone')

    def test_add_option_cursor(self):
        self.assert_returns_wrapped_cursor('add_option')

    def test_remove_option_cursor(self):
        self.assert_returns_wrapped_cursor('remove_option')

    def test_batch_size_cursor(self):
        self.assert_returns_wrapped_cursor('batch_size')

    def test_skip_cursor(self):
        self.assert_returns_wrapped_cursor('skip')

    def test_max_scan_cursor(self):
        self.assert_returns_wrapped_cursor('max_scan')

    def test_sort_cursor(self):
        self.assert_returns_wrapped_cursor('sort')

    def test_hint_cursor(self):
        self.assert_returns_wrapped_cursor('hint')

    def test_where_cursor(self):
        self.assert_returns_wrapped_cursor('where')

    def call_tracker(self, **kwargs):
        tracker = Mock()
        for key, value in kwargs.iteritems():
            setattr(tracker, key, value)
        return tracker

    def test_before_save_middleware(self):
        middleware = Mock()
        tracker = self.call_tracker(middleware=middleware, collection=self.mock_collection)
        self.Car.before_save(middleware)
        self.car.save()
        self.assertEquals([call.middleware(self.car), call.collection.save(self.car)], tracker.mock_calls)

    def test_after_save_middleware(self):
        middleware = Mock()
        tracker = self.call_tracker(middleware=middleware, collection=self.mock_collection)
        self.Car.after_save(middleware)
        self.car.save()
        self.assertEquals([call.collection.save(self.car), call.middleware(self.car)], tracker.mock_calls)

    def test_before_validate_middleware(self):
        middleware = Mock()
        car_schema.validate = Mock()
        tracker = self.call_tracker(middleware=middleware, validate=car_schema.validate)
        self.Car.before_validate(middleware)
        self.car.validate()
        self.assertEquals([call.middleware(self.car), call.validate(self.car)], tracker.mock_calls)

    def test_after_validate_middleware(self):
        middleware = Mock()
        car_schema.validate = Mock()
        tracker = self.call_tracker(middleware=middleware, validate=car_schema.validate)
        self.Car.after_validate(middleware)
        self.car.validate()
        self.assertEquals([call.validate(self.car), call.middleware(self.car)], tracker.mock_calls)

    def test_virtual_field_getter(self):
        self.assertEquals('Peugeot 406', self.car.description)

    def test_virtual_field_setter(self):
        self.car.description = "Volvo S60"
        self.assertEquals('Volvo', self.car.make)
        self.assertEquals('S60', self.car.model)

