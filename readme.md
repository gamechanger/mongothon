# Mongothon

Mongothon is a MongoDb object-document mapping API for Python, loosely based on the awesome mongoose.js library. 


## Quick Start

Mongothon allows you to declaratively express the structure and contraints of your Mongo document in a reusable Schema using Python dicts. Schemas can then be used to generate reusable Model classes which can be used in your application to perform IO with your associated Mongo collection.

### Example:

```python
# Define our document structure and constraints in a Schema
car_schema = Schema({
    "make":         {"type": basestring, "required": True},
    "model":        {"type": basestring, "required": True},
    "num_wheels":   {"type": int, "default": 4, "validates": gte(0)}
    "color":        {"type": basestring, "validates": one_of("red", "green", "blue")}
})


# Define a virtual field on our schema
car_schema.virtual("description", getter=lambda doc: "{0} {1}".format(doc.make, doc.model))


# Generate a reusable model class from the Schema and pymongo collection
Car = create_model(car_schema, db['car'])


# Find, modify and save a document
car = Car.find_by_id(some_id)
car.color = "green"
car.save()


# Create a new document
car = new Car({
    "make":     "Ford",
    "model":    "F-150",
    "color":    "red"
})
car.save()


# Delete a document
car.delete()


# Validate a document
car = new Car({
    "make":         "Ford",
    "model":        "F-150",
    "num_wheels":   -1
    "color":        "red"
})

try:
    car.validate()
except ValidationException:
    # num_wheels should be >= 0

```
