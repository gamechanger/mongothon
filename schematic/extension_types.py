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
