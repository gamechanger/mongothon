from bson.objectid import ObjectId
import schemer


class Schema(schemer.Schema):
    """A Schema encapsulates the structure and constraints of a Mongo document."""

    indexes = []

    def __init__(self, doc_spec, **kwargs):
        super(Schema, self).__init__(doc_spec, **{k:v for k,v in kwargs.iteritems() if k != 'indexes'})

        # Every mongothon schema should expect an ID field.
        if '_id' not in self._doc_spec:
            self._doc_spec['_id'] = {"type": ObjectId}

        self.indexes = kwargs.get('indexes', [])
        self._validate_indexes()

    def _validate_indexes(self):
        for index in self.indexes:
            if 'name' not in index:
                raise KeyError('name')
            if 'key' not in index:
                raise KeyError('key')
