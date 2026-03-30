"""Unit tests for common.py — 100% branch coverage."""
import inspect
import io
import types
import importlib.util
import pytest
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock
from pathlib import Path
from hypothesis import given, settings, HealthCheck
from hypothesis.errors import Unsatisfiable
import hypothesis.strategies as st

import common
from common import (
    load_module_from_path,
    get_common_functions,
    get_common_classes,
    get_display_name,
    _json_type_to_strategy,
    infer_strategy,
    _get_candidate_values,
    _type_to_strategy,
    smart_infer_arg_strategies,
)


# ---------------------------------------------------------------------------
# load_module_from_path
# ---------------------------------------------------------------------------

def test_load_module_success(tmp_path):
    f = tmp_path / "mymod.py"
    f.write_text("def hello(): return 'hi'")
    mod = load_module_from_path(str(f), "mymod")
    assert mod.hello() == "hi"


def test_load_module_spec_none_raises():
    with patch("importlib.util.spec_from_file_location", return_value=None):
        with pytest.raises(ImportError, match="Could not load module"):
            load_module_from_path("/fake/path.py", "fake")


def test_load_module_loader_none_raises():
    mock_spec = MagicMock()
    mock_spec.loader = None
    with patch("importlib.util.spec_from_file_location", return_value=mock_spec):
        with pytest.raises(ImportError, match="Could not load module"):
            load_module_from_path("/fake/path.py", "fake")


# ---------------------------------------------------------------------------
# get_common_functions
# ---------------------------------------------------------------------------

def _make_module(name, func_names):
    """Create a real module object with functions defined in it."""
    mod = types.ModuleType(name)
    mod.__name__ = name
    for fn_name in func_names:
        code = f"def {fn_name}(): pass"
        exec(code, mod.__dict__)  # noqa: S102
        getattr(mod, fn_name).__module__ = name
    return mod


def test_get_common_functions_overlap():
    m1 = _make_module("mod1", ["foo", "bar"])
    m2 = _make_module("mod2", ["bar", "baz"])
    result = get_common_functions(m1, m2)
    assert result == ["bar"]


def test_get_common_functions_no_overlap():
    m1 = _make_module("mod1", ["foo"])
    m2 = _make_module("mod2", ["bar"])
    assert get_common_functions(m1, m2) == []


def test_get_common_functions_filters_imported():
    """Functions whose __module__ doesn't match are excluded."""
    m1 = _make_module("mod1", ["foo"])
    m2 = _make_module("mod2", ["foo"])
    # Make foo in m2 look like it was imported from somewhere else
    m2.foo.__module__ = "some_other_module"
    assert get_common_functions(m1, m2) == []


# ---------------------------------------------------------------------------
# get_common_classes
# ---------------------------------------------------------------------------

def _make_module_with_class(name, cls_names):
    mod = types.ModuleType(name)
    mod.__name__ = name
    for cls_name in cls_names:
        cls = type(cls_name, (), {"__module__": name})
        setattr(mod, cls_name, cls)
    return mod


def test_get_common_classes_overlap():
    m1 = _make_module_with_class("mod1", ["Foo", "Bar"])
    m2 = _make_module_with_class("mod2", ["Bar", "Baz"])
    result = get_common_classes(m1, m2)
    assert result == ["Bar"]


def test_get_common_classes_no_overlap():
    m1 = _make_module_with_class("mod1", ["Foo"])
    m2 = _make_module_with_class("mod2", ["Bar"])
    assert get_common_classes(m1, m2) == []


def test_get_common_classes_filters_imported():
    """Classes whose __module__ doesn't match are excluded."""
    m1 = _make_module_with_class("mod1", ["Foo"])
    m2 = _make_module_with_class("mod2", ["Foo"])
    m2.Foo.__module__ = "external"
    assert get_common_classes(m1, m2) == []


# ---------------------------------------------------------------------------
# get_display_name
# ---------------------------------------------------------------------------

def test_display_name_no_config():
    assert get_display_name("foo") == "foo"


def test_display_name_path_prefix_exact():
    config = {"functions": {"path/to/file.py:foo": ["int"]}}
    assert get_display_name("foo", config) == "path/to/file.py:foo"


def test_display_name_path_prefix_qualname():
    config = {"functions": {"path/to/file.py:MyClass.method": ["int"]}}
    assert get_display_name("MyClass.method", config) == "path/to/file.py:MyClass.method"


def test_display_name_no_match_in_functions():
    config = {"functions": {"path/to/file.py:other": ["int"]}}
    assert get_display_name("foo", config) == "foo"


def test_display_name_source_files_backward_compat():
    config = {"source_files": {"foo": "path/to/file.py"}}
    assert get_display_name("foo", config) == "path/to/file.py:foo"


def test_display_name_source_files_miss():
    config = {"source_files": {"other": "path/to/file.py"}}
    assert get_display_name("foo", config) == "foo"


# ---------------------------------------------------------------------------
# _json_type_to_strategy
# ---------------------------------------------------------------------------

