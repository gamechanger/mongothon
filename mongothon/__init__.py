import inspect
from inflection import camelize
from document import Document
from model import Model, NotFoundException
from schema import Schema, IndexSpec
from schemer import Mixed, ValidationException, Array


def _module_name_from_previous_frame(num_frames_back):
    """
    Returns the module name associated with a frame `num_frames_back` in the
    call stack. This function adds 1 to account for itself, so `num_frames_back`
    should be given relative to the caller.
    """
    frm = inspect.stack()[num_frames_back + 1]
    return inspect.getmodule(frm[0]).__name__


def create_model(schema, collection, class_name=None):
    """
    Main entry point to creating a new mongothon model. Both
    schema and Pymongo collection objects must be provided.

    Returns a new class which can be used as a model class.

    The class name of the model class by default is inferred
    from the provided collection (converted to camel case).
    Optionally, a class_name argument can be provided to
    override this.
    """
    if not class_name:
        class_name = camelize(str(collection.name))

    model_class = type(class_name,
                       (Model,),
                       dict(schema=schema, _collection_factory=staticmethod(lambda: collection)))

    # Since we are dynamically creating this class here, we modify __module__ on the
    # created class to point back to the module from which `create_model` was called
    model_class.__module__ = _module_name_from_previous_frame(1)

    return model_class


def create_model_offline(schema, collection_factory, class_name):
    """
    Entry point for creating a new Mongothon model without instantiating
    a database connection. The collection is instead provided through a closure
    that is resolved upon the model's first database access.
    """
    model_class = type(class_name,
                       (Model,),
                       dict(schema=schema, _collection_factory=staticmethod(collection_factory)))

    # Since we are dynamically creating this class here, we modify __module__ on the
    # created class to point back to the module from which `create_model_offline` was called
    model_class.__module__ = _module_name_from_previous_frame(1)

    return model_class
