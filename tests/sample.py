"""Provides a valid sample set of schemas and documents adhereing to those
schemas for use in testing."""

from mongothon import Schema, Mixed
from mongothon.validators import one_of
from datetime import datetime
from bson.objectid import ObjectId


def stubnow():
    return datetime(2012, 4, 5)

name_schema = Schema({
    "first":    {"type": basestring, "required": True},
    "last":     {"type": basestring, "required": True}
})

# TEST SCHEMAS
comment_schema = Schema({
    "commenter":    {"type": name_schema, "required": True},
    "email":        {"type": basestring, "required": False},
    "comment":      {"type": basestring, "required": True},
    "votes":        {"type": int, "default": 0}
})

blog_post_schema = Schema({
    "author":           {"type": name_schema, "required": True},
    "content":          {"type": Schema({
        "title":            {"type": basestring, "required": True},
        "text":             {"type": basestring, "required": True},
        "page_views":       {"type": int, "default": 1}
    }), "required": True},
    "category":         {"type": basestring, "validates":one_of("cooking", "politics")},
    "comments":         [comment_schema],
    "likes":            {"type": int, "default": 0},
    "creation_date":    {"type": datetime, "default": stubnow},
    "tags":             [basestring],
    "misc":             {"type": Mixed(basestring, int)},
    "linked_id":        {"type": Mixed(int, basestring)},
    "publication_id":   {"type": ObjectId}
})


def valid_doc(overrides=None):
    doc = {
        "author": {
            "first":    "John",
            "last":     "Humphreys"
        },
        "content": {
            "title": "How to make cookies",
            "text": "First start by pre-heating the oven..."
        },
        "category": "cooking",
        "comments": [
            {
                "commenter": {
                    "first": "Julio",
                    "last": "Cesar"
                },
                "email": "jcesar@test.com",
                "comment": "Great post dude!"
            },
            {
                "commenter": {
                    "first": "Michael",
                    "last": "Andrews"
                },
                "comment": "My wife loves these."
            }
        ],
        "tags": ["cookies", "recipe", "yum"]
    }
    if overrides:
        doc.update(overrides)
    return doc


# The expected version of the document once it has been saved to the DB,
# including the use of Unicode and applied defaults.
def expected_db_doc(object_id):
    return {
        u"_id": object_id,
        u"author": {
            u"first":    u"John",
            u"last":     u"Humphreys"
        },
        u"content": {
            u"title": u"How to make cookies",
            u"text": u"First start by pre-heating the oven...",
            u"page_views": 1
        },
        u"category": u"cooking",
        u"comments": [
            {
                u"commenter": {
                    u"first": u"Julio",
                    u"last": u"Cesar"
                },
                u"email": u"jcesar@test.com",
                u"comment": u"Great post dude!",
                u"votes": 0
            },
            {
                u"commenter": {
                    u"first": u"Michael",
                    u"last": u"Andrews"
                },
                u"comment": u"My wife loves these.",
                u"votes": 0
            }
        ],
        u"likes": 0,
        u"tags": [u"cookies", u"recipe", u"yum"],
        u"creation_date": stubnow()
    }
