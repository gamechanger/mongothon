class EventHandlerRegistrar(object):
    """Handles the registration of event handler functions against specific
    model events and the execution of those functions in response to
    those events being emitted.

    This class is internal to Mongothon and should not be manipulated
    directly. Instead, consumer code should register and indirectly
    invoke handlers via Models."""

    def __init__(self):
        self._handler_dict = {}

    def register(self, event, fn):
        """Registers the given function as a handler to be applied
        in response to the the given event."""

        # TODO: Can we check the method signature?
        self._handler_dict.setdefault(event, [])
        if fn not in self._handler_dict[event]:
            self._handler_dict[event].append(fn)

    def apply(self, event, document, *args, **kwargs):
        """Applies all middleware functions registered against the given
        event in order to the given document."""
        for fn in self._handler_dict.get(event, []):
            fn(document, *args, **kwargs)
