from inflection import camelize
from document import Document
from model import Model, NotFoundException
from schema import Schema, Mixed, ValidationException

def create_model(schema, collection, class_name=None):
    if not class_name:
        class_name = camelize(str(collection.name))
    return type(
        class_name,
        (Model,),
        dict(schema=schema, collection=collection))
