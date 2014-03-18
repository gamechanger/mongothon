class NotFoundException(Exception):
    """Exception used to indicate that a requested record could not be
    found."""
    def __init__(self, collection, id):
        self._collection = collection
        self._id = id

    def __str__(self):
        return "{} {} not found".format(self._collection.name, self._id)

class InvalidIDException(Exception):
    """
    Indicates that you passed a shitty ID into a function that expects a non-shitty one
    """
    def __init__(self, id):
        self._id = id
        self.message = str(self)

    def __str__(self):
        return "{} ({}) is an invalid ID".format(self._id, type(self._id))
