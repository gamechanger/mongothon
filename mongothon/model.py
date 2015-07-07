import re
import types
from copy import deepcopy, copy
from bson import ObjectId
from .document import Document
from .queries import ScopeBuilder
from .exceptions import NotFoundException
from .events import EventHandlerRegistrar
from .scopes import STANDARD_SCOPES
from .schema import IndexSpec

OBJECTIDEXPR = re.compile(r"^[a-fA-F0-9]{24}$")


class ModelMeta(type):
    """
    To support lazy collection loading without breaking the existing API, we have
    three requirements:
    1. `collection` is accessible as a class property of Model
    2. `collection` is accessible as an instance property of Model
    3. The collection can be dynamically resolved at runtime rather than compile time

    We use this metaclass to provide #1 while hooking into a class method (which
    provides #3) under the hood.
    """
    def __getattribute__(self, name):
        if name == 'collection':
            return self.get_collection()
        return super(ModelMeta, self).__getattribute__(name)


class Model(Document):
    """
    Model base class on which all specific user model classes subclass.

    ** Do not attempt to subclass Model directly. **

    Instead use mongothon.create_model which will ensure the model
    subclass is correctly constructed with the appropriate collection
    and schema dependencies.
    """

    __metaclass__ = ModelMeta

    # Valid lifecycle states which a given Model instance may occupy.
    NEW = 1
    PERSISTED = 2
    DELETED = 3

    def __init__(self, inital_doc=None, initial_state=NEW, **kwargs):
        self._state = initial_state
        super(Model, self).__init__(inital_doc, **kwargs)
        self.emit('did_init')
        if initial_state == self.PERSISTED:
            self.emit('did_find')

    def _create_working(self):
        working = deepcopy(self)
        self.schema.apply_defaults(working)
        return working

    @classmethod
    def handler_registrar(cls):
        if not hasattr(cls, '_handler_registrar'):
            cls._handler_registrar = EventHandlerRegistrar()
        return cls._handler_registrar

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
        """Validates this model against the schema with which it was constructed.
        Throws a ValidationException if the document is found to be invalid."""
        self._do_validate(self._create_working())

    def _do_validate(self, document):
        self._emit('will_validate', document)
        self.schema.validate(document)
        self._emit('did_validate', document)

    def apply_defaults(self):
        """Apply schema defaults to this document."""
        self.emit('will_apply_defaults')
        self.schema.apply_defaults(self)
        self.emit('did_apply_defaults')

    @classmethod
    def apply_index(cls, index):
        index.apply_to(cls.get_collection())

    @classmethod
    def apply_indexes(cls):
        for index in cls.schema.indexes:
            index.apply_to(cls.get_collection())

    @classmethod
    def _existing_indexes(cls):
        """
          >>> db.<col>.index_information()
          {u'_id_': {u'key': [(u'_id', 1)]},
           u'x_1': {u'unique': True, u'key': [(u'x', 1)]}}
        """
        info = cls.get_collection().index_information()
        indexes = []
        for k, v in info.iteritems():
            if k == '_id_': # this is the primary key index, not interesting
                continue
            index = IndexSpec(k, v['key'])
            for arg, val in v.iteritems():
                if arg == 'key':
                    continue
                index.kwargs[arg] == val
            index.validate()
            indexes.append(index)
        return indexes

    @classmethod
    def applied_indexes(cls):
        return [i.name for i in cls._existing_indexes()]

    @classmethod
    def unapplied_indexes(cls):
        existing_names = set([i.name for i in cls._existing_indexes()])
        expected_names = [i.name for i in cls.schema.indexes]
        return [name for name in expected_names if name not in existing_names]

    @classmethod
    def get_collection(cls):
        if not hasattr(cls, '_collection'):
            cls._collection = cls._collection_factory()
        return cls._collection

    def save(self, *args, **kwargs):
        # Create a working copy of ourselves and validate it
        working = self._create_working()
        self._do_validate(working)

        self._emit('will_save', working)

        # Attempt to save
        self.collection.save(working, *args, **kwargs)
        self._state = Model.PERSISTED

        self._emit('did_save', working)

        # On successful completion, update from the working copy
        self.populate(working)

    @classmethod
    def insert(cls, *args, **kwargs):
        cls.collection.insert(*args, **kwargs)

    def update_instance(self, *args, **kwargs):
        self.emit('will_update', *args, **kwargs)
        result = type(self).update({'_id': self['_id']}, *args, **kwargs)
        self.emit('did_update', *args, **kwargs)
        return result

    @classmethod
    def update(cls, *args, **kwargs):
        return cls.collection.update(*args, **kwargs)

    def __getattribute__(self, name):
        # This ensures that we can resolve model.update (instance method) to
        # dict.update on the underlying document given that the Model.update
        # (class method) proxies to the PyMongo collection.update instance method.
        if name == 'update':
            return lambda *args, **kwargs: super(Model, self).update(*args, **kwargs)

        # This branch allows `collection` to be dynamically resolved and accessed
        # as an instance property, see the docstring for ModelMeta for more
        elif name == 'collection':
            return self.get_collection()
        return super(Model, self).__getattribute__(name)

    def remove(self, *args, **kwargs):
        self.emit('will_remove', *args, **kwargs)
        self.collection.remove(self['_id'], *args, **kwargs)
        self.emit('did_remove', *args, **kwargs)
        self._state = Model.DELETED

    @classmethod
    def count(cls):
        return cls.collection.count()

    @classmethod
    def find_one(cls, *args, **kwargs):
        obj = cls.collection.find_one(*args, **kwargs)
        if obj:
            return cls(obj, initial_state=Model.PERSISTED)
        return None

    @classmethod
    def find(cls, *args, **kwargs):
        return CursorWrapper(cls.collection.find(*args, **kwargs), cls)

    @classmethod
    def find_by_id(cls, id):
        """
        Finds a single document by its ID. Throws a
        NotFoundException if the document does not exist (the
        assumption being if you've got an id you should be
        pretty certain the thing exists)
        """
        obj = cls.find_one(cls._id_spec(id))
        if not obj:
            raise NotFoundException(cls.collection, id)
        return obj

    def reload(self):
        """Reloads the current model's data from the underlying
        database record, updating it in-place."""
        self.emit('will_reload')
        self.populate(self.collection.find_one(type(self)._id_spec(self['_id'])))
        self.emit('did_reload')

    @classmethod
    def on(cls, event, handler_func=None):
        """
        Registers a handler function whenever an instance of the model
        emits the given event.

        This method can either called directly, passing a function reference:

            MyModel.on('did_save', my_function)

        ...or as a decorator of the function to be registered.

            @MyModel.on('did_save')
            def myfunction(my_model):
                pass

        """
        if handler_func:
            cls.handler_registrar().register(event, handler_func)
            return

        def register(fn):
            cls.handler_registrar().register(event, fn)
            return fn

        return register

    def _emit(self, event, document, *args, **kwargs):
        """
        Inner version of emit which passes the given document as the
        primary argument to handler functions.
        """
        self.handler_registrar().apply(event, document, *args, **kwargs)


    def emit(self, event, *args, **kwargs):
        """
        Emits an event call to all handler functions registered against
        this model's class and the given event type.
        """
        self._emit(event, self, *args, **kwargs)

    @classmethod
    def remove_handler(self, event, handler_func):
        """
        Deregisters the given handler function from the given event on this Model.
        When the given event is next emitted, the given function will not be called.
        """
        self.handler_registrar().deregister(event, handler_func)

    @classmethod
    def remove_all_handlers(self, *events):
        """
        Deregisters all handler functions, or those registered against the given event(s).
        """
        self.handler_registrar().deregister_all(*events)

    @classmethod
    def handlers(self, event):
        """
        Returns all handlers registered against the given event.
        """
        return self.handler_registrar().handlers(event)

    @classmethod
    def static_method(cls, f):
        """Decorator which dynamically binds static methods to the model for later use."""
        setattr(cls, f.__name__, staticmethod(f))
        return f

    @classmethod
    def class_method(cls, f):
        """Decorator which dynamically binds class methods to the model for later use."""
        setattr(cls, f.__name__, classmethod(f))
        return f

    @classmethod
    def instance_method(cls, f):
        """Decorator which dynamically binds instance methods to the model."""
        setattr(cls, f.__name__, f)
        return f

    @classmethod
    def scope(cls, f):
        """Decorator which can dynamically attach a query scope to the model."""
        if not hasattr(cls, "scopes"):
            cls.scopes = copy(STANDARD_SCOPES)

        cls.scopes.append(f)

        def create_builder(self, *args, **kwargs):
            bldr = ScopeBuilder(cls, cls.scopes)
            return getattr(bldr, f.__name__)(*args, **kwargs)

        setattr(cls, f.__name__, classmethod(create_builder))
        return f


