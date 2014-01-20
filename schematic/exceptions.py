

class SchemaFormatException(Exception):
    """Exception which encapsulates a problem found during the verification of a
    a schema."""

    def __init__(self, message, path):
        self._message = message.format(path)
        self._path = path

    @property
    def path(self):
        """The field path at which the format error was found."""
        return self._path

    def __str__(self):
        return self._message


class ValidationException(Exception):
    """Exception which is thrown in response to the failed validation of a document
    against it's associated schema."""

    def __init__(self, errors):
        self._errors = errors

    @property
    def errors(self):
        """A dict containing the validation error(s) found at each field path."""
        return self._errors

    def __str__(self):
        return repr(self._errors)
