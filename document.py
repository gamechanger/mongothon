import re

valid_key = re.compile('^[\$A-Za-z_][0-9A-Za-z_\$]*$')

class Document(dict):
    def __init__(self, initial=None):
        if initial:
            for key, value in initial.iteritems():
                # All document keys must be strings containing valid javascript identifier
                if not valid_key.match(key):
                    raise Exception('Invalid document') # TODO make this nicer

                if isinstance(value, dict):
                    self[key] = Document(value)

                elif isinstance(value, list):
                    self[key] = [Document(item) for item in value]

                else:
                    self[key] = value

    def __getattr__(self, name):
        if self.has_key(name):
            return self[name]
        raise AttributeError("{0} is not found")