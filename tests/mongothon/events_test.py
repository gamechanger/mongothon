from mongothon.events import EventHandlerRegistrar
from mock import Mock
import unittest


class TestEventHandlerRegistrar(unittest.TestCase):
    def setUp(self):
        self.registrar = EventHandlerRegistrar()

    def test_applies_registered_handler(self):
        handler = Mock()
        document = Mock()
        self.registrar.register('save', handler)
        self.registrar.apply('save', document)
        handler.assert_called_once_with(document)

    def test_applies_only_handler_registered_for_event(self):
        save_handler = Mock()
        remove_handler = Mock()
        document = Mock()
        self.registrar.register('save', save_handler)
        self.registrar.register('remove', remove_handler)
        self.registrar.apply('save', document)
        save_handler.assert_called_once_with(document)
        self.assertEquals(0, remove_handler.call_count)

    def test_applies_all_registered_handlers_in_order(self):
        def get_handler(num):
            """Creates a event func which adds a number to the doc's invoked list."""
            def fn(doc):
                doc['invoked'].append(num)
            return fn

        self.registrar.register('save', get_handler(1))
        self.registrar.register('save', get_handler(2))
        self.registrar.register('save', get_handler(3))
        document = {'invoked': []}
        self.registrar.apply('save', document)
        self.assertEquals([1, 2, 3], document['invoked'])

    def test_handles_events_with_no_registered_handler(self):
        self.registrar.apply('save', {})

    def test_double_registered_event_called_only_once(self):
        handler = Mock()
        document = Mock()
        self.registrar.register('save', handler)
        self.registrar.register('save', handler)
        self.registrar.apply('save', document)
        handler.assert_called_once_with(document)