@given(_json_type_to_strategy("int(1, 10)"))
def test_json_type_int_range(val):
    assert 1 <= val <= 10


@given(_json_type_to_strategy("int(-5, 5)"))
def test_json_type_int_range_negative(val):
    assert -5 <= val <= 5


@given(_json_type_to_strategy("int(bad, val)"))
def test_json_type_int_range_bad_parse(val):
    # "int(bad, val)" — ValueError in int() → falls back to st.integers() | st.text() fallback
    assert isinstance(val, (int, str))


@given(_json_type_to_strategy("int"))
@settings(max_examples=1)
def test_json_type_int(val):
    assert isinstance(val, int)


@given(_json_type_to_strategy("float"))
@settings(max_examples=1)
def test_json_type_float(val):
    assert isinstance(val, float)


@given(_json_type_to_strategy("str"))
@settings(max_examples=1)
def test_json_type_str(val):
    assert isinstance(val, str)


@given(_json_type_to_strategy("string"))
@settings(max_examples=1)
def test_json_type_string(val):
    assert isinstance(val, str)


@given(_json_type_to_strategy("bool"))
@settings(max_examples=1)
def test_json_type_bool(val):
    assert isinstance(val, bool)


@given(_json_type_to_strategy("list"))
@settings(max_examples=1)
def test_json_type_list(val):
    assert isinstance(val, list)


@given(_json_type_to_strategy("dict"))
@settings(max_examples=1)
def test_json_type_dict(val):
    assert isinstance(val, dict)


@given(_json_type_to_strategy("none"))
@settings(max_examples=1)
def test_json_type_none(val):
    assert val is None


@given(_json_type_to_strategy("unknown_xyz"))
@settings(max_examples=1)
def test_json_type_fallback(val):
    assert isinstance(val, (int, str))


@given(_json_type_to_strategy("INT(1,5)"))
def test_json_type_case_insensitive(val):
    assert 1 <= val <= 5


# ---------------------------------------------------------------------------
# infer_strategy
# ---------------------------------------------------------------------------

@given(st.data())
@settings(max_examples=1)
def test_infer_strategy_int_annotation(data):
    def f(x: int): pass
    param = list(inspect.signature(f).parameters.values())[0]
    strat = infer_strategy(param)
    val = data.draw(strat)
    assert isinstance(val, int)


@given(st.data())
@settings(max_examples=1)
def test_infer_strategy_str_annotation(data):
    def f(x: str): pass
    param = list(inspect.signature(f).parameters.values())[0]
    strat = infer_strategy(param)
    val = data.draw(strat)
    assert isinstance(val, str)


def test_infer_strategy_from_type_fails_fallback():
    """When st.from_type raises, falls back to one_of (lines 120-121)."""
    def f(x: int): pass
    param = list(inspect.signature(f).parameters.values())[0]
    # Temporarily make annotation non-int so we enter the st.from_type path,
    # then mock it to raise
    class MyType:
        pass

    def g(x: MyType): pass
    param2 = list(inspect.signature(g).parameters.values())[0]
    with patch("common.st.from_type", side_effect=Exception("cannot resolve")):
        strat = infer_strategy(param2)
    assert strat is not None


def test_infer_strategy_no_annotation():
    def f(x): pass
    param = list(inspect.signature(f).parameters.values())[0]
    strat = infer_strategy(param)
    assert strat is not None


# ---------------------------------------------------------------------------
# _get_candidate_values
# ---------------------------------------------------------------------------

def test_get_candidate_values():
    vals = _get_candidate_values()
    assert isinstance(vals, list)
    assert len(vals) > 0
    assert 1 in vals
    assert True in vals
    assert None in vals
    assert {} in vals
    assert [] in vals


# ---------------------------------------------------------------------------
# _type_to_strategy
# ---------------------------------------------------------------------------

@given(st.data())
@settings(max_examples=1)
def test_type_to_strategy_bool(data):
    strat = _type_to_strategy(True)
    val = data.draw(strat)
    assert isinstance(val, bool)


@given(st.data())
@settings(max_examples=1)
def test_type_to_strategy_int(data):
    strat = _type_to_strategy(42)
    val = data.draw(strat)
    assert isinstance(val, int)


@given(st.data())
@settings(max_examples=1)
def test_type_to_strategy_float(data):
    strat = _type_to_strategy(1.5)
    val = data.draw(strat)
    assert isinstance(val, float)


@given(st.data())
@settings(max_examples=1)
def test_type_to_strategy_str(data):
    strat = _type_to_strategy("hello")
    val = data.draw(strat)
    assert isinstance(val, str)


@given(st.data())
@settings(max_examples=1)
def test_type_to_strategy_none(data):
    strat = _type_to_strategy(None)
    val = data.draw(strat)
    assert val is None


@given(st.data())
@settings(max_examples=1)
def test_type_to_strategy_list(data):
    strat = _type_to_strategy([1, 2])
    val = data.draw(strat)
    assert isinstance(val, list)


