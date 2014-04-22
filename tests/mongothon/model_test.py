from mongothon import create_model
from pickle import dumps, loads
from unittest import TestCase
from mock import Mock, ANY, call
from mongothon import Document, Schema, NotFoundException, Array
from mongothon.validators import one_of
from mongothon.scopes import STANDARD_SCOPES
from bson import ObjectId
from copy import deepcopy
from .fake import FakeCursor

car_schema = Schema({
    "make":                 {"type": basestring, "required": True},
    "model":                {"type": basestring, "required": True},
    "trim":                 {"type": Schema({
        "ac":                   {"type": bool, "default": True},
        "doors":                {"type": int, "required": True, "default": 4}
    }), "required": True},
    "wheels":               {"type": Array(Schema({
        "position":         {"type": basestring, "required": True, "validates": one_of('FR', 'FL', 'RR', 'RL')},
        "tire":             {"type": basestring},
        "diameter":         {"type": int}
    }))},
    "options":              {"type": Array(basestring)}
})


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

# This has to live here so pickle can find it.
mock_collection = Mock()
mock_collection.name = "pickleable"
Pickleable = create_model(Mock(), mock_collection)


class TestModel(TestCase):

    def setUp(self):
        self.mock_collection = Mock()
        self.mock_collection.name = "car"
        self.Car = create_model(car_schema, self.mock_collection)
        self.car = self.Car(doc)

    def tearDown(self):
        self.Car.remove_all_handlers()

    def assert_predicates(self, model, is_new=False, is_persisted=False, is_deleted=False):
        self.assertEquals(is_new, model.is_new())
        self.assertEquals(is_persisted, model.is_persisted())
        self.assertEquals(is_deleted, model.is_deleted())

    def test_class_module_is_that_of_caller(self):
        self.assertEqual(self.Car.__module__, 'tests.mongothon.model_test')

    def test_class_is_pickleable(self):
        pickled = dumps(Pickleable)
        unpickled = loads(pickled)
        self.assertEqual(unpickled, Pickleable)

    def test_class_name_defaults_to_camelcased_collection_name(self):
        mock_collection = Mock()
        mock_collection.name = "some_model"
        SomeModel = create_model(Schema({}), mock_collection)
        self.assertEquals("SomeModel", SomeModel.__name__)

    def test_class_name_can_be_overridden(self):
        mock_collection = Mock()
        mock_collection.name = "some_model"
        SomeModel = create_model(Schema({}), mock_collection, "SomethingElse")
        self.assertEquals("SomethingElse", SomeModel.__name__)

    def test_can_be_treated_as_a_dict(self):
        self.assertIsInstance(self.car, dict)
        self.car['make'] = 'volvo'
        self.assertEquals('volvo', self.car['make'])

    def test_can_be_treated_as_a_document(self):
        self.assertIsInstance(self.car, Document)
        self.car['make'] = 'volvo'
        self.assertEquals('volvo', self.car['make'])

    def test_instantiate(self):
        self.assert_predicates(self.car, is_new=True)

    def test_validation_of_valid_doc(self):
        self.car.validate()

    def test_validation_respects_defaults(self):
        # this would cause validation to fail without a default being applied
        del self.car['trim']['doors']
        self.car.validate()

    def test_validation_does_not_apply_defaults_to_instance(self):
        del self.car['trim']['doors']
        self.car.validate()
        self.assertFalse('doors' in self.car['trim'])

    def test_apply_defaults(self):
        del self.car['trim']['doors']
        self.car.apply_defaults()
        self.assertEquals(4, self.car['trim']['doors'])

    def test_save_applies_defaults(self):
        del self.car['trim']['doors']
        self.car.save()
        self.assertEqual(4, self.car['trim']['doors'])

    def test_save_rolls_back_defaults_if_save_fails(self):
        del self.car['trim']['doors']
        self.mock_collection.save = Mock(side_effect=Exception('IO error'))
        try:
            self.car.save()
        except:
            self.assertFalse('doors' in self.car['trim'])

    def test_save_passes_arguments_to_collection(self):
        self.car.save(manipulate=False, safe=True, check_keys=False)
        self.mock_collection.save.assert_called_with(ANY, manipulate=False, safe=True, check_keys=False)

    def test_save_changes_state_to_persisted(self):
        self.car.save()
        self.assert_predicates(self.car, is_persisted=True)

    def test_save_resets_change_tracking(self):
        self.car['trim']['ac'] = True
        self.car['make'] = 'Rover'
        self.car.save()
        self.assertFalse(self.car['trim'].changed)
        self.assertFalse(self.car.changed)

    def test_remove(self):
        oid = ObjectId()
        self.car['_id'] = oid
        self.car.remove()
        self.mock_collection.remove.assert_called_with(oid)
        self.assert_predicates(self.car, is_deleted=True)

    def test_insert(self):
        self.Car.insert(doc)
        self.mock_collection.insert.assert_called_with(doc)

    def test_update_instance(self):
        oid = ObjectId()
        self.car['_id'] = oid
        self.car.save()
        self.car.update_instance({'model': '106'})
        self.assert_predicates(self.car, is_persisted=True)
        self.mock_collection.update.assert_called_with(
            {'_id': oid}, {'model': '106'})

    def test_update_on_instance(self):
        oid = ObjectId()
        self.car['_id'] = oid
        self.car.update({'model': '106'})
        self.assertFalse(self.mock_collection.called)
        self.assertEqual(self.car['model'], '106')

    def test_update_on_class(self):
        oid = ObjectId()
        self.car['_id'] = oid
        self.car.save()
        self.Car.update({'_id': oid}, {'model': '106'})
        self.assert_predicates(self.car, is_persisted=True)
        self.mock_collection.update.assert_called_with(
            {'_id': oid}, {'model': '106'})

    def test_count(self):
        self.mock_collection.count.return_value = 45
        self.assertEquals(45, self.Car.count())

    def test_find_one(self):
        self.mock_collection.find_one.return_value = doc
        loaded_car = self.Car.find_one({'make': 'Peugeot'})
        self.assertEquals(doc, loaded_car)
        self.assert_predicates(loaded_car, is_persisted=True)
        self.mock_collection.find_one.assert_called_with({'make': 'Peugeot'})

    def test_find(self):
        cursor = FakeCursor([{'make': 'Peugeot', 'model': '405'}, {'make': 'Peugeot', 'model': '205'}])
        self.mock_collection.find.return_value = cursor
        cars = self.Car.find({'make': 'Peugeot'}, limit=2)
        self.assertIsInstance(cars[0], self.Car)
        self.assertEqual(2, cars.count())
        for car in cars:
            self.assert_predicates(car, is_persisted=True)
            self.assertIsInstance(car, self.Car)

    def test_find_with_iterator_protocol(self):
        cursor = FakeCursor([{'make': 'Peugeot', 'model': '405'}, {'make': 'Peugeot', 'model': '205'}])
        self.mock_collection.find.return_value = cursor
        cars = self.Car.find({'make': 'Peugeot'}, limit=2)
        iter1 = cars.__iter__()
        iter2 = cars.__iter__()
        self.assertIsInstance(iter1.next(), self.Car)
        self.assertIsInstance(iter2.next(), self.Car)
        self.assertIsInstance(iter1.next(), self.Car)
        self.assertIsInstance(iter2.next(), self.Car)


    def test_find_by_id(self):
        self.mock_collection.find_one.return_value = doc
        oid = ObjectId()
        loaded_car = self.Car.find_by_id(oid)
        self.assertEquals(doc, loaded_car)
        self.assert_predicates(loaded_car, is_persisted=True)
        self.mock_collection.find_one.assert_called_with({'_id': oid})

    def test_find_by_id_handles_integer_id(self):
        self.mock_collection.find_one.return_value = doc
        loaded_car = self.Car.find_by_id(33)
        self.assertEquals(doc, loaded_car)
        self.assert_predicates(loaded_car, is_persisted=True)
        self.mock_collection.find_one.assert_called_with({'_id': 33})

    def test_find_by_id_handles_oid_as_string(self):
        self.mock_collection.find_one.return_value = doc
        oid = ObjectId()
        loaded_car = self.Car.find_by_id(str(oid))
        self.assertEquals(doc, loaded_car)
        self.assert_predicates(loaded_car, is_persisted=True)
        self.mock_collection.find_one.assert_called_with({'_id': oid})

    def test_find_by_id_missing_record(self):
        """Test that find_by_id throws a NotFoundException if the requested record does not exist"""
        self.mock_collection.find_one.return_value = None
        with self.assertRaises(NotFoundException):
            self.Car.find_by_id(ObjectId())


    def test_find_by_id_handles_non_oid_string_id(self):
        self.mock_collection.find_one.return_value = doc
        loaded_car = self.Car.find_by_id("bob")
        self.assertEquals(doc, loaded_car)
        self.assert_predicates(loaded_car, is_persisted=True)
        self.mock_collection.find_one.assert_called_with({'_id': "bob"})

    def test_reload(self):
        updated_doc = deepcopy(doc)
        updated_doc['make'] = 'Volvo'
        self.mock_collection.find_one.side_effect = [doc, updated_doc]
        oid = ObjectId()
        car = self.Car.find_by_id(str(oid))
        car['_id'] = oid
        car.reload()
        self.assertEquals(updated_doc, car)
        self.mock_collection.find_one.assert_has_calls([
            call({'_id': oid}), call({'_id': oid})])

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
        """Groups together mocks for the purpose of tracking the
        order of calls across all of those mocks."""
        tracker = Mock()
        for key, value in kwargs.iteritems():
            setattr(tracker, key, value)
        return tracker

    def test_will_save_event(self):
        handler = Mock()
        tracker = self.call_tracker(handler=handler, collection=self.mock_collection)
        self.Car.on('will_save', handler)
        self.car.save()
        self.assertEquals([call.handler(self.car), call.collection.save(self.car)], tracker.mock_calls)

    def test_did_save_event(self):
        handler = Mock()
        tracker = self.call_tracker(handler=handler, collection=self.mock_collection)
        self.Car.on('did_save', handler)
        self.car.save()
        self.assertEquals([call.collection.save(self.car), call.handler(self.car)], tracker.mock_calls)

    def test_changes_available_to_did_save_event_handler(self):
        inner = Mock()
        def handler(car):
            self.assertTrue(car.changed)
            self.assertEqual({'ac': True}, car['trim'].changed)
            self.assertEqual({}, car['trim'].added)
            self.assertEquals({'diameter': (22, 23)}, car['wheels'][0].changes)
            inner()

        self.Car.on('did_save', handler)
        self.car['make'] = 'Rover'
        self.car['trim']['ac'] = True
        self.car['wheels'][0]['diameter'] = 23
        self.car.save()
        inner.assert_called_once_with()

    def test_changes_available_to_will_validate_event_handler(self):
        inner = Mock()
        def handler(car):
            self.assertTrue(car.changed)
            self.assertIn('ac', car['trim'].changed)
            self.assertEqual({}, car['trim'].added)
            self.assertEquals({'diameter': (22, 23)}, car['wheels'][0].changes)
            self.assertIsInstance(car, self.Car)
            inner()

        self.Car.on('will_validate', handler)
        self.car['make'] = 'Rover'
        self.car['trim']['ac'] = True
        self.car['wheels'][0]['diameter'] = 23
        self.car.save()
        inner.assert_called_once_with()

    def test_will_validate_event(self):
        handler = Mock()
        car_schema.validate = Mock()
        tracker = self.call_tracker(handler=handler, validate=car_schema.validate)
        self.Car.on('will_validate', handler)
        self.car.validate()
        self.assertEquals([call.handler(self.car), call.validate(self.car)], tracker.mock_calls)

    def test_did_validate_event(self):
        handler = Mock()
        car_schema.validate = Mock()
        tracker = self.call_tracker(handler=handler, validate=car_schema.validate)
        self.Car.on('did_validate', handler)
        self.car.validate()
        self.assertEquals([call.validate(self.car), call.handler(self.car)], tracker.mock_calls)

    def test_did_init_event(self):
        handler = Mock()
        self.Car.on('did_init', handler)
        car = self.Car()
        handler.assert_called_once_with(car)

    def test_will_update_event(self):
        handler = Mock()
        self.Car.on('will_update', handler)
        self.car['_id'] = 'abc'
        self.car.update_instance({"$set": {"somefield": "somevalue"}}, safe=True)
        handler.assert_called_once_with(self.car, {"$set": {"somefield": "somevalue"}}, safe=True)

    def test_did_update_event(self):
        handler = Mock()
        self.Car.on('did_update', handler)
        self.car['_id'] = 'abc'
        self.car.update_instance({"$set": {"somefield": "somevalue"}}, safe=True)
        handler.assert_called_once_with(self.car, {"$set": {"somefield": "somevalue"}}, safe=True)

    def test_will_remove_event(self):
        handler = Mock()
        self.Car.on('will_remove', handler)
        self.car['_id'] = 'abc'
        self.car.remove(True, j=True)
        handler.assert_called_once_with(self.car, True, j=True)

    def test_did_remove_event(self):
        handler = Mock()
        self.Car.on('did_remove', handler)
        self.car['_id'] = 'abc'
        self.car.remove(True, j=True)
        handler.assert_called_once_with(self.car, True, j=True)

    def test_will_apply_defaults_event(self):
        handler = Mock()
        self.Car.on('will_apply_defaults', handler)
        self.car.apply_defaults()
        handler.assert_called_once_with(self.car)

    def test_did_apply_defaults_event(self):
        handler = Mock()
        self.Car.on('did_apply_defaults', handler)
        self.car.apply_defaults()
        handler.assert_called_once_with(self.car)

    def test_did_find_event(self):
        handler = Mock()
        self.Car.on('did_find', handler)
        cursor = FakeCursor([{'make': 'Peugeot', 'model': '405'}, {'make': 'Peugeot', 'model': '205'}])
        self.mock_collection.find.return_value = cursor
        cars = self.Car.find({'make': 'Peugeot'}, limit=2)
        self.assertEqual([call(cars[0]), call(cars[1])], handler.mock_calls)

    def test_will_reload_event(self):
        handler = Mock()
        self.car['_id'] = ObjectId()
        self.Car.on('will_reload', handler)
        doc = {'make': 'Peugeot', 'model': '405'}
        self.mock_collection.find_one.return_value = doc
        self.car.reload()
        handler.assert_called_once_with(self.car)

    def test_did_reload_event(self):
        handler = Mock()
        self.car['_id'] = ObjectId()
        self.Car.on('did_reload', handler)
        doc = {'make': 'Peugeot', 'model': '405'}
        self.mock_collection.find_one.return_value = doc
        self.car.reload()
        handler.assert_called_once_with(self.car)

    def test_did_find_event_not_fire_for_simple_init(self):
        handler = Mock()
        self.Car.on('did_find', handler)
        self.Car()
        self.assertFalse(handler.called)

    def test_register_event_handler_with_decorator(self):
        stub = Mock()

        @self.Car.on('did_init')
        def func(*args, **kwargs):
            stub(*args, **kwargs)

        car = self.Car()
        stub.assert_called_once_with(car)

    def test_on_decorator_with_other_decorators(self):
        outer_decorator = Mock()

        @outer_decorator
        @self.Car.on('did_init')
        def func(*args, **kwargs):
            pass

        outer_decorator.assert_called_once_with(ANY)
        self.assertTrue(callable(outer_decorator.call_args[0][0]))

    def test_emit_custom_event(self):
        handler = Mock()
        self.Car.on('fruit_explosion', handler)
        self.car.emit('fruit_explosion', 'apples', other_fruit='oranges')
        handler.assert_called_once_with(self.car, 'apples', other_fruit='oranges')

    def test_remove_handler(self):
        handler = Mock()
        self.Car.on('did_init', handler)
        self.Car.remove_handler('did_init', handler)
        self.Car()
        self.assertEquals(0, handler.call_count)

    def test_remove_all_handlers(self):
        handler = Mock()
        self.Car.on('did_init', handler)
        self.Car.remove_all_handlers()
        self.Car()
        self.assertEquals(0, handler.call_count)

    def test_handlers(self):
        handler = Mock()
        self.Car.on('did_init', handler)
        self.assertEquals([handler], self.Car.handlers('did_init'))

    def test_different_classes_managed_their_own_handlers(self):
        CarA = create_model(car_schema, Mock())
        CarB = create_model(car_schema, Mock())
        handler = Mock()
        CarA.on('did_save', handler)
        self.assertEquals([], CarB.handlers('did_save'))

    def test_class_method_registration(self):
        response = Mock()

        @self.Car.class_method
        def find_by_make(Car, make):
            self.assertEquals(Car, self.Car)
            self.assertEquals("Peugeot", make)
            return response

        self.assertEquals(response, self.Car.find_by_make("Peugeot"))

    def test_class_method_registration_with_other_decorators(self):
        outer_decorator = Mock()

        @outer_decorator
        @self.Car.class_method
        def find_by_make(Car, make):
            pass

        outer_decorator.assert_called_once_with(ANY)
        self.assertTrue(callable(outer_decorator.call_args[0][0]))

    def test_instance_method_registration(self):
        response = Mock()

        @self.Car.instance_method
        def add_option(car, option):
            self.assertIsInstance(car, self.Car)
            self.assertEquals(option, "sunroof")
            return response

        car = self.Car(doc)
        self.assertEquals(response, car.add_option("sunroof"))

    def test_instance_method_registration_with_other_decorators(self):
        outer_decorator = Mock()

        @outer_decorator
        @self.Car.instance_method
        def add_option(car, option):
            pass

        outer_decorator.assert_called_once_with(ANY)
        self.assertTrue(callable(outer_decorator.call_args[0][0]))


    def test_scope_query(self):
        @self.Car.scope
        def with_ac(available=True):
            return {"trim.ac": available}

        @self.Car.scope
        def hatchback():
            return {"trim.doors": {"$in": [3, 5]}}, {}, {"sort": [("make", -1)]}

        cursor = FakeCursor([{'make': 'Peugeot', 'model': '405'}, {'make': 'Peugeot', 'model': '205'}])
        self.mock_collection.find.return_value = cursor
        cars = self.Car.hatchback().with_ac().where({'year': 2005})
        self.assertIsInstance(cars[0], self.Car)
        self.mock_collection.find.assert_called_once_with(
            {"trim.ac": True, "trim.doors": {"$in": [3, 5]}, "year": 2005},
            None,
            sort=[("make", -1)])
        self.assertEqual(2, cars.count())
        for car in cars:
            self.assertIsInstance(car, self.Car)

    def test_scope_with_other_decorator(self):
        outer_decorator = Mock()

        @outer_decorator
        @self.Car.scope
        def with_ac(available=True):
            return {"trim.ac": available}

        outer_decorator.assert_called_once_with(ANY)
        self.assertTrue(callable(outer_decorator.call_args[0][0]))

    def test_models_maintain_their_own_scope_lists(self):
        CarA = create_model(car_schema, Mock())
        CarB = create_model(car_schema, Mock())

        def scope_a():
            return {}

        def scope_b():
            return {}

        CarA.scope(scope_a)
        CarB.scope(scope_b)
        self.assertEquals(STANDARD_SCOPES + [scope_a], CarA.scopes)
        self.assertEquals(STANDARD_SCOPES + [scope_b], CarB.scopes)

