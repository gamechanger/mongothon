class NotFoundException(Exception):
    """Exception used to indicate that a requested record could not be
    found."""
    def __init__(self, collection, id):
        self._collection = collection
        self._id = id

    def __str__(self):
        return "{} {} not found".format(self._collection.name, self._id)
