from document import Document
from model import Model, NotFoundException
from schema import Schema, Mixed, ValidationException

def create_model(schema, collection):
    return type("Model", (Model,), dict(schema=schema, collection=collection))
