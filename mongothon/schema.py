from bson.objectid import ObjectId
import schemer


class Schema(schemer.Schema):
    """A Schema encapsulates the structure and constraints of a Mongo document."""

    def __init__(self, doc_spec, **kwargs):
        super(Schema, self).__init__(doc_spec, **kwargs)

        # Every mongothon schema should expect an ID field.
        if '_id' not in self._doc_spec:
            self._doc_spec['_id'] = {"type": ObjectId}
