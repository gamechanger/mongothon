import os
from pymongo.connection import Connection
import unittest
from mongothon import create_model
from sample import blog_post_schema, valid_doc, expected_db_doc
from contextlib import contextmanager

host = os.environ.get("DB_IP", "localhost")
port = int(os.environ.get("DB_PORT", 27017))


def get_db(*args, **kwargs):
    return Connection(host, port, *args, **kwargs).mongothon_test

blog_post_collection = get_db().blog_post
BlogPost = create_model(blog_post_schema, blog_post_collection)


class TestPyMongoIntegration(unittest.TestCase):
    """Test that when we use a model against an actual database using
    pymongo, everything works as it should."""
    def setUp(self):
        self.maxDiff = None

    def tearDown(self):
        blog_post_collection.remove()

    @contextmanager
    def assert_no_difference(self, func):
        """Context manager which asserts the given function returns the
        same value either side of the wrapped block."""
        before = func()
        yield
        after = func()
        self.assertEqual(before, after)

    @contextmanager
    def assert_difference(self, func, difference):
        """Context manager which asserts that the given function returns values
        which differ by the given amount before and after the yield block."""
        before = func()
        yield
        after = func()
        self.assertEqual(before + difference, after)

    def test_save_then_load_new_document(self):
        blog_post = BlogPost(valid_doc())
        with self.assert_difference(blog_post_collection.count, 1):
            blog_post.save()
        self.assertIsNotNone(blog_post._id)

        reloaded_blog_post = BlogPost.find_by_id(blog_post._id)
        self.assertDictEqual(
            expected_db_doc(blog_post._id), reloaded_blog_post)

    def test_does_not_persist_invalid_document(self):
        blog_post = BlogPost(valid_doc())
        del blog_post['author']
        with self.assert_no_difference(blog_post_collection.count):
            try:
                blog_post.save()
            except:
                pass

    def test_remove_document(self):
        BlogPost(valid_doc()).save()
        BlogPost(valid_doc()).save()
        blog_post = BlogPost(valid_doc())
        blog_post.save()
        with self.assert_difference(blog_post_collection.count, -1):
            blog_post.remove()

    def test_update_existing_document(self):
        blog_post = BlogPost(valid_doc())
        blog_post.save()
        blog_post.author.first = "Troy"
        with self.assert_no_difference(blog_post_collection.count):
            blog_post.save()
        # Reload to check the change is there
        reloaded_blog_post = BlogPost.find_by_id(blog_post._id)
        expected = expected_db_doc(blog_post._id)
        expected['author']['first'] = u"Troy"
        self.assertDictEqual(
            expected, reloaded_blog_post)

    def test_find_and_modify_selection(self):
        for i in range(5):
            BlogPost(valid_doc()).save()
        posts = BlogPost.find()
        self.assertEquals(posts.count(), 5)
        post = posts[0]
        del post['author']
        try:
            post.validate()
        except:
            pass  # expected

    def test_find_query(self):
        for i in range(10):
            BlogPost(valid_doc({"likes": i})).save()
        posts = BlogPost.find({"likes": {"$gte": 5}})
        self.assertEquals(5, posts.count())

    def test_update(self):
        other = BlogPost(valid_doc())
        other.save()
        blog_post = BlogPost(valid_doc())
        blog_post.save()
        blog_post.update({"likes": 5})
        reloaded_blog_post = BlogPost.find_by_id(blog_post._id)
        reloaded_other_blog_post = BlogPost.find_by_id(other._id)
        self.assertEqual(5, reloaded_blog_post.likes)
        self.assertEqual(0, reloaded_other_blog_post.likes)

    def test_count(self):
        for i in range(5):
            BlogPost(valid_doc()).save()
        self.assertEqual(5, BlogPost.count())

    def test_find_one(self):
        for i in range(10):
            BlogPost(valid_doc({"likes": i})).save()
        post = BlogPost.find_one({"likes": {"$gte": 5}})
        self.assertIsInstance(post, BlogPost)
