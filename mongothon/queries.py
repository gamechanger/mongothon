from copy import deepcopy

def deep_merge(source, dest):
    """Deep merges source dict into dest dict."""
    for key, value in source.iteritems():
        if key in dest:
            if isinstance(value, dict) and isinstance(dest[key], dict):
                deep_merge(value, dest[key])
                continue
            elif isinstance(value, list) and isinstance(dest[key], list):
                for item in value:
                    if item not in dest[key]:
                        dest[key].append(item)
                continue
        dest[key] = value


class ScopeBuilder(object):
    """A helper class used to build query scopes. This class is provided with a
    list of scope functions (all of which return query args) which can then
    be chained together using this builder to build up more complex queries."""

    @classmethod
    def unpack_scope(cls, scope):
        """Unpacks the response from a scope function. The function should return
        either a query, a query and a projection, or a query a projection and
        an query options hash."""
        query = {}
        projection = {}
        options = {}

        if isinstance(scope, tuple):
            if len(scope) > 3:
                raise ValueError("Invalid scope")
            if len(scope) >= 1:
                query = scope[0]
            if len(scope) >= 2:
                projection = scope[1]
            if len(scope) == 3:
                options = scope[2]
        elif isinstance(scope, dict):
            query = scope
        else:
            raise ValueError("Invalid scope")

        return query, projection, options


    @classmethod
    def register_fn(cls, f):
        """Registers a scope function on this builder."""
        def inner(self, *args, **kwargs):
            try:
                query, projection, options = cls.unpack_scope(f(*args, **kwargs))
                new_query = deepcopy(self.query)
                new_projection = deepcopy(self.projection)
                new_options = deepcopy(self.options)
                deep_merge(query, new_query)
                new_projection.update(projection)
                new_options.update(options)
                return ScopeBuilder(self.model, self.fns, new_query,
                    new_projection, new_options)
            except ValueError:
                raise ValueError("Scope function \"{}\ returns an invalid scope".format(f.__name__))

        setattr(cls, f.__name__, inner)


    def __init__(self, model, fns, query={}, projection={}, options={}):
        self.fns = fns
        self.model = model
        self.query = query
        self.projection = projection
        self.options = options
        self._active_cursor = None
        for fn in fns:
            self.register_fn(fn)

    @property
    def cursor(self):
        """
        Returns a cursor for the currently assembled query, creating it if
        it doesn't already exist.
        """
        if not self._active_cursor:
            self._active_cursor = self.model.find(self.query,
                                                  self.projection or None,
                                                  **self.options)
        return self._active_cursor

    def __getitem__(self, index):
        return self.cursor[index]

    def __iter__(self):
        return self.cursor.__iter__()

    def __getattr__(self, key):
        # If the method is not one of ours, attempt to find it on the cursor
        # which will mean executing it.
        if hasattr(self.cursor, key):
            return getattr(self.cursor, key)
