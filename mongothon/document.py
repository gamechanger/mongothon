def wrap(value):
    if isinstance(value, dict):
        return Document(value)
    elif isinstance(value, list):
        return DocumentList(value)
    else:
        return value

class Document(dict):
    def __init__(self, initial=None):
        if initial:
            self.update(initial)

    def __setitem__(self, key, value):
        super(Document, self).__setitem__(key, wrap(value))

    def update(self, other=None, **kwargs):
        if other:
            for key in other:
                self[key] = other[key]

        if kwargs:
            for key, in kwargs:
                self[key] = kwargs[key]

    def setdefault(self, key, default):
        return super(Document, self).setdefault(key, wrap(default))

    def populate(self, other):
        """Like update, but clears the contents first."""
        self.clear()
        self.update(other)


class DocumentList(list):
    def __init__(self, initial=None):
        if initial:
            self.extend(initial)

    def __setslice__(self, i, j, sequence):
        super(DocumentList, self).__setslice__(i, j, [wrap(value) for value in sequence])

    def __setitem__(self, index, value):
        super(DocumentList, self).__setitem__(index, wrap(value))

    def extend(self, other):
        if other:
            super(DocumentList, self).extend([wrap(value) for value in other])

    def append(self, item):
        super(DocumentList, self).append(wrap(item))

    def insert(self, i, item):
        super(DocumentList, self).insert(i, wrap(item))