@given(st.data())
@settings(max_examples=1)
def test_type_to_strategy_dict(data):
    strat = _type_to_strategy({"a": 1})
    val = data.draw(strat)
    assert isinstance(val, dict)


@given(st.data())
@settings(max_examples=1)
def test_type_to_strategy_other(data):
    obj = object()
    strat = _type_to_strategy(obj)
    val = data.draw(strat)
    assert val is obj


# ---------------------------------------------------------------------------
# smart_infer_arg_strategies
# ---------------------------------------------------------------------------

@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority1_type_hints(data):
    """Priority 1: all params typed → use type hints."""
    def typed_func(x: int, y: str) -> bool:
        return True

    strat = smart_infer_arg_strategies(typed_func)
    example = data.draw(strat)
    assert isinstance(example, tuple)
    assert len(example) == 2
    assert isinstance(example[0], int)
    assert isinstance(example[1], str)


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority2a_path_prefix_qualname(data):
    """Priority 2a: config key ends with :qualname."""
    def untyped(x, y):
        return x + y

    config = {"functions": {f"path/to/file.py:{untyped.__qualname__}": ["int", "int"]}}
    buf = io.StringIO()
    with redirect_stdout(buf):
        strat = smart_infer_arg_strategies(untyped, config=config)
    assert "[INFO] Found config entry" in buf.getvalue()
    example = data.draw(strat)
    assert len(example) == 2
    assert isinstance(example[0], int)


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority2b_path_prefix_name(data):
    """Priority 2b: config key ends with :name (not qualname)."""
    def untyped(x, y):
        return x + y

    # Use name only (not qualname) in path-prefixed key
    config = {"functions": {"path/file.py:untyped": ["int", "int"]}}
    strat = smart_infer_arg_strategies(untyped, config=config)
    example = data.draw(strat)
    assert len(example) == 2


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority2c_direct_qualname(data):
    """Priority 2c: direct qualname match in config."""
    def untyped(x, y):
        return x + y

    config = {"functions": {untyped.__qualname__: ["int", "int"]}}
    strat = smart_infer_arg_strategies(untyped, config=config)
    example = data.draw(strat)
    assert len(example) == 2


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority2d_direct_name(data):
    """Priority 2d: direct name match in config (when qualname doesn't match)."""
    def untyped(x, y):
        return x + y

    # Override qualname to something that won't match, use name as key
    config = {"functions": {"untyped": ["int", "int"]}}
    strat = smart_infer_arg_strategies(untyped, config=config)
    example = data.draw(strat)
    assert len(example) == 2


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority3_no_args(data):
    """Priority 3: zero args → returns empty tuples strategy."""
    def no_args():
        return 42

    strat = smart_infer_arg_strategies(no_args)
    example = data.draw(strat)
    assert example == ()


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority3_probe_le3(data):
    """Priority 3 probe: num_args <= 3, finds valid inputs."""
    def accepts_int(x):
        if not isinstance(x, (int, float, bool)):
            raise TypeError
        return x * 2

    strat = smart_infer_arg_strategies(accepts_int)
    example = data.draw(strat)
    assert len(example) == 1


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority3_probe_gt3_all_same(data):
    """Priority 3 probe: num_args > 3 exercises all-same path."""
    def accepts_many(a, b, c, d):
        if not all(isinstance(v, int) for v in [a, b, c, d]):
            raise TypeError
        return a + b + c + d

    strat = smart_infer_arg_strategies(accepts_many)
    example = data.draw(strat)
    assert len(example) == 4


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority3_probe_gt3_first_n(data):
    """Priority 3 probe: first-N path (candidates[:n]) — line 255.
    Uses a function that fails all-same but succeeds with (1, 0, -1, 1.5)."""
    def needs_mixed(a, b, c, d):
        # Only accepts exactly (1, 0, -1, 1.5) — fails all-same combos
        if a == b == c == d:
            raise ValueError("all same")
        if a != 1:
            raise ValueError
        return True

    strat = smart_infer_arg_strategies(needs_mixed)
    example = data.draw(strat)
    assert len(example) == 4


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_priority3_probe_gt3_break_at_100(data):
    """Priority 3 probe: random loop breaks at >100 working signatures — line 266."""
    def very_permissive(a, b, c, d):
        # Accepts any args — fills working_signatures fast via random trials
        return (a, b, c, d)

    strat = smart_infer_arg_strategies(very_permissive)
    example = data.draw(strat)
    assert len(example) == 4


def test_smart_infer_priority3_no_valid_raises():
    """Priority 3: probe finds nothing → raises Unsatisfiable."""
    def impossible(x):
        raise RuntimeError("always fails")

    with pytest.raises(Unsatisfiable):
        smart_infer_arg_strategies(impossible)


@given(st.data())
@settings(max_examples=1)
def test_smart_infer_self_excluded(data):
    """'self' param is excluded from param count."""
    class Foo:
        def method(self, x: int) -> int:
            return x

    strat = smart_infer_arg_strategies(Foo().method)
    example = data.draw(strat)
    assert len(example) == 1
    assert isinstance(example[0], int)
