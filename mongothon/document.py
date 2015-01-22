from copy import deepcopy

def wrap(value):
    """
    Wraps the given value in a Document or DocumentList as applicable.
    """
    if isinstance(value, Document) or isinstance(value, DocumentList):
        return value
    elif isinstance(value, dict):
        return Document(value)
    elif isinstance(value, list):
        return DocumentList(value)
    else:
        return value


def unwrap(value):
    """
    Unwraps the given Document or DocumentList as applicable.
    """
    if isinstance(value, Document):
        return value.to_dict()
    elif isinstance(value, DocumentList):
        return value.to_list()
    else:
        return value


class ChangeTracker(object):
    def __init__(self, instance):
        self._instance = instance
        self.reset_changes()

    def reset_changes(self):
        """
        Resets the document's internal change-tracking state. All field additions,
        changes and deletions are forgotten.
        """
        self._added = []
        self._previous = {}
        self._deleted = {}

    def update(self, other):
        self.reset_changes()
        self._added.extend(other._added)
        self._previous.update(other._previous)
        self._deleted.update(other._deleted)

    def note_change(self, key, value):
        """
        Updates change state to reflect a change to a field. Takes care of ignoring
        no-ops, reversions and takes appropriate steps if the field was previously
        deleted or added to ensure the change state purely reflects the diff since
        last reset.
        """
        # If we're changing the value and we haven't done so already, note it.
        if value != self._instance[key] and key not in self._previous and key not in self._added:
            self._previous[key] = self._instance[key]

        # If we're setting the value back to the original value, discard the change note
        if key in self._previous and value == self._previous[key]:
            del self._previous[key]

    def note_addition(self, key, value):
        """
        Updates the change state to reflect the addition of a field. Detects previous
        changes and deletions of the field and acts accordingly.
        """
        # If we're adding a field we previously deleted, remove the deleted note.
        if key in self._deleted:
            # If the key we're adding back has a different value, then it's a change
            if value != self._deleted[key]:
                self._previous[key] = self._deleted[key]
            del self._deleted[key]
        else:
            self._added.append(key)

    def note_deletion(self, key):
        """
        Notes the deletion of a field.
        """
        # If we'rew deleting a key we previously added, then there is no diff
        if key in self._added:
            self._added.remove(key)
        else:
            # If the deleted key was previously changed, use the original value
            if key in self._previous:
                self._deleted[key] = self._previous[key]
                del self._previous[key]
            else:
                self._deleted[key] = self._instance[key]

    @property
    def changed(self):
        """
        Returns a dict containing just the fields which have changed on this
        Document since it was created or last saved, together with their new
        values.

            doc['name']             # => 'bob'
            doc['name'] = 'clive'
            doc.changed             # => {'name': 'clive'}
        """
        return {key: self._instance[key] for key in self._previous}

    @property
    def changes(self):
        """
        Returns a dict containing just the fields which have changed on this
        Document since it was created or last saved, together with both their
        previous and current values

            doc['name']             # => 'bob'
            doc['name'] = 'clive'
            doc.changes             # => {'name': ('bob', clive')}
        """
        return {key: (self._previous[key], self._instance[key])
                for key in self._previous}

    @property
    def added(self):
        """
            doc                     # => {'name': 'bob'}
            doc['age'] = 42
            doc.added               # => {'age': 42}
        """
        return {key: self._instance[key] for key in self._added}

    @property
    def deleted(self):
        """
            doc                     # => {'name': 'bob'}
            del doc['name']
            doc.deleted             # => {'name': 'bob'}
        """
        return self._deleted

class Document(dict):
    """
    Subclass of dict which adds some useful functionality around change tracking.
    """

    def __init__(self, initial=None):
        if initial:
            self.update(initial)
        self.reset_changes()

    @property
    def _tracker(self):
        try:
            return self._change_tracker
        except AttributeError:
            self._change_tracker = ChangeTracker(self)
            return self._change_tracker

    def reset_changes(self):
        self._tracker.reset_changes()

    def reset_all_changes(self):
        """
        Resets change tracking in this document, recursing into child Documents and
        DocumentLists.
        """
        self.reset_changes()
        for value in self.values():
            if isinstance(value, Document) or isinstance(value, DocumentList):
                value.reset_all_changes()

    def __deepcopy__(self, memo):
        clone = type(self)(deepcopy(dict(self), memo))
        clone._tracker.update(self._tracker)
        return clone

    @property
    def changed(self):
        return self._tracker.changed

    @property
    def changes(self):
        return self._tracker.changes

    @property
    def added(self):
        return self._tracker.added

    @property
    def deleted(self):
        return self._tracker.deleted

    def __setitem__(self, key, value):
        if key in self:
            self._tracker.note_change(key, value)
        else:
            self._tracker.note_addition(key, value)
        super(Document, self).__setitem__(key, wrap(value))

    def __delitem__(self, key):
        self._tracker.note_deletion(key)
        super(Document, self).__delitem__(key)

    def update(self, other=None, **kwargs):
        if other:
            for key in other:
                self[key] = other[key]

        if kwargs:
            for key, value in kwargs.iteritems():
                self[key] = value

    def setdefault(self, key, default):
        return super(Document, self).setdefault(key, wrap(default))

    def populate(self, other):
        """Like update, but clears the contents first."""
        self.clear()
        self.update(other)
        self.reset_all_changes()

    def to_dict(self):
        """
        Returns the contents of the Document as a raw dict. Also recurses
        into child Documents and DocumentLists converting those to dicts
        and lists respectively.
        """
        return {key: unwrap(value) for key, value in self.iteritems()}


class DocumentList(list):
    """
    Subclass of list which provides some additional details around change tracking.
    """
    def __init__(self, initial=None):
        if initial:
            self.extend(initial)

    def reset_all_changes(self):
        for value in self:
            if isinstance(value, Document) or isinstance(value, DocumentList):
                value.reset_all_changes()

    def __setslice__(self, i, j, sequence):
        super(DocumentList, self).__setslice__(i, j, [wrap(value) for value in sequence])

    def __setitem__(self, index, value):
        super(DocumentList, self).__setitem__(index, wrap(value))

    def extend(self, other):
        super(DocumentList, self).extend([wrap(value) for value in other])

    def append(self, item):
        super(DocumentList, self).append(wrap(item))

    def insert(self, i, item):
        super(DocumentList, self).insert(i, wrap(item))

    def remove(self, item):
        super(DocumentList, self).remove(item)

    def pop(self, *args):
        return super(DocumentList, self).pop(*args)

    def to_list(self):
        """
        Returns the contents of the DocumentList as a raw list. Also recurses
        into child Documents and DocumentLists converting those to dicts
        and lists respectively.
        """
        return [unwrap(value) for value in self]
