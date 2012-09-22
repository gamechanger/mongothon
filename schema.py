from datetime import datetime
from types import FunctionType

def _append_path(prefix, field):
    if prefix:
        return "{0}.{1}".format(prefix, field)
    else:
        return field

def _verify_schema(schema, path_prefix):
    for field, spec in schema.doc_spec.iteritems():
        path = _append_path(path_prefix, field)
        
        # Standard dict-based spec
        if isinstance(spec, dict):
            _verify_field_spec(spec, path)
            
        # An embedded collection
        elif isinstance(spec, list):
            if len(spec) == 0:
                raise SchemaFormatException(
                    "No type declared for the embedded collection at {0}",
                    path)

            if len(spec) > 1:
                raise SchemaFormatException(
                    "Only one type must be declared for the embedded collection at {0}",
                    path)

            if not isinstance(spec[0], Schema):
                raise SchemaFormatException(
                    "Embedded collection at {0} not described using a Schema object.",
                    path)

            _verify_schema(spec[0], path)

        else:
            raise SchemaFormatException("Invalid field definition for {0}", path)


def _verify_field_spec(spec, path):
    if not spec.has_key('type'):
        raise SchemaFormatException("{0} has no type declared.", path)

    field_type = spec['type']

    if isinstance(field_type, Schema):
        _verify_schema(field_type, path)
        return

    if field_type not in [basestring, int, float, datetime, long, bool]:
        raise SchemaFormatException("{0} is not declared with a valid type.", path)

    if spec.has_key('required') and not isinstance(spec['required'], bool):
        raise SchemaFormatException("{0} required declaration should be True or False", path)
        
    if spec.has_key('validates'):
        validates = spec['validates']
        if not (isinstance(validates, FunctionType) or 
                isinstance(validates, list)):
            raise SchemaFormatException("Invalid validations for {0}", path)

        elif isinstance(validates, list): 
            for validator in validates:
                if not isinstance(validator, FunctionType):
                    raise SchemaFormatException("Invalid validations for {0}", path)

    if not set(spec.keys()).issubset(set(['type', 'required', 'validates'])):
        raise SchemaFormatException("Unsupported field spec item at {0}. Items: "+repr(spec.keys()), path)

def _validate_instance_against_schema(instance, schema, path_prefix, errors):
    # Loop over each field in the schema and check the instance value conforms
    # to its spec
    for field, spec in schema.doc_spec.iteritems():
        value = instance.get(field, None)

        path = _append_path(path_prefix, field)
        
        # Standard dict-based spec
        if isinstance(spec, dict):
            _validate_value(value, spec, path, errors)

        # An embedded collection
        elif isinstance(spec, list):
            if (value is not None):
                if not isinstance(value, list):
                    errors[path] = "Expected a list."
                    continue
                else:
                    for i, item in enumerate(value):
                        instance_path = "{0}.{1}".format(path, i)
                        _validate_instance_against_schema(item, spec[0], instance_path, errors)


def _validate_value(value, field_spec, path, errors):
    # Check for an empty value and bail out if necessary applying the required
    # constraint in the process.
    if value is None:
        if field_spec.get('required', False):
            errors[path] = "%s is required." % path
        return

    # All fields should have a type
    field_type = field_spec['type']

    # If our field is an embedded document, recurse into it
    if isinstance(field_type, Schema):
        if isinstance(value, dict):
            _validate_instance_against_schema(value, field_type, path, errors)
        else:
            errors[path] = "%s should be an embedded document" % path
        return

    # Otherwise, validate the field
    if not isinstance(value, field_type):
        errors[path] = "Field should be of type {0}".format(field_type)
        return

    validations = field_spec.get('validates', None)
    if validations is None:
        return

    def apply(fn):
        error = fn(value)
        if error:
            errors[path] = error

    if isinstance(validations, list):
        for validation in validations:
            apply(validation)
    else:
        apply(validations)


class SchemaFormatException(Exception):
    def __init__(self, message, path):
        self._message = message.format(path)
        self._path = path

    @property
    def path(self):
        return self._path

    def __str__(self):
        return self._message


class ValidationException(Exception):
    def __init__(self, errors):
        self._errors = errors

    @property
    def errors(self):
        return self._errors

    def __str__(self):
        return repr(self._errors)


class Schema(object):
    def __init__(self, doc_spec):
        self._doc_spec = doc_spec

    @property
    def doc_spec(self):
        return self._doc_spec

    def verify(self):
        """Verifies that the given schema document spec is valid."""
        _verify_schema(self, None)

    def apply_defaults(self, instance):
        """Applies default values to the given document"""
        #for (field, spec) in 

    def validate(self, instance):
        """Validates the given document against this schema. Raises a 
        ValidationException if there are any failures."""
        errors = {}
        _validate_instance_against_schema(instance, self, None, errors)

        if len(errors) > 0:
            raise ValidationException(errors)


