def _validate_instance_against_schema(instance, schema, path_prefix, errors):
    # Loop over each field in the schema and check the instance value conforms
    # to its spec
    for field, spec in schema.doc_spec.iteritems():
        value = instance.get(field, None)

        if path_prefix:
            path = "{0}.{1}".format(path_prefix, field)
        else:
            path = field

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


    def _verify_spec(self):
        """Verifies that the given schema document spec is valid."""
        _verify_schema_validity(self, None)

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


