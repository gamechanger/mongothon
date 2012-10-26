# Mongothon

Mongothon is a MongoDB object-document mapping API for Python, loosely based on the awesome [mongoose.js](http://mongoosejs.com/) library. 


## Quick Start

Mongothon allows you to declaratively express the structure and contraints of your Mongo document in a reusable Schema using Python dicts. Schemas can then be used to generate reusable Model classes which can be used in your application to perform IO with your associated Mongo collection.

### Example

Define the Mongo document structure and constraints in a Schema:
```python
car_schema = Schema({
    "make":         {"type": basestring, "required": True},
    "model":        {"type": basestring, "required": True},
    "num_wheels":   {"type": int,        "default": 4, "validates": gte(0)}
    "color":        {"type": basestring, "validates": one_of("red", "green", "blue")}
})
```
Define a virtual field on the schema
```python
car_schema.virtual("description", getter=lambda doc: "{0} {1}".format(doc.make, doc.model))
```
Generate a reusable model class from the Schema and pymongo collection
```python
Car = create_model(car_schema, db['car'])
```
Find, modify and save a document
```python
car = Car.find_by_id(some_id)
car.color = "green"
car.save()
```
Create a new document
```python
car = new Car({
    "make":     "Ford",
    "model":    "F-150",
    "color":    "red"
})
car.save()
```
Delete a document
```python
car.delete()
```
Validate a document
```python
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



