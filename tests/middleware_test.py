from middleware import MiddlewareRegistrar
from mock import Mock
import unittest


class TestMiddlewareRegistrar(unittest.TestCase):
    def setUp(self):
        self.registrar = MiddlewareRegistrar()

    def test_applies_registered_middleware(self):
        middleware = Mock()
        document = Mock()
        self.registrar.register('save', middleware)

        self.registrar.apply('save', document)

        middleware.assert_called_once_with(document)

    def test_applies_only_middleware_registered_for_event(self):
        save_middleware = Mock()
        remove_middleware = Mock()
        document = Mock()
        self.registrar.register('save', save_middleware)
        self.registrar.register('remove', remove_middleware)

        self.registrar.apply('save', document)

        save_middleware.assert_called_once_with(document)
        self.assertEquals(0, remove_middleware.call_count)

    def test_applies_all_registered_middleware_in_order(self):
        def get_middleware(num):
            """Creates a middleware func which adds a number to the doc's invoked list."""
            def fn(doc):
                doc['invoked'].append(num)
            return fn

        self.registrar.register('save', get_middleware(1))
        self.registrar.register('save', get_middleware(2))
        self.registrar.register('save', get_middleware(3))
        document = {'invoked': []}

        self.registrar.apply('save', document)

        self.assertEquals([1, 2, 3], document['invoked'])

    def test_handles_events_with_no_registered_middleware(self):
        self.registrar.apply('save', {})


        
