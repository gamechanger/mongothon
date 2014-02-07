

class FakeCursor(object):
    """A fake cursor which emulates a cursor returned by Mongo."""
    def __init__(self, contents):
        self._contents = contents
        self._next = 0

    def __getitem__(self, index):
        return self._contents[index]

    def __getattr__(self, name):
        def return_self(*args, **kwargs):
            return self

        if name in ['rewind', 'clone', 'add_option', 'remove_option',
                    'limit', 'batch_size', 'skip', 'max_scan', 'sort',
                    'hint', 'where']:
            return return_self

    def __iter__(self):
        return FakeCursor(self._contents)

    def next(self):
        if self._next >= len(self._contents):
            raise StopIteration

        self._next += 1
        return self._contents[self._next - 1]

    def count(self):
        return len(self._contents)
