from mongothon.queries import ScopeBuilder
from mongothon.scopes import where
from unittest import TestCase
from mock import Mock, call
from .fake import FakeCursor


class TestScopeBuilder(TestCase):
    def test_bad_scope(self):
        """Test that we detect a scope which returns nothing"""
        mock_model = Mock()

        def bad_scope():
            pass

        bldr = ScopeBuilder(mock_model, [bad_scope])

        with self.assertRaises(ValueError):
            bldr.bad_scope()


    def test_scope_builder_returns_another_scope_builder(self):
        mock_model = Mock()

        def sample_scope():
            return {"thing": "blah"}

        bldr = ScopeBuilder(mock_model, [sample_scope])
        bldr2 = bldr.sample_scope()
        self.assertIsInstance(bldr2, ScopeBuilder)
        self.assertNotEqual(bldr, bldr2)
        self.assertEquals({}, bldr.query)
        self.assertEquals({"thing": "blah"}, bldr2.query)


    def test_scope_builder_with_projection_and_options(self):
        mock_model = Mock()

        def sample_scope():
            return ({"thing": "blah"},
                    {"thing": 1, "other": 1},
                    {"limit": 5})

        bldr = ScopeBuilder(mock_model, [sample_scope]).sample_scope()
        self.assertIsInstance(bldr, ScopeBuilder)
        self.assertEquals({"thing": "blah"}, bldr.query)
        self.assertEquals({"thing": 1, "other": 1}, bldr.projection)
        self.assertEquals({"limit": 5}, bldr.options)


    def test_chained_scope_query_building(self):
        mock_model = Mock()

        def scope_a():
            return {"thing": "blah"}

        def scope_b():
            return {"woo": "ha"}, {"ezy": "e"}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        bldr = bldr.scope_a().scope_b()
        self.assertEquals({"thing": "blah", "woo": "ha"},
                          bldr.query)
        self.assertEquals({"ezy": "e"}, bldr.projection)

    def test_last_query_wins_in_chained_scopes(self):
        mock_model = Mock()

        def scope_a():
            return {"thing": "blah"}, {}, {"limit": 5}

        def scope_b():
            return {"thing": "pish"}, {}, {"limit": 10}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        bldr = bldr.scope_a().scope_b()
        self.assertEquals({"thing": "pish"},
                          bldr.query)
        self.assertEquals({"limit": 10}, bldr.options)

    def test_queries_are_deep_merged_with_chained_scopes(self):
        mock_model = Mock()

        def scope_a():
            return {"thing": {"$elemMatch": {'somefield': 1}}}

        def scope_b():
            return {"thing": {"$elemMatch": {'someotherfield': 10}}}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        bldr = bldr.scope_a().scope_b()
        self.assertEquals({"thing": {"$elemMatch": {'somefield': 1,
                                                    'someotherfield': 10}}},
                          bldr.query)

    def test_queries_combined_with_where_scope(self):
        mock_model = Mock()

        def scope_a():
            return {"thing": {"$elemMatch": {'somefield': 1}}}

        def scope_b():
            return {"thing": {"$elemMatch": {'someotherfield': 10}}}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b, where])
        bldr = bldr.scope_a().scope_b().where({'a': 'b'})
        self.assertEquals({"thing": {"$elemMatch": {'somefield': 1,
                                                    'someotherfield': 10}},
                           'a': 'b'},
                          bldr.query)

    def test_queries_with_lists_are_deep_merged_with_chained_scopes(self):
        mock_model = Mock()

        def scope_a():
            return {"thing": {"$in": [1, 2, 3]}}

        def scope_b():
            return {"thing": {"$in": [3, 4, 5]}}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        bldr = bldr.scope_a().scope_b()
        self.assertEquals({"thing": {"$in": [1, 2, 3, 4, 5]}},
                          bldr.query)

    def test_queries_with_lists_of_dicts_are_deep_merged_with_chained_scopes(self):
        mock_model = Mock()

        def scope_a():
            return {"thing": {"$all": [{"$elemMatch": {"size": "M"}}]}}

        def scope_b():
            return {"thing": {"$all": [{"$elemMatch": {"num": 100}}]}}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        bldr = bldr.scope_a().scope_b()
        self.assertEquals({"thing": {"$all": [{"$elemMatch": {"size": "M"}},
                                              {"$elemMatch": {"num": 100}}]}},
                          bldr.query)

    def test_calls_back_to_model_when_getting_cursor(self):
        mock_model = Mock()
        cursor = Mock()
        mock_model.find.return_value = cursor

        def scope_a():
            return {"thing": "blah"}, {}, {"sort": True}

        def scope_b():
            return {"woo": "ha"}, {"icecube": 1}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        results = bldr.scope_a().scope_b().cursor
        mock_model.find.assert_called_once_with(
            {"thing": "blah", "woo": "ha"},
            {"icecube": 1},
            sort=True)
        self.assertEquals(cursor, results)

    def test_iterate(self):
        mock_model = Mock()
        cursor = FakeCursor([{'_id': 1}, {'_id': 2}])
        mock_model.find.return_value = cursor

        def scope_a():
            return {"thing": "blah"}

        def scope_b():
            return {"woo": "ha"}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        results = bldr.scope_a().scope_b()
        it = results.__iter__()
        self.assertEqual({'_id': 1}, it.next())
        self.assertEqual({'_id': 2}, it.next())
        mock_model.find.assert_called_once_with(
            {"thing": "blah", "woo": "ha"},
            None)

    def test_index(self):
        mock_model = Mock()
        cursor = FakeCursor([{'_id': 1}, {'_id': 2}])
        mock_model.find.return_value = cursor

        def scope_a():
            return {"thing": "blah"}

        def scope_b():
            return {"woo": "ha"}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        self.assertEqual({'_id': 2}, bldr.scope_a().scope_b()[1])
        mock_model.find.assert_called_once_with(
            {"thing": "blah", "woo": "ha"},
            None)

    def test_convert_to_list(self):
        mock_model = Mock()
        cursor = FakeCursor([{'_id': 1}, {'_id': 2}])
        mock_model.find.return_value = cursor

        def scope_a():
            return {"thing": "blah"}

        def scope_b():
            return {"woo": "ha"}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        lst = list(bldr.scope_a().scope_b())
        self.assertEqual([{'_id': 1}, {'_id': 2}], lst)
        mock_model.find.assert_called_once_with(
            {"thing": "blah", "woo": "ha"},
            None)

    def test_call_mongo_cursor_methods(self):
        mock_model = Mock()
        cursor = FakeCursor([{'_id': 1}, {'_id': 2}])
        mock_model.find.return_value = cursor

        def scope_a():
            return {"thing": "blah"}

        def scope_b():
            return {"woo": "ha"}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        result = bldr.scope_a().scope_b()
        self.assertEqual(result.count(), 2)
        self.assertEqual(result.limit(1), cursor)
        mock_model.find.assert_called_once_with(
            {"thing": "blah", "woo": "ha"},
            None)

    def test_extending_scope_chain_after_cursor_access(self):
        mock_model = Mock()
        cursor_a = FakeCursor([{'_id': 1}, {'_id': 2}])
        cursor_b = FakeCursor([{'_id': 1}])

        mock_model.find.side_effect = [cursor_a, cursor_b]

        def scope_a():
            return {"thing": "blah"}

        def scope_b():
            return {"woo": "ha"}

        bldr = ScopeBuilder(mock_model, [scope_a, scope_b])
        result_a = bldr.scope_a()

        self.assertEqual(result_a.count(), 2)
        self.assertEqual(result_a[1], {'_id': 2})
        self.assertEqual(result_a.limit(1), cursor_a)

        result_b = result_a.scope_b()
        self.assertEqual(result_b.count(), 1)
        self.assertEqual(result_b[0], {'_id': 1})
        self.assertEqual(result_b.limit(1), cursor_b)

        self.assertEqual([
            call({"thing": "blah"}, None),
            call({"thing": "blah", "woo": "ha"}, None)
        ], mock_model.find.mock_calls)


    def test_unpack_scope_with_just_query(self):
        bldr = ScopeBuilder(Mock(), [])
        query, projection, options = bldr.unpack_scope({"thing": "blah"})
        self.assertEqual({"thing": "blah"}, query)
        self.assertEqual({}, projection)
        self.assertEqual({}, options)

    def test_unpack_scope_with_query_and_projection(self):
        bldr = ScopeBuilder(Mock(), [])
        query, projection, options = bldr.unpack_scope(({"thing": "blah"}, {"thing": 1}))
        self.assertEqual({"thing": "blah"}, query)
        self.assertEqual({"thing": 1}, projection)
        self.assertEqual({}, options)

    def test_unpack_scope_with_all_options(self):
        bldr = ScopeBuilder(Mock(), [])
        query, projection, options = bldr.unpack_scope(({"thing": "blah"}, {"thing": 1}, {"limit": 5}))
        self.assertEqual({"thing": "blah"}, query)
        self.assertEqual({"thing": 1}, projection)
        self.assertEqual({"limit": 5}, options)

    def test_unpack_scope_missing_no_data(self):
        bldr = ScopeBuilder(Mock(), [])

        with self.assertRaises(ValueError):
            bldr.unpack_scope(None)

    def test_unpack_scope_too_many_args(self):
        bldr = ScopeBuilder(Mock(), [])

        with self.assertRaises(ValueError):
            bldr.unpack_scope(({}, {}, {}, {}))