class CursorWrapper(object):
    """
    A wrapper for the standard pymongo Cursor object which ensures all
    objects returned by the cursor's query are wrapped in an instance
    of the given Model class.
    """
    RETURNS_CURSOR = ['rewind', 'clone', 'add_option', 'remove_option',
                      'limit', 'batch_size', 'skip', 'max_scan', 'sort',
                      'hint', 'where']

    def __init__(self, wrapped_cursor, model_class):
        self._wrapped = wrapped_cursor
        self._model_class = model_class

    def __getitem__(self, index):
        return self._model_class(self._wrapped[index], initial_state=Model.PERSISTED)

    def __iter__(self):
        return IteratorWrapper(self._wrapped.__iter__(), self._model_class)

    def __getattr__(self, name):
        attr = getattr(self._wrapped, name)
        if name in self.RETURNS_CURSOR:
            def attr_wrapper(*args, **kwargs):
                return CursorWrapper(attr(*args, **kwargs), self._model_class)

            return attr_wrapper
        return attr


class IteratorWrapper(object):
    """
    Wrapper for the iterator object returned by the pymongo cursor. Allows
    CursorWrapper to implement the iterator protocol while still returning
    models.
    """

    def __init__(self, wrapped_iterator, model_class):
        self._wrapped = wrapped_iterator
        self._model_class = model_class

    def next(self):
        return self._model_class(self._wrapped.next(), initial_state=Model.PERSISTED)
