from inspect import getargspec
from bson.objectid import ObjectId
import logging


def Mixed(*types):
    """Mixed type, used to indicate a field in a schema can be
    one of many types. Use as a last resort only.
    The Mixed type can be used directly as a class to indicate
    any type is permitted for a given field:
    `"my_field": {"type": Mixed}`
    It can also be instantiated with list of specific types the
    field may is allowed to be for more control:
    `"my_field": {"type": Mixed(ObjectId, int)}`
    """
    if len(types) < 2:
        raise ValueError("Mixed type requires at least 2 specific types")

    types = set(types) # dedupe

    class MixedType(type):
        def __instancecheck__(cls, instance):
            """Returns true if the given value is an instance of
            one of the types enclosed by this mixed type."""
            for mtype in types:
                if isinstance(instance, mtype):
                    return True
            return False

    class Mixed(object):
        __metaclass__ = MixedType

    return Mixed


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



class Schema(object):
    """A Schema encapsulates the structure and constraints of a Mongo document."""

    def __init__(self, doc_spec, strict=True):
        self._doc_spec = doc_spec
        self._virtuals = {}
        self._strict = strict

        # Every schema should expect an ID field.
        if '_id' not in self._doc_spec:
            self._doc_spec['_id'] = {"type": ObjectId}

    @property
    def doc_spec(self):
        return self._doc_spec

    def verify(self):
        """Verifies that the given schema document spec is valid."""
        self._verify_schema(self)

    def apply_defaults(self, instance):
        """Applies default values to the given document"""
        self._apply_schema_defaults(self, instance)

    def validate(self, instance):
        """Validates the given document against this schema. Raises a
        ValidationException if there are any failures."""
        errors = {}
        self._validate_instance_against_schema(instance, self, errors)

        if len(errors) > 0:
            raise ValidationException(errors)

    def _append_path(self, prefix, field):
        """Appends the given field to the given path prefix."""
        if prefix:
            return "{0}.{1}".format(prefix, field)
        else:
            return field

    def _verify_schema(self, schema, path_prefix=None):
        """Verifies that the given schema is valid. This method is recursive and verifies and
        schemas nested within the given schema."""
        for field, spec in schema.doc_spec.iteritems():
            path = self._append_path(path_prefix, field)

            # Standard dict-based spec
            if isinstance(spec, dict):
                self._verify_field_spec(spec, path)

            # An embedded collection
            elif isinstance(spec, list):
                if len(spec) == 0 or len(spec) > 1:
                    raise SchemaFormatException(
                        "Exactly one type must be declared for the embedded collection at {0}",
                        path)

                # If the list type is a schema, recurse into it
                if isinstance(spec[0], Schema):
                    self._verify_schema(spec[0], path)
                    continue

            else:
                raise SchemaFormatException("Invalid field definition for {0}", path)


    def _verify_field_spec(self, spec, path):
        """Verifies a given field specification is valid, recursing into nested schemas if required."""

        # Required should be a boolean
        if 'required' in spec and not isinstance(spec['required'], bool):
            raise SchemaFormatException("{0} required declaration should be True or False", path)

        # Must have a type specified
        if 'type' not in spec:
            raise SchemaFormatException("{0} has no type declared.", path)

        field_type = spec['type']

        if isinstance(field_type, Schema):
            # Nested documents cannot have defaults or validation
            if not set(spec.keys()).issubset(set(['type', 'required'])):
                raise SchemaFormatException("Unsupported field spec item at {0}. Items: "+repr(spec.keys()), path)

            # Recurse into nested Schema
            self._verify_schema(field_type, path)
            return

        # Validations should be either a single function or array of functions
        if 'validates' in spec:
            validates = spec['validates']

            if isinstance(validates, list):
                for validator in validates:
                    self._verify_validator(validator, path)
            else:
                self._verify_validator(validates, path)

        # Defaults must be of the correct type or a function
        if 'default' in spec and not (isinstance(spec['default'], field_type) or callable(spec['default'])):
            raise SchemaFormatException("Default value for {0} is not of the nominated type.", path)

        # Only expected spec keys are supported
        if not set(spec.keys()).issubset(set(['type', 'required', 'validates', 'default'])):
            raise SchemaFormatException("Unsupported field spec item at {0}. Items: "+repr(spec.keys()), path)


    def _verify_validator(self, validator, path):
        """Verifies that a given validator associated with the field at the given path is legitimate."""

        # Validator should be a function
        if not callable(validator):
            raise SchemaFormatException("Invalid validations for {0}", path)

        # Validator should accept a single argument
        (args, varargs, keywords, defaults) = getargspec(validator)
        if len(args) != 1:
            raise SchemaFormatException("Invalid validations for {0}", path)


    def _validate_instance_against_schema(self, instance, schema, errors, path_prefix=''):
        """Validates that the given instance of a document conforms to the given schema's
        structure and validations. Any validation errors are added to the given errors
        collection. The caller should assume the instance is considered valid if the
        errors collection is empty when this method returns."""

        if not isinstance(instance, dict):
            errors[path_prefix] = "Expected instance of dict to validate against schema."
            return

        # Loop over each field in the schema and check the instance value conforms
        # to its spec
        for field, spec in schema.doc_spec.iteritems():
            value = instance.get(field, None)

            path = self._append_path(path_prefix, field)

            # Standard dict-based spec
            if isinstance(spec, dict):
                self._validate_value(value, spec, path, errors)

            # An embedded collection
            elif isinstance(spec, list):
                if (value is not None):
                    if not isinstance(value, list):
                        errors[path] = "Expected a list."
                        continue
                    else:
                        for i, item in enumerate(value):
                            instance_path = "{0}.{1}".format(path, i)

                            if isinstance(spec[0], Schema):
                                self._validate_instance_against_schema(item, spec[0], errors, instance_path)
                            elif not isinstance(item, spec[0]):
                                errors[instance_path] = "List item is of incorrect type"

        # Now loop over each field in the given instance and make sure we don't
        # have any fields not declared in the schema, unless strict mode has been
        # explicitly disabled.
        for field in instance:
            if field not in schema.doc_spec:
                if self._strict:
                    errors[self._append_path(path_prefix, field)] = "Unexpected document field not present in schema"
                else:
                    logging.warning("Unexpected document field not present in schema: {}".format(self._append_path(path_prefix, field)))


    def _validate_value(self, value, field_spec, path, errors):
        """Validates that the given field value is valid given the associated
        field spec and path. Any validation failures are added to the given errors
        collection."""

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
                self._validate_instance_against_schema(value, field_type, errors, path)
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


    def _apply_schema_defaults(self, schema, instance):
        """Applies the defaults described by the given schema to the given
        document instance as appropriate. Defaults are only applied to
        fields which are currently unset."""

        for field, spec in schema.doc_spec.iteritems():

            # Determine if a value already exists for the field
            if field in instance:
                value = instance[field]

                # recurse into nested collections
                if isinstance(spec, list):
                    if isinstance(value, list) and isinstance(spec[0], Schema):
                        for item in value:
                            self._apply_schema_defaults(spec[0], item)

                # recurse into nested docs
                elif isinstance(spec['type'], Schema) and isinstance(value, dict):
                    self._apply_schema_defaults(spec['type'], value)

                # Bailout as we don't want to apply a default
                continue

            # Apply a default if one is available
            if isinstance(spec, dict) and 'default' in spec:
                default = spec['default']
                if callable(default):
                    instance[field] = default()
                else:
                    instance[field] = default
