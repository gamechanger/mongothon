from copy import deepcopy


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
                new_query.update(query)
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
        for fn in fns:
            self.register_fn(fn)

    def __getitem__(self, index):
        """Implementation of the iterator __getitem__ method. This allows the
        builder query to be executed and iterated over without a separate call
        to `execute()` being needed."""
        if not hasattr(self, "in_progress_cursor"):
            self.in_progress_cursor = self.execute()
        return self.in_progress_cursor[index]


    def execute(self):
        """Executes the currently built up query."""
        return self.model.find(self.query, self.projection or None, **self.options)
