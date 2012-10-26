class MiddlewareRegistrar(object):
    """Handles the registration of middleware functions against specific
    model events and the execution of those middleware in response to
    those events.

    This class is internal to Mongothon and should not be manipulated
    directly. Instead, consumer code should register and indirectly
    invoke middleware via Models."""

    def __init__(self):
        self._middleware_dict = {}

    def register(self, event, fn):
        """Registers the given function as a middleware to be applied
        in response to the the given event."""

        # TODO: Can we check the method signature?
        self._middleware_dict.setdefault(event, [])
        if fn not in self._middleware_dict[event]:
            self._middleware_dict[event].append(fn)

    def apply(self, event, document):
        """Applies all middleware functions registered against the given
        event in order to the given document."""
        for fn in self._middleware_dict.get(event, []):
            fn(document)
