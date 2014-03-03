from mongothon.events import EventHandlerRegistrar
from mock import Mock
import unittest


class TestEventHandlerRegistrar(unittest.TestCase):
    def setUp(self):
        self.registrar = EventHandlerRegistrar()

    def test_applies_registered_handler(self):
        handler = Mock()
        document = Mock()
        arg = Mock()
        kwarg = Mock()
        self.registrar.register('save', handler)
        self.registrar.apply('save', document, arg, kwarg=kwarg)
        handler.assert_called_once_with(document, arg, kwarg=kwarg)

    def test_applies_only_handler_registered_for_event(self):
        save_handler = Mock()
        remove_handler = Mock()
        document = Mock()
        arg = Mock()
        kwarg = Mock()
        self.registrar.register('save', save_handler)
        self.registrar.register('remove', remove_handler)
        self.registrar.apply('save', document, arg, kwarg=kwarg)
        save_handler.assert_called_once_with(document, arg, kwarg=kwarg)
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

    def test_handler_not_called_after_deregistration(self):
        handler = Mock()
        document = Mock()
        arg = Mock()
        kwarg = Mock()
        self.registrar.register('save', handler)
        self.registrar.deregister('save', handler)
        self.registrar.apply('save', document, arg, kwarg=kwarg)
        self.assertEquals(0, handler.call_count)

    def test_deregister_when_not_registered(self):
        handler = Mock()
        self.registrar.register('save', handler)
        self.registrar.deregister('save', handler)
        self.registrar.deregister('save', handler)
        self.registrar.deregister('bogus', handler)

    def test_deregister_all(self):
        handler1, handler2 = Mock(), Mock()
        document = Mock()
        arg = Mock()
        kwarg = Mock()
        self.registrar.register('save', handler1)
        self.registrar.register('save', handler2)
        self.registrar.deregister_all()
        self.registrar.apply('save', document, arg, kwarg=kwarg)
        self.assertEquals(0, handler1.call_count)
        self.assertEquals(0, handler2.call_count)

    def test_deregister_all_with_event_type(self):
        handler1, handler2 = Mock(), Mock()
        document = Mock()
        arg = Mock()
        kwarg = Mock()
        self.registrar.register('save', handler1)
        self.registrar.register('save', handler2)
        self.registrar.deregister_all('reload')
        self.registrar.apply('save', document, arg, kwarg=kwarg)
        self.assertEquals(1, handler1.call_count)
        self.assertEquals(1, handler2.call_count)
        self.registrar.deregister_all('other', 'save')
        self.assertEquals(1, handler1.call_count)
        self.assertEquals(1, handler2.call_count)

    def test_handlers(self):
        handler1, handler2 = Mock(), Mock()
        self.registrar.register('save', handler1)
        self.registrar.register('save', handler2)
        self.assertEquals([handler1, handler2], self.registrar.handlers('save'))
        self.assertEquals([], self.registrar.handlers('other'))

