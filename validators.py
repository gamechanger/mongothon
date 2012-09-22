def one_of(*args):
    """Validates that the field value is in the given list."""
    def validate(value):
        if not value in args:
            return "'{0}' is not in the list {1}".format(value, args)
    return validate


def gte(min_value):
    def validate(value):
        if value < min_value:
            return "{0} is less than the minimum value of {1}".format(value, min_value)
    return validate


def lte(max_value):
    def validate(value):
        if value > max_value:
            return "{0} is greater than the maximum value of {1}".format(value, max_value)
    return validate
