class Document(dict):
    def __init__(self, initial=None):
        if initial:
            self.populate(initial)

    def _populate(self, from_dict, seen):
        if id(from_dict) in seen:
            raise ValueError("Circular reference detected in dict used to populate Mongothon document")
        seen.add(id(from_dict))

        def create_doc(value):
            doc = Document()
            doc._populate(value, seen)
            return doc

        self.clear()
        for key, value in from_dict.iteritems():
            if isinstance(value, dict):
                self[key] = create_doc(value)

            elif isinstance(value, list):
                self[key] = []
                for item in value:
                    if isinstance(item, dict):
                        self[key].append(create_doc(item))
                    else:
                        self[key].append(item)

            else:
                self[key] = value

    def populate(self, from_dict):
        """Populates this document from the given dict."""
        seen = set()
        self._populate(from_dict, seen)


