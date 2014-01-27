from document import Document
from queries import ScopeBuilder
from exceptions import NotFoundException
from copy import deepcopy
from bson import ObjectId
from middleware import MiddlewareRegistrar
import re
import types


OBJECTIDEXPR = re.compile(r"^[a-fA-F0-9]{24}$")


class Model(Document):
    """
    Model base class on which all specific user model classes subclass.

    ** Do not attempt to subclass Model directly. **

    Instead use mongothon.create_model which will ensure the model
    subclass is correctly constructed with the appropriate collection
    and schema dependencies.
    """

    # Valid lifecycle states which a given Model instance may occupy.
    NEW = 1
    PERSISTED = 2
    DELETED = 3

    middleware_registrar = MiddlewareRegistrar()

    def __init__(self, inital_doc=None, initial_state=NEW):
        self._state = initial_state
        super(Model, self).__init__(inital_doc)

    def _create_working(self):
        working = deepcopy(self)
        self.schema.apply_defaults(working)
        return working

    @classmethod
    def _ensure_object_id(cls, id):
        """Checks whether the given id is an ObjectId instance, and if not wraps it."""
        if isinstance(id, ObjectId):
            return id

        if isinstance(id, basestring) and OBJECTIDEXPR.match(id):
            return ObjectId(id)

        return id

    @classmethod
    def _id_spec(cls, id):
        return {'_id': cls._ensure_object_id(id)}

    def is_new(self):
        """Returns true if the current model instance is new and has yet to be
        persisted to the underlying Mongo collection."""
        return self._state == Model.NEW

    def is_persisted(self):
        """Returns true if the model instance exists in the database."""
        return self._state == Model.PERSISTED

    def is_deleted(self):
        """Returns true if the model instance was deleted from the database."""
        return self._state == Model.DELETED

    def validate(self):
        """Validates this model against the schema with which is was constructed.
        Throws a ValidationException if the document is found to be invalid."""
        self._do_validate(self._create_working())

    def _do_validate(self, document):
        self.middleware_registrar.apply('before_validate', document)
        self.schema.validate(document)
        self.middleware_registrar.apply('after_validate', document)

    def apply_defaults(self):
        """Apply schema defaults to this document."""
        self.schema.apply_defaults(self)

    def save(self, *args, **kwargs):
        # Create a working copy of ourselves and validate it
        working = self._create_working()
        self._do_validate(working)

        # Apply before save middleware
        self.middleware_registrar.apply('before_save', working)

        # Attempt to save
        self.collection.save(working, *args, **kwargs)
        self._state = Model.PERSISTED

        # Apply after save middleware
        self.middleware_registrar.apply('after_save', working)

        # On successful completion, update from the working copy
        self.populate(working)

    @classmethod
    def insert(cls, *args, **kwargs):
        cls.collection.insert(*args, **kwargs)

    def update_instance(self, *args, **kwargs):
        return self.__class__.update({'_id': self['_id']}, *args, **kwargs)

    @classmethod
    def update(cls, *args, **kwargs):
        return cls.collection.update(*args, **kwargs)

    def __getattribute__(self, name):
        if name == 'update':
            return lambda *args, **kwargs: dict.update(self, *args, **kwargs)
        return super(Model, self).__getattribute__(name)

    def remove(self, *args, **kwargs):
        self.collection.remove(self['_id'], *args, **kwargs)
        self._state = Model.DELETED

    @classmethod
    def count(cls):
        return cls.collection.count()

    @classmethod
    def find_one(cls, *args, **kwargs):
        return cls(cls.collection.find_one(*args, **kwargs),
                   initial_state=Model.PERSISTED)

    @classmethod
    def find(cls, *args, **kwargs):
        return CursorWrapper(cls.collection.find(*args, **kwargs), cls)

    @classmethod
    def find_by_id(cls, id):
        """
        Finds a single document by it's ID. Throws a
        NotFoundException if the document does not exist (the
        assumption being if you're got an id you should be
        pretty certain the thing exists)
        """
        obj = cls.find_one(cls._id_spec(id))
        if not obj:
            raise NotFoundException(cls.collection, id)
        return obj

    def reload(self):
        """Reloads the current model's data from the underlying
        database record, updating it in-place."""
        self.populate(self.collection.find_one(self.__class__._id_spec(self['_id'])))

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

    def __init__(self, wrapped_cursor, model_class):
        self._wrapped = wrapped_cursor
        self._model_class = model_class

    def __getitem__(self, index):
        return self._model_class(self._wrapped[index], initial_state=Model.PERSISTED)

    def __getattr__(self, name):
        attr = getattr(self._wrapped, name)
        if name in self.RETURNS_CURSOR:
            def attr_wrapper(*args, **kwargs):
                return CursorWrapper(attr(*args, **kwargs), self._model_class)

            return attr_wrapper
        return attr
