def one_of(*args):
    if len(args) == 1 and isinstance(args[0], list):
        items = tuple(args[0])
    else:
        items = args

    """Validates that the field value is in the given list."""
    def validate(value):
        if not value in items:
            return "'{0}' is not in the list {1}".format(value, items)
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


def gt(gt_value):
    def validate(value):
        if value <= gt_value:
            return "Value must be greater than {0}".format(gt_value)
    return validate


def lt(lt_value):
    def validate(value):
        if value >= lt_value:
            return "Value must be less than {0}".format(lt_value)
    return validate


def between(min_value, max_value):
    def validate(value):
        if value < min_value:
            return "{0} is less than the minimum value of {1}".format(value, min_value)
        if value > max_value:
            return "{0} is greater than the maximum value of {1}".format(value, max_value)
    return validate
