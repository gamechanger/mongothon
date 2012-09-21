def one_of(*args):
    """Validates that the field value is in the given list."""
    def validate(value):
        if not value in args:
            return "'{0}'' is not in list {1}".format(value, args)
    return validate

