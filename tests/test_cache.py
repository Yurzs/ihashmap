from collections import UserDict
from unittest.mock import MagicMock

import pytest

from smart_cache.cache import Action, Cache, Pipeline


@pytest.fixture
def fake_cache():
    return {}


@pytest.fixture
def fake_get(fake_cache):
    def _get(name, key, default):
        return fake_cache[name].get(key, default)

    return _get


@pytest.fixture
def fake_set(fake_cache):
    def _set(name, key, value):
        fake_cache.setdefault(name, {})[key] = value
        return value

    return _set


@pytest.fixture
def fake_update(fake_cache):
    return fake_cache.update


@pytest.fixture
def fake_delete(fake_cache):
    def _delete(key):
        del fake_cache[key]

    return _delete


def test_Action_execute_before():

    mocked_function = MagicMock()
    action = Action(mocked_function)
    action.execute_before({}, "fake")
    assert mocked_function.called
    assert mocked_function.call_count == 1
    assert mocked_function.call_args[0] == ({}, "fake")


def test_Action_execution_after():
    mocked_function = MagicMock()
    action = Action(mocked_function)
    call_args = ({"fake_context": True}, {"_id": "1234"})
    action.execute_after(*call_args)
    assert mocked_function.called
    assert mocked_function.call_count == 1
    assert mocked_function.call_args[0] == call_args


def test_Pipeline___call__():
    pipe = Pipeline()

    assert len(pipe.pipe_before) == 0
    assert len(pipe.pipe_after) == 0
    mocked_function = pipe.add_action("before")(MagicMock())
    assert len(pipe.pipe_before) == 1
    assert len(pipe.pipe_after) == 0

    @pipe
    def test_func(cls, name, key, value):
        pass

    test_func("fake1", "fake2", "fake3", "fake4")

    assert mocked_function.called
    assert mocked_function.call_count == 1
    assert mocked_function.call_args[0] == ({}, "fake1", "fake2", "fake3", "fake4")


def test_Pipeline_add_action():
    pipe = Pipeline()

    assert len(pipe.pipe_before) == 0
    assert len(pipe.pipe_after) == 0
    mocked_function = pipe.add_action("before")(MagicMock())
    assert len(pipe.pipe_before) == 1
    assert len(pipe.pipe_after) == 0

    # TODO: check for function in pipes

    @pipe.add_action("before")
    def test_func():
        pass

    assert len(pipe.pipe_before) == 2
    assert len(pipe.pipe_after) == 0

    @pipe.add_action("after")
    def test_func2():
        pass

    assert len(pipe.pipe_before) == 2
    assert len(pipe.pipe_after) == 1


def test_Cache_register_get_method(fake_get):

    assert Cache.GET_METHOD != fake_get
    Cache.register_get_method(fake_get)
    assert Cache.GET_METHOD == fake_get


def test_Cache_register_set_method(fake_set):
    assert Cache.SET_METHOD != fake_set
    Cache.register_set_method(fake_set)
    assert Cache.SET_METHOD == fake_set


def test_Cache_register_update_method(fake_update):
    assert Cache.UPDATE_METHOD != fake_update
    Cache.register_update_method(fake_update)
    assert Cache.UPDATE_METHOD == fake_update


def test_Cache_register_delete_method(fake_delete):
    assert Cache.DELETE_METHOD != fake_delete
    Cache.register_delete_method(fake_delete)
    assert Cache.DELETE_METHOD == fake_delete


def test_Cache_search(fake_cache, fake_set, fake_get, fake_delete, fake_update):

    Cache.register_set_method(fake_set)
    Cache.register_update_method(fake_update)
    Cache.register_get_method(fake_get)
    Cache.register_delete_method(fake_delete)

    entity = UserDict({"_id": "12345", "test_key": "test_value"})
    Cache.set("test", "12345", entity)

    assert "12345" in fake_cache["test"]
    assert fake_cache["test"]["12345"] == entity
    assert len(fake_cache["test"]) == 2

    assert Cache.search("test", {"_id": "12345"}) == [entity]
    assert Cache.search("test", {"_id": "12345", "success": "True"}) == []
    assert Cache.search("test", {"success": True}) == []
    assert Cache.search("test", {"_id": lambda _id: _id in ["4322", "12345"]}) == [
        entity
    ]