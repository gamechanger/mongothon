# Mongothon

Mongothon is a MongoDB object-document mapping API for Python, loosely based on the awesome [mongoose.js](http://mongoosejs.com/) library.

[![build status](https://travis-ci.org/gamechanger/mongothon.png?branch=master "Build status")](https://travis-ci.org/gamechanger/mongothon)

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

Generate a reusable model class from the Schema and pymongo collection:
```python
Car = create_model(car_schema, db['car'])
```

Find, modify and save a document:
```python
car = Car.find_by_id(some_id)
car['color'] = "green"
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

Remove a document
```python
car.remove()
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
                                   # or throws NotFoundException
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
Mongothon two mechanisms to run updates against documents.

##### `Model.update` (static method)
The class method version of `update` is essentially a proxy for the underlying Pymongo collection object's `update` method and can be
called as such.
```python
Order.update({'total_due': {'$gte': 700}}, {'$unset': {'line_items': 1}})
```

##### `model.update_instance` (instance method)
The instance method `update_instance` makes it easy to run an update statement against the current model document by defaulting the `query` used to `{'_id': self['_id']}`.
```python
order = Order.find_by_id(some_id)
order.update_instance({'$unset': {'line_items': 1}})
```

###### Note
`model.update` (instance method) will delegate to python's dictionary API:
```python
order = Order.find_by_id(some_id)
order.update({'line_items': 1})
print order['line_items']  # 1
```

#### Counting items
```python
Order.count()
```

#### Custom class methods
You can dynamically add custom class methods to your model by using the model's `class_method` decorator function. These are useful for adding custom finder methods to your model:

```python
@BlogPost.class_method
def find_by_author(cls, author):
    return cls.find({"author": author})

posts = BlogPost.find_by_author("Jeff Atwood")
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

#### Saving documents
In order to persist document changes to the DB, the model can be saved:
```python
order.save()
```
Saving an existing, previously loaded document will cause it to be updated. Saving a new document will cause it to be inserted.
In all cases, saving a document results in schema defaults being applied where appropriate and the document being validated before it is saved to the database. In the event of a validation failure `save()` will raise a ValidationException.

#### Deleting documents
A document may be removed from the underlying collection by calling the `remove()` method on the associated model instance:
```python
order = Order.find_by_id(some_id)
order.remove()  # document is removed from the DB
```

#### Reload
You can easily reload a model instance from the database by calling the `reload` method on an instance:
```python
order = Order.find_by_id(some_id)
...
order.reload()
```


#### Custom instance methods
Custom instance methods can be added to a model using the model's `instance_method` decorator. This comes in useful when you want to wrap up common operations on a document:

```python
@Order.instance_method
def add_line_item(self, name, price):
    self.line_items.append({'item_name': name, 'price': price})

order = Order.find_by_id(some_id)
order.add_line_item("iPad Mini", 300)
order.save()
```

### "Scopes" (beta)

Scopes are a dynamic way of attaching reusable sets of query options to a model which can then be chained together dynamically in order to run actual queries against the model's underlying collection.

For example:
```python
@Order.scope
def before(date):
    return {"created_date": {"$lt": date}}

@Order.scope
def single_item():
    return {"items": {"$size": 1}}

# Obtains a list of orders which were created before 20120101 which have a single line item.
orders = Order.before(datetime(2012, 1, 1)).single_item().execute()
```

#### Combining queries with nested criteria

When dealing with multiple chained scopes, Mongothon uses a "deep merge, last query wins" approach to combine multiple query dicts into a single query dicts. This ensures that queries with nested query elements may be combined just as easily as simple key-value queries.

Examples:
```python
@Order.scope
def item_priced_lt(price):
    return {"items": {
        "$elemMatch": {
            "price": {"$lt": price}
        }
    }}

@Order.scope
def item_priced_gt(price):
    return {"items": {
        "$elemMatch": {
            "price": {"$gt": price}
        }
    }}

@Order.scope
def item_named(name:
    return {"items": {
        "$elemMatch": {
            "name": name
        }
    }}

orders = Order.item_named('iPhone').item_priced_lt(500).item_priced_gt(200).execute()

# Resultant query:
#   {"items": {
#       "$elemMatch": {
#           "name": "iPhone",
#           "price": {"$gt": 200, "$lt": 500}
#       }
#   }}

```

Also note: If you have multiple queries specifying a list of values (e.g. as part of an $in statement) for the same field, Mongothon will combine the two lists for you.

#### Implementing scope functions

A "scope" function is simply a function which returns up to three return values:
 - A query dict
 - A projection dict
 - An options dict, containing a list of kwargs suitable for passing to PyMongo's `find` method.

A scope is registered with a given model by using the model's `scope` decorator.

Some example scopes:
```python
@BlogPost.scope
def author(name):
    """A scope which restricts the query to only blog posts by the given author"""
    return {"name": name}

@BlogPost.scope
def id_only():
    """Only return the ID from the query"""
    return {}, {"_id": 1}

@BlogPost.scope
def by_created_date():
    """Sorts the query results by created date"""
    return {}, {}, {"sort": ["created_date", 1]}
```

#### Using scopes

Scope functions, once registered to a given model, can be called on the model class to dynamically build up a query context in a chainable manner.

Once the query context has been built it can be executed as an actual query against the database by calling `execute()`.

```python
# Finds all BlogPosts with a given author, only returning their IDs
posts = BlogPost.author("bob").id_only().execute()
```

The builder API which allows scopes to be chained together in this manner also implements a Python iterator which will call `execute()` behind the scenes if you attempt to index into it:

```python
for post in BlogPost.author("bob").id_only():
    # Do something
```

### Middleware

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


### Model State

Mongothon models provide a few handy methods which let you determine the document's current persistence state:

```python
post = BlogPost()
assert post.is_new()

post.save()
assert not post.is_new()
assert post.is_persisted()

post.remove()
assert not post.is_new()
assert not post.is_persisted()
assert port.is_deleted()
```

# Developing and Contributing

To run Mongothon's tests, simply run `python setup.py nosetests` at the command line.

All contributions submitted as GitHub pull requests are warmly received.
