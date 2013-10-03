from document import Document
from copy import deepcopy
from bson import ObjectId
from middleware import MiddlewareRegistrar
import types


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
        return self.model.find(self.query, self.projection, **self.options)


def create_model(schema, collection):
    """Creates and returns a model class which can be used to perform all IO
    against the given collection using the given schema."""

    class Model(Document):
        middleware_registrar = MiddlewareRegistrar()

        def _create_working(self):
            working = deepcopy(self)
            schema.apply_defaults(working)
            return working

        @classmethod
        def _ensure_object_id(cls, id):
            """Checks whether the given id is an ObjectId instance, and if not wraps it."""
            if isinstance(id, ObjectId):
                return id
            return ObjectId(id)

        @classmethod
        def _id_spec(cls, id):
            return {'_id': cls._ensure_object_id(id)}

        def validate(self):
            """Validates this model against the schema with which is was constructed.
            Throws a ValidationException if the document is found to be invalid."""
            self._do_validate(self._create_working())

        def _do_validate(self, document):
            Model.middleware_registrar.apply('before_validate', document)
            schema.validate(document)
            Model.middleware_registrar.apply('after_validate', document)

        def apply_defaults(self):
            """Apply schema defaults to this document."""
            schema.apply_defaults(self)

        def __getattr__(self, name):
            if name in schema.virtuals:
                return schema.virtuals[name].on_get(self)
            return super(Model, self).__getattr__(name)

        def __setattr__(self, name, value):
            if name in schema.virtuals:
                schema.virtuals[name].on_set(value, self)
            super(Model, self).__setattr__(name, value)

        def save(self, *args, **kwargs):
            # Create a working copy of ourselves and validate it
            working = self._create_working()
            self._do_validate(working)

            # Apply before save middleware
            Model.middleware_registrar.apply('before_save', working)

            # Attempt to save
            collection.save(working, *args, **kwargs)

            # Apply after save middleware
            Model.middleware_registrar.apply('after_save', working)

            # On successful completion, update from the working copy
            self.populate(working)

        @staticmethod
        def insert(*args, **kwargs):
            collection.insert(*args, **kwargs)

        def update(self, *args, **kwargs):
            return collection.update({"_id": self._id}, *args, **kwargs)

        def remove(self, *args, **kwargs):
            collection.remove(self._id, *args, **kwargs)

        @staticmethod
        def count():
            return collection.count()

        @classmethod
        def find_one(cls, *args, **kwargs):
            return cls(collection.find_one(*args, **kwargs))

        @staticmethod
        def find(*args, **kwargs):
            return CursorWrapper(collection.find(*args, **kwargs))

        @classmethod
        def find_by_id(cls, id):
            return cls.find_one(cls._id_spec(id))

        def reload(self):
            self.populate(collection.find_one(self.__class__._id_spec(self._id)))

        @classmethod
        def before_save(cls, middleware_func):
            """Registers a middleware function to be run before every instance
            of the given model is saved, after any before_validate middleware.
            """
            cls.middleware_registrar.register('before_save', middleware_func)

        @classmethod
        def after_save(cls, middleware_func):
            """Registers a middleware function to be run after every instance
            of the given model is saved.
            """
            cls.middleware_registrar.register('after_save', middleware_func)

        @classmethod
        def before_validate(cls, middleware_func):
            """Registers a middleware function to be run before every instance
            of the given model is validated.
            """
            cls.middleware_registrar.register('before_validate', middleware_func)

        @classmethod
        def after_validate(cls, middleware_func):
            """Registers a middleware function to be run after every instance
            of the given model is validated.
            """
            cls.middleware_registrar.register('after_validate', middleware_func)

        @classmethod
        def class_method(cls, f):
            """Decorator which dynamically binds class methods to the model for later use."""
            setattr(cls, f.__name__, types.MethodType(f, cls))

        @classmethod
        def instance_method(cls, f):
            """Decorator which dynamically binds instance methods to the model."""
            setattr(cls, f.__name__, f)

        @classmethod
        def scope(cls, f):
            """Decorator which can dynamically attach a query scope to the model."""
            if not hasattr(cls, "scopes"):
                cls.scopes = []

            cls.scopes.append(f)

            def create_builder(self, *args, **kwargs):
                bldr = ScopeBuilder(cls, cls.scopes)
                return getattr(bldr, f.__name__)(*args, **kwargs)

            setattr(cls, f.__name__, types.MethodType(create_builder, cls))




    class CursorWrapper(object):
        RETURNS_CURSOR = ['rewind', 'clone', 'add_option', 'remove_option',
                          'limit', 'batch_size', 'skip', 'max_scan', 'sort',
                          'hint', 'where']

        def __init__(self, wrapped_cursor):
            self._wrapped = wrapped_cursor

        def __getitem__(self, index):
            return Model(self._wrapped[index])

        def __getattr__(self, name):
            attr = getattr(self._wrapped, name)
            if name in self.RETURNS_CURSOR:
                def attr_wrapper(*args, **kwargs):
                    return CursorWrapper(attr(*args, **kwargs))

                return attr_wrapper
            return attr

    return Model
