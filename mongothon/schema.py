from bson.objectid import ObjectId
import pymongo
import schemer


class IndexSpec(object):
    def __init__(self, name, key_spec, **kwargs):
        self.name = name
        self.key_spec = key_spec
        self.kwargs = kwargs

    def apply_to(self, collection):
        collection.create_index(self.key_spec, name=self.name, **self.kwargs)

    def validate(self):
        if not self.name:
            raise ValueError("Must specify a non-nil name for every index")
        if not self.key_spec:
            raise ValueError("Must specify the actual index for {}".format(self.name))
        for name, index_type in self.key_spec:
            if index_type not in {pymongo.ASCENDING, pymongo.DESCENDING, pymongo.HASHED}:
                raise ValueError('Unsupported Index Type {} for {}'.format(index_type, self.name))
        return self



class Schema(schemer.Schema):
    """A Schema encapsulates the structure and constraints of a Mongo document."""

    indexes = []

    def __init__(self, doc_spec, indexes=[], **kwargs):
        super(Schema, self).__init__(doc_spec, **kwargs)

        # Every mongothon schema should expect an ID field.
        if '_id' not in self._doc_spec:
            self._doc_spec['_id'] = {"type": ObjectId}

        self.indexes = [i.validate() for i in indexes]
