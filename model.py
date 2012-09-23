from document import Document
from copy import deepcopy
from bson import ObjectId

def create(schema, collection):

    class Model(Document):
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
            return {'_id':cls._ensure_object_id(id)}

        def validate(self):
            schema.validate(self._create_working())

        def apply_defaults(self):
            """Apply schema defaults to this document."""
            schema.apply_defaults(self)

        def save(self, *args, **kwargs):
            # Create a working copy of ourselves and validate it
            working = self._create_working()
            schema.validate(working)

            # Attempt to save
            collection.save(working, *args, **kwargs)

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


    class CursorWrapper(object):
        def __init__(self, wrapped_cursor):
            self._wrapped = wrapped_cursor

        def __getitem__(self, index):
            return Model(self._wrapped[index])

        def __getattr__(self, name):
            return getattr(self._wrapped, name)


    return Model

