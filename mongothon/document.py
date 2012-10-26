import re

valid_key = re.compile('^[\$A-Za-z_][0-9A-Za-z_\$]*$')

class Document(dict):
    def __init__(self, initial=None):
        if initial:
            self.populate(initial)

    def populate(self, from_dict):
        """Populates this document from the given dict."""

        self.clear()
        for key, value in from_dict.iteritems():
            # All document keys must be strings containing valid javascript identifier
            if not valid_key.match(key):
                raise ValueError("Document property {0} is improperly named.".format(key)) 

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

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError("{0} is not found")

    def __setattr__(self, name, value):
        self[name] = value
