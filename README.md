# Mongothon

Mongothon is a MongoDB object-document mapping API for Python, loosely based on the awesome [mongoose.js](http://mongoosejs.com/) library.

![build status](https://travis-ci.org/tleach/mongothon.png?branch=master "Build status")

# Installation

Install via easy_install:
```
easy_install mongothon
```
Or, via pip:
```
pip install mongothon
```

# Getting Started

Mongothon allows you to declaratively express the structure and contraints of your Mongo document in a reusable Schema using Python dicts. Schemas can then be used to generate reusable Model classes which can be used in your application to perform IO with your associated Mongo collection.

## Example

Define the Mongo document structure and constraints in a Schema:
```python
car_schema = Schema({
    "make":         {"type": basestring, "required": True},
    "model":        {"type": basestring, "required": True},
    "num_wheels":   {"type": int,        "default": 4, "validates": gte(0)}
    "color":        {"type": basestring, "validates": one_of("red", "green", "blue")}
})
```

Define a virtual field on the schema:
```python
car_schema.virtual("description", getter=lambda doc: "{0} {1}".format(doc.make, doc.model))
```

Generate a reusable model class from the Schema and pymongo collection:
```python
Car = create_model(car_schema, db['car'])
```

Find, modify and save a document:
```python
car = Car.find_by_id(some_id)
car.color = "green"
car.save()
```

Create a new document:
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

# API Reference

## Schemas

### Types

Each field in a Mongothon schema must be given a type by adding a `"type"` key to the field spec dict. For example, this schema declares a single `"name"` field with a type of `basestring`:
```python
schema = Schema({"name": {"type": basestring}})
```
Supported field types are: `basestring`, `int`, `float`, `datetime`, `long`, `bool`, `Schema` (see Nested schemas below) and `Mixed`. 

#### The "Mixed" type
The `Mixed` type allows you to indicate that a field supports values of multiple types. Use of this type is generally not encouraged (consistent field typing makes life easier) but is sometimes necessary.
`Mixed` can be provided as a class to indicate a value of any supported type may be used in a given field:
```python
schema = Schema({"misc": {"type": Mixed}})  # all types are valid in this field
```
You can also instantiate `Mixed` with a list of sub-types to indicate that a value of one of a subset of supported types may be used in the field:
```python
schema = Schema({"external_id": {"type": Mixed(basestring, int, ObjectId)}})  # only basestring, int and ObjectId are supported
```

If you attempt to save a model containing a value of the wrong type for a given a field a `ValidationException` will be thrown.

### Mandatory fields
You can require a field to be present in a document by adding `"required": True` to the Schema:
```python
schema = Schema({"name": {"type": basestring, "required": True}})
```
By default all fields are not required.
If `save()` is called on model which does not contain a value for a required field then the model will raise a `ValidationException`.

### Defaults
Schemas allow you to specify default values for fields which are used in the event a value is not provided in a given document.
A default can either be specified as literal:
```python
schema = Schema({"num_wheels": {"type": int, "default": 4}})
```
or as a reference to parameterless function which will be called at the point the document is saved:
```python
import datetime
schema = Schema({"created_date": {"type": datetime, "default": datetime.now}})
```

### Validation
Mongothon allows you to specify validation for a field using the `"validates"` key in the field spec. 
You can specify a single validator:
```python
schema = Schema({"color": {"type": basestring, "validates": one_of("red", "green", "blue")}})
```
or multiple validators:
```python
schema = Schema({"num_wheels": {"type": int, "validates": [gte(0), lte(6)]}})
```

#### Provided validators
Mongothon provides the following validators out-of-the-box:
```python
# Validator                         # Validates that the field...
gte(value)                          # is greater than or equal to the given value
lte(value)                          # is less than or equal to the given value
gt(value)                           # is greater than the given value
lt(value)                           # is less than the given value
between(min_value, max_value)       # is between the given min and max values
length(min_length, [max_length])    # is at least the given min length and (optionally) at most the given max length 
match(pattern)                      # matches the given regex pattern
one_of(values...)                   # is equal to one of the given values
is_url()                            # is a valid URL
is_email()                          # is a valid email address
```

#### Creating custom validators
In addition to the provided validators it's easy to create your own custom validators. 
To create a custom validator:
 - declare a function which accepts any arguments you want to provide to the validation algorithm
 - the function should itself return a function which will ultimately be called by Mongothon when validating a field value. The function should:
    - accept a single argument - the field value being validated
    - return nothing if the given value is valid
    - return a string describing the validation error if the value is invalid

Here's the declaration of an example custom validator:
```python
def startswith(prefix):
    def validate(value):
        if not value.startswith(prefix):
            return "String must start with %s" % prefix

# Usage:
schema = Schema({"full_name": {"type": basestring, "validates": startswith("Mr")}})
```

### Nested schemas
Schemas may be nested within one another in order to describe the structure of documents containing deep graphs. 

Nested can either be declared inline:
```python
blog_post_schema = Schema({
    "author":   {"type": Schema({"first_name": {"type": basestring}, "last_name": {"type": basestring}})},
    "title":    {"type": basestring},
    "content":  {"type": basestring}
})

```
or declared in isolation and then referenced (and potentially reused between multiple parent schemas):
```python
name_schema = Schema({
    "first_name":   {"type": basestring}, 
    "last_name":    {"type": basestring}
})

blog_post_schema = Schema({
    "author":   {"type": name_schema},
    "title":    {"type": basestring},
    "content":  {"type": basestring}
})

comment_schema = Schema({
    "author":   {"type": name_schema, "required":True},
    "comment":  {"type": base_string}
})

```
In each case the nested schema is provided as the `type` parameter in the parent field's spec and can be declared as `"required"=True` if so desired. Any validation present within the nested schema is applied wherever the schema
is used.


### Embedded collections
As well as nesting schemas directly under fields, Mongothon supports embedded collections within documents. To declare an embedded collection, simply declare the type of the embedded items using Python list syntax:
```python
line_item_schema = Schema({
    "price":        {"type": int, "required": True}
    "item_name":    {"type": basestring, "required": True} 
})

order_schema = Schema({
    "line_items":   [line_item_schema]
    "total_due":    {"type": int}
})
```
Simple primitive types can be embedded as well as full schemas:
```python
bookmark_schema = Schema({
    "url":      {"type": basestring},
    "tags":     [basestring]
})
```

### Virtual fields
Mongothon supports defining virtual fields on schemas through the registration of named getter and setter functions.Virtual fields are useful when you want to provide a view over a document's fields without needing to store the derived view as a separate field in the database. 

To declare a virtual field, register a getter and/or setter function on the schema:
```python
name_schema = Schema({
    "first_name":   {"type": basestring}, 
    "last_name":    {"type": basestring}
})

def get_full_name(doc):
    return "%s %s" % (doc.first_name, doc.last_name)

def set_full_name(value, doc):
    doc.first_name, doc.last_name = value.split(" ")

name_schema.virtual("full_name", getter=get_full_name, setter=set_full_name)
```

Getter functions receive the document as the one and only argument and should return the value of the virtual field for that document.

Setter functions receive the value being set and destination document as arguments. The setter should update the document as appropriate from the given value.

## Models
Where Schemas are used to declare the structure and constraints of a Mongo document, Models allow those Schemas to be used in interacting with the database to enforce that document structure.

### Creating a model class
To create a new model class from an existing schema, use the `create_model` method:
```python
Order = create_model(order_schema, db['orders'])
```
The second argument which must be provided to `create_model` is the PyMongo collection object associated with the underlying MongoDB collection to be associated with the model. 

### Class methods
Model classes provide a number of class methods which can be used to interact with the underlying collection as a whole.

#### Finding documents
Model classes can be used to find individual documents by ID:
```python
order = Order.find_by_id(some_id)  # returns an instance of Order
```
or using a search condition:
```python
order = Order.find_one({'total_due': {'$gte': '10'}})  # returns an instance of Order
```
Selections of documents can also be retrieved using search criteria:
```python
order = Order.find({'total_due': {'$gte': '10'}})  # returns a cursor containing Order instances
```

#### Updating documents
Model classes can be used to perform updates on the collection:
```python
Order.update({'total_due': {'$gte': '10'}}, {'$unset': {'line_items': 1}})
```

#### Counting items
```python
Order.count()
```

### Instance methods
Instances of models allow documents to be easily created, manipulated, save and deleted.

#### Creating documents
Create a new instance of a model by passing the document as a Python dict into the constructor:
```python
order = Order({
    "line_items": [
        {"item_name": "iPhone 5", "price": 200},
        {"item_name": "Mac Mini", "price": 500}
    ],
    "total_due": 700
})
```
#### Manipulating documents
Document fields can be updated via model instance properties which are automatically available:
```python
order.line_items[1].item_name = "Mac Mini Gen. 2"
```

#### Saving documents
In order to persist document changes to the DB, the model can be saved:
```python
order.save()
```
Saving an existing, previously loaded document will cause it to be updated. Saving a new document will cause it to be inserted. 
In all cases, saving a document results in schema defaults being applied where appropriate and the document being validated before it is saved to the database. In the event of a validation failure `save()` will raise a ValidationException.

#### Deleting documents
A document may be removed from the underlying collection by calling the `delete()` method on the associated model instance:
```python
order = Order.find_by_id(some_id)
order.delete()  # document is removed from the DB
```

## Middleware

Models allow you to register middleware functions which will be passed flow control at various specific points in the lifecycle of a model. 

Currently supported middleware events are:

`before_save` - called just before a document is saved
`after_save` - called just after a document is saved
`before_validate` - called just before a document is validated
`after_validate` - called just after a document is validated

In each case the registered middleware function will be passed the document object. 

Example:
```python
def log_saved(doc):
    logging.info("Saved order {0}", doc._id)

# Register the function
Order.after_save(log_saved)
```
There is no limit to the number of middleware functions which can be registered.


# Developing and Contributing

To run Mongothon's tests, simply run `python setup.py nosetests` at the command line.

All contributions submitted as GitHub pull requests are warmly received.
