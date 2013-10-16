class Document(dict):
    def __init__(self, initial=None):
        if initial:
            self.populate(initial)

    def populate(self, from_dict):
        """Populates this document from the given dict."""

        self.clear()
        for key, value in from_dict.iteritems():
            if isinstance(value, dict):
                self[key] = Document(value)

            elif isinstance(value, list):
                self[key] = []
                for item in value:
                    if isinstance(item, dict):
                        self[key].append(Document(item))
                    else:
                        self[key].append(item)

            else:
                self[key] = value

