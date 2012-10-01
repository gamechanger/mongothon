from document import Document
from copy import deepcopy
from bson import ObjectId
from middleware import MiddlewareRegistrar

def create(schema, collection):

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

        def delete(self, *args, **kwargs):
            collection.remove(self._id, *args, **kwargs)

        @staticmethod
        def insert(*args, **kwargs):
            collection.insert(*args, **kwargs)

        @staticmethod
        def update(*args, **kwargs):
            collection.update(*args, **kwargs)

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
