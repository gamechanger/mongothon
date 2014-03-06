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

Mongothon allows you to couple reusable schemas (based on the [Schemer](http://github.com/gamechanger/schemer) API) with Model classes which can be used in your application to perform IO with your associated Mongo collection.

## Example

Define the Mongo document structure and constraints in a Schema:
```python
from mongothon import Schema

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
car = Car({
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

Schemas in Mongothon are based almost completely on the Schema class provided by the [Schemer](http://github.com/gamechanger/schemer) library. Take a look at the [Schemer](http://github.com/gamechanger/schemer) docs for details of how to describe your document's structure, validation rules and defaults.

For convenience, Mongothon offers it's own `Schema` subclass which includes standard Schemer functionality but adds support for Mongo "_id" fields.

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

#### Validating documents
You can validate a document against its Schema by simply calling `validate` on the document instance:
```python
order.validate()  # raises a ValidationException is the document is invalid
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
Custom instance methods can be added to a model using the model's `instance_method` decorator. This comes in handy when you want to wrap up common operations on a document:

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
orders = Order.before(datetime(2012, 1, 1)).single_item()
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

orders = Order.item_named('iPhone').item_priced_lt(500).item_priced_gt(200)

# Resultant query:
#   {"items": {
#       "$elemMatch": {
#           "name": "iPhone",
#           "price": {"$gt": 200, "$lt": 500}
#       }
#   }}

```

Other notes:
 - If you have multiple queries specifying a list of values (e.g. as part of an $in statement) for the same field, Mongothon will combine the two lists for you. `{'tags': {'$in': ['red', 'blue']}` + `{'tags': {'$in': ['green', 'blue']}` => `{'tags': {'$in': ['red', 'blue', 'green']}`
 - Even with deep merging, if you attempt to combine two queries which specify different values for matching a field, the last scope in the chain will win.

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

Once the query context has been built up, it will executed as soon as the caller attempts to access the results.

```python
# Finds all BlogPosts with a given author, only returning their IDs
posts = BlogPost.author("bob").id_only()

# The actual query is only executed against Mongo when we attempt access
first = posts[0]
```

The builder API which allows scopes to be chained together in this manner implements the Python iterator protocol as well:

```python
for post in BlogPost.author("bob").id_only():
    # Do something
```

You can call any pymongo `Cursor` method via the scope builder:

```python
num_posts_by_bob = BlogPost.author("bob").count()

ten_posts_by_bob = BlogPost.author("bob").limit(10)
```

Furthermore, scopes can be further refined even after you have performed access on them:

```python
posts = BlogPost.author('bob')
print "Bob has written a total of {} posts".format(posts.count())

gardening_posts = posts.tagged('gardening')
print "{} of these are about gardening".format(gardening_posts.count())
```

### Events

Mongothon Models emit events at various points in the lifecycle of a model instance. You can register one or more handler functions for a given event against the model class. These functions are then invoked at the point a model instance emits the event.

To register a function to receive an event, use the `on` model class method, either by calling it directly passing your handler function, or as a decorator:

```python

def log_save(blog_post):
    logging.info('Blog post {} was saved!'.format(blog_post['_id']))

# Register the handler function
BlogPost.on('did_save', log_save)

...

@BlogPost.on('did_save')
def log_save(blog_post):
    logging.info('Blog post {} was saved!'.format(blog_post['_id']))
```

#### Implementing handler functions

A valid event handler function should always expect to receive:
 - the model instance from which the event is being emitted as it's first argument
 - any other specific arguments associated with the given event (see below for a list of standard events and their additional arguments).

```python
@BlogPost.on('did_remove')
def log_remove(blog_post, *args, **kwargs):
    logging.info('Blog post {} was removed!'.format(blog_post['_id']))

@BlogPost.on('did_update')
def log_update(blog_post, document, *args, **kwargs):
    logging.info('Blog post {} was updated using document'.format(blog_post['_id'], document))

```

When emitting custom events (see below for more details), this allows essentially any arguments to be passed to all handlers registered for that event.

```python
@BlogPost.on('archived')
def log_archived(blog_post, archived_by):
    logging.info('Blog post {} was archived by {}'.format(blog_post['_id'], archived_by))

...

def archive_blog_post(post_id, user_email):
    blog_post = BlogPost.find_by_id(post_id)
    blog_post['archived'] = True
    blog_post.save()
    blog_post.emit('archived', archived_by=user_email)
```

#### Standard events

Every Mongothon model emits the following events as part of its lifecycle:

| Event | Additional args | Description |
| ----- | --------------- | ----------- |
| `'did_init'` | None | Emitted whenever a new model object instance is initialized. |
| `'did_find'` | None | Emitted when a model object is instantiated as the result of database lookup. Fires after `'did_init'`. |
| `'will_validate`' | None | Emitted just before a model is validated against it's schema. |
| `'did_validate`' | None | Emitted just after a model is validated against it's schema. |
| `'will_apply_defaults'` | None | Emitted just before defaults (from the associated schema) are applied to the `Model` instance .|
| `'did_apply_defaults'` | None | Emitted just after defaults (from the associated schema) are applied to the `Model` instance .|
| `'will_save'` | None | Emitted just before a model is saved to the database. Fires _after_ validation (and it's associated events). |
| `'did_save'` | None | Emitted just after a model is saved to the database. |
| `'will_update'` | All arguments provided to `update_instance()`. | Emitted just before an `update` is performed for the given model instance. |
| `'did_update'` | All arguments provided to `update_instance()`. | Emitted just after an `update` is performed for the given model instance. |
| `'will_remove'` | All arguments provided to `remove()`. | Emitted just before an `remove` is performed for the given model instance. |
| `'did_remove'` | All arguments provided to `remove()`. | Emitted just after an `remove` is performed for the given model instance. |


##### Working copy event arguments

`'will_validate'`, `'did_validate'` and `'will_save'` events include a `working` argument which is a working copy of the model instance. To properly understand what this argument is, it is useful to think about the steps Mongothon goes through when saving a Mongothon `Model` instance:

1. A working (deep) copy of the model instance is created.
2. Any schema default values are applied to the working copy, without affecting the primary object instance.
3. The working copy is validated against the model's schema.
4. If validation passes, an attempt is made to save the working copy to the underlying database collection.
5. If the database save operation succeeds, the working copy is merged back into the primary object instance so that it reflects the document in the collection.

So for these events which receive the `working` argument, depending on the model's schema it is possible that this object may contain different values to the primary model instance.

Also note that if you want to implement any universal "pre-save" updates to the model just before it is saved (e.g. updating a 'modified' timestamp), you can do this simply by manipulating the working copy.

#### Emitting custom events

As well as the standard set of events listed above which are emitted by models, it's also possible to use the `Model` event bus for any custom events you want to emit.

To emit a custom event, just invoke `emit` on a give  model instance passing a string to identify the type of event, along with any custom arguments which are relevant to that event.

(Note that you don't need to pass the model instance itself as an argument to `emit`).

```python
post = BlogPost.find_by_id(post_id)
post.emit('loaded', datetime.utcnow())
```

Generally speaking, rather than emitting events directly from your model-consuming code, a better pattern is to implement an `@instance_method` on your `Model` which wraps up some operation and emit an event from within that method.

To handle a custom event, just register a handler function in the same way you would for a standard event:

```python
BlogPost.on('loaded')
def log_load(post, loaded_time):
    logging.debug('Loaded post {} at {}'.format(post['_id'], loaded_time))
```

#### Removing event handlers

Sometimes it is desirable to be able to remove event handlers from a Model (e.g. for testing purposes). Models expose a few methods to make this easy:

```python
BlogPost.on('did_save', log_save)
BlogPost.on('did_save', inc_save_count)
BlogPost.on('did_find', log_find)

# Inspect what handlers are registered for a given event
BlogPost.handlers('did_save')  # => [<function log_save>, <function inc_save_count>]

# Remove a given handler
BlogPost.remove_handler('did_save', log_save)

# Remove all handlers registered against a given event
BlogPost.remove_all_handlers('did_save')

# Remove all handlers registered against a given list of events
BlogPost.remove_all_handlers('did_save', 'did_find')

# Remove all handlers registered all events
BlogPost.remove_all_handlers()

```


### Change Tracking

It's useful often to know which fields on a Model have changed, for example when determining if some secondary process needs to be initiated as a result of that change.

Mongothon allows you easily inspect which fields and list items have been added / changed / removed at all parts of your Model object graph.

#### Changing field values
```python

blog_post = BlogPost.find_by_id(id)
blog_post['author']     # => 'Bob Smith'

# Change a field value
blog_post['author'] = 'John Davies'

# `changed` returns a dict of changed fields and their current values
blog_post.changed       # => {'author': 'John Davies'}

# `changes` returns a dict of changed fields and their previous / current values as a tuple
blog_post.changes       # => {'author': ('Bob Smith', 'John Smith')}

# Because non-empty dicts evaluate to True, `changed` can be used in `if` statements
if blog_post.changed:
    print "Blog post changed!"
```

#### Adding a new field

```python

# Add a new field
'views' in blog_post    # => False
blog_post['views'] = 12

# `added` returns a dict of added fields and their values
blog_post.added         # => {'views': 12}

```

#### Deleting a field
```python
# Delete a field
del blog_post['title']

# `deleted` returns a dict of fields which have been deleted and their values
blog_post.deleted       # => {'title': 'How to get ahead in software engineering'}
```

#### Saving and Reloading
Saving and reloading resets the tracked changes.
```python
blog_post = BlogPost.find_by_id(id)
blog_post['author'] = 'Dave Jones'
blog_post.changed           # => {'author': 'Dave Jones'}
blog_post.save()
blog_post.changed           # => {}
```

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
assert post.is_deleted()
```

# Developing and Contributing

To run Mongothon's tests, simply run `python setup.py nosetests` at the command line.

All contributions submitted as GitHub pull requests are warmly received.
