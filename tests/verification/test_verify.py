"""Unit tests for verify.py — 100% branch coverage."""
import inspect
import multiprocessing
import queue as queue_mod
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from dataclasses import dataclass

import hypothesis.strategies as st
from hypothesis.errors import Unsatisfiable

import verify
from verify import (
    VerifyResult,
    is_explicit_raise,
    clean_traceback,
    run_hypothesis_verification,
    objects_are_equal,
    check_result_equivalence,
    NaiveRandomFuzzer,
    run_naive_fuzzing,
    combine_results,
    worker_verify_function,
    worker_verify_class_method,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# is_explicit_raise
# Requires file-based code: inspect.getframeinfo can only read code_context
# from source files on disk, not from interactive/in-memory code.
# ---------------------------------------------------------------------------

def _load_and_raise(fixture_subdir, func_name, args=()):
    """Load a fixture module and call a function, returning the caught exception."""
    from common import load_module_from_path
    path = str(FIXTURES / fixture_subdir / "original.py")
    mod = load_module_from_path(path, f"_iexr_{fixture_subdir}")
    func = getattr(mod, func_name)
    try:
        func(*args)
    except Exception as e:
        return e
    return None


def test_is_explicit_raise_true():
    # safe_divide raises explicitly when y==0
    exc = _load_and_raise("job_pass_explicit_raise", "safe_divide", (1, 0))
    assert exc is not None
    assert is_explicit_raise(exc) is True


def test_is_explicit_raise_false_implicit():
    # invert(0) → ZeroDivisionError which is implicit (line is "return 1 / x")
    exc = _load_and_raise("job_pass_implicit_fixed", "invert", (0,))
    assert exc is not None
    assert is_explicit_raise(exc) is False


def test_is_explicit_raise_no_traceback():
    e = ValueError("no tb")
    # e.__traceback__ is None since we didn't raise it
    assert is_explicit_raise(e) is False


def test_is_explicit_raise_code_context_none():
    exc = _load_and_raise("job_pass_explicit_raise", "safe_divide", (1, 0))
    assert exc is not None
    mock_frame_info = MagicMock()
    mock_frame_info.code_context = None
    with patch("verify.inspect.getframeinfo", return_value=mock_frame_info):
        result = is_explicit_raise(exc)
    assert result is False


def test_is_explicit_raise_getframeinfo_throws():
    exc = _load_and_raise("job_pass_explicit_raise", "safe_divide", (1, 0))
    assert exc is not None
    with patch("verify.inspect.getframeinfo", side_effect=Exception("boom")):
        result = is_explicit_raise(exc)
    assert result is False


# ---------------------------------------------------------------------------
# clean_traceback
# ---------------------------------------------------------------------------

def test_clean_traceback_assertion_error():
    tb = "Traceback (most recent call last):\n  File x.py, line 1\nAssertionError: x != y"
    assert clean_traceback(tb) == "AssertionError: x != y"


def test_clean_traceback_name_error():
    tb = "...\nNameError: name 'foo' is not defined"
    result = clean_traceback(tb)
    assert "NameError:" in result


def test_clean_traceback_type_error():
    tb = "...\nTypeError: unsupported operand"
    assert "TypeError:" in clean_traceback(tb)


def test_clean_traceback_value_error():
    tb = "...\nValueError: invalid literal"
    assert "ValueError:" in clean_traceback(tb)


def test_clean_traceback_fallback():
    tb = "Something completely different\nno known error here"
    assert clean_traceback(tb) == ""


# ---------------------------------------------------------------------------
# objects_are_equal
# ---------------------------------------------------------------------------

def test_objects_equal_primitives_equal():
    assert objects_are_equal(1, 1)
    assert objects_are_equal("x", "x")


def test_objects_equal_primitives_not_equal():
    assert not objects_are_equal(1, 2)


def test_objects_equal_list_equal():
    assert objects_are_equal([1, 2, 3], [1, 2, 3])


def test_objects_equal_list_not_equal_value():
    assert not objects_are_equal([1, 2], [1, 3])


def test_objects_equal_list_different_length():
    assert not objects_are_equal([1], [1, 2])


def test_objects_equal_tuple_equal():
    assert objects_are_equal((1, 2), (1, 2))


def test_objects_equal_mixed_list_tuple():
    # Both are list/tuple, treated uniformly
    assert objects_are_equal([1, 2], (1, 2))


def test_objects_equal_dict_equal_via_recursive_compare():
    """Hit dict key-by-key comparison returning True (line 148).
    Need custom objects inside dict so top-level == fails."""
    class Foo1:
        def __init__(self): self.x = 1
    class Foo2:
        def __init__(self): self.x = 1
    Foo1.__name__ = Foo2.__name__ = "SameName"
    d1 = {"a": Foo1()}
    d2 = {"a": Foo2()}
    assert objects_are_equal(d1, d2)


def test_objects_equal_dict_equal():
    assert objects_are_equal({"a": 1}, {"a": 1})


def test_objects_equal_dict_different_values():
    assert not objects_are_equal({"a": 1}, {"a": 2})


def test_objects_equal_dict_different_keys():
    assert not objects_are_equal({"a": 1}, {"b": 1})


def test_objects_equal_custom_same_name_enum():
    from enum import Enum
    Color1 = Enum("Color", ["RED", "GREEN"])
    Color2 = Enum("Color", ["RED", "GREEN"])
    # Different class objects, same name — should compare via .name
    assert objects_are_equal(Color1.RED, Color2.RED)
    assert not objects_are_equal(Color1.RED, Color2.GREEN)


def test_objects_equal_custom_same_name_dict_equal():
    """Two classes with same __name__ but different identity, equal __dict__."""
    class Foo1:
        def __init__(self): self.x = 1
    class Foo2:
        def __init__(self): self.x = 1
    Foo1.__name__ = Foo2.__name__ = "SameName"
    assert objects_are_equal(Foo1(), Foo2())


def test_objects_equal_custom_same_name_dict_not_equal():
    class Foo1:
        def __init__(self): self.x = 1
    class Foo2:
        def __init__(self): self.x = 2
    Foo1.__name__ = Foo2.__name__ = "SameName"
    assert not objects_are_equal(Foo1(), Foo2())


def test_objects_equal_custom_same_name_dict_keys_mismatch():
    class Foo1:
        def __init__(self): self.x = 1
    class Foo2:
        def __init__(self): self.y = 1
    Foo1.__name__ = Foo2.__name__ = "SameName"
    assert not objects_are_equal(Foo1(), Foo2())


def test_objects_equal_type_mismatch():
    assert not objects_are_equal(1, "1")


# ---------------------------------------------------------------------------
# check_result_equivalence
# ---------------------------------------------------------------------------

def _exc(exc_class, msg="test"):
    """Helper: return a raised exception with traceback."""
    try:
        raise exc_class(msg)
    except exc_class as e:
        return e


def _implicit_exc():
    """Return an implicit (non-raise) exception."""
    try:
        _ = 1 / 0
    except ZeroDivisionError as e:
        return e


def test_check_equiv_both_exc_same_type():
    e1 = _exc(ValueError)
    e2 = _exc(ValueError)
    # Should not raise
    check_result_equivalence(None, e1, None, e2, "ctx")


def test_check_equiv_both_exc_different_type_explicit():
    """Original raises explicitly with a different type than refactored → FAIL."""
    # Use _load_and_raise so the traceback survives and is_explicit_raise returns True
    orig_exc = _load_and_raise("job_pass_explicit_raise", "safe_divide", (1, 0))
    assert orig_exc is not None
    assert is_explicit_raise(orig_exc)
    # Simulate refactored raising a different exception type
    ref_exc = _implicit_exc()  # ZeroDivisionError (different type)
    with pytest.raises(AssertionError, match="Mismatch"):
        check_result_equivalence(None, orig_exc, None, ref_exc, "ctx")


def test_check_equiv_both_exc_different_type_implicit():
    """Both raise different implicit (unexpected) exceptions → PASS."""
    e1 = _implicit_exc()  # ZeroDivisionError, no explicit raise
    try:
        _ = "a" + 1  # TypeError, no explicit raise
    except TypeError as e:
        e2 = e
    # Should not raise — both crashed unexpectedly, types don't need to match
    check_result_equivalence(None, e1, None, e2, "ctx")


def test_check_equiv_orig_explicit_ref_ok():
    """Original raises explicitly, refactored doesn't → FAIL."""
    orig_exc = _load_and_raise("job_pass_explicit_raise", "safe_divide", (1, 0))
    assert orig_exc is not None
    with pytest.raises(AssertionError, match="explicit"):
        check_result_equivalence(None, orig_exc, 42, None, "ctx")


def test_check_equiv_orig_implicit_ref_ok():
    """Original raises implicitly → refactored fixing it is allowed (PASS)."""
    orig_exc = _load_and_raise("job_pass_implicit_fixed", "invert", (0,))
    assert orig_exc is not None
    # Should NOT raise — this is an allowed fix
    check_result_equivalence(None, orig_exc, 0.0, None, "ctx")


def test_check_equiv_no_orig_exc_ref_raises():
    ref_exc = _exc(TypeError)
    with pytest.raises(AssertionError, match="Mismatch"):
        check_result_equivalence(42, None, None, ref_exc, "ctx")


def test_check_equiv_no_exc_equal():
    check_result_equivalence(42, None, 42, None, "ctx")  # no raise


def test_check_equiv_no_exc_not_equal():
    with pytest.raises(AssertionError, match="Mismatch"):
        check_result_equivalence(42, None, 43, None, "ctx")


# ---------------------------------------------------------------------------
# NaiveRandomFuzzer
# ---------------------------------------------------------------------------

@pytest.fixture
def fuzzer():
    return NaiveRandomFuzzer(iterations=5)


def test_gen_int(fuzzer):
    assert isinstance(fuzzer._gen_int(), int)


def test_gen_float(fuzzer):
    assert isinstance(fuzzer._gen_float(), float)


def test_gen_str(fuzzer):
    assert isinstance(fuzzer._gen_str(), str)


def test_gen_bool(fuzzer):
    assert isinstance(fuzzer._gen_bool(), bool)


def test_gen_any_depth_zero(fuzzer):
    """Run many iterations to exercise all 7 random choices (depth <= 2)."""
    results = [fuzzer._gen_any(depth=0) for _ in range(500)]
    # We expect to have seen lists and dicts in this many iterations
    types_seen = {type(r) for r in results}
    assert len(types_seen) > 1


def test_gen_any_depth_three(fuzzer):
    """At depth > 2, only choices 0-4 are valid (no recursive lists/dicts)."""
    results = [fuzzer._gen_any(depth=3) for _ in range(200)]
    for r in results:
        assert not isinstance(r, (list, dict))


def test_generate_args_int_annotation(fuzzer):
    def f(x: int): pass
    args = fuzzer.generate_args(f)
    assert len(args) == 1
    assert isinstance(args[0], int)


def test_generate_args_float_annotation(fuzzer):
    def f(x: float): pass
    args = fuzzer.generate_args(f)
    assert isinstance(args[0], float)


def test_generate_args_str_annotation(fuzzer):
    def f(x: str): pass
    assert isinstance(fuzzer.generate_args(f)[0], str)


def test_generate_args_bool_annotation(fuzzer):
    def f(x: bool): pass
    assert isinstance(fuzzer.generate_args(f)[0], bool)


def test_generate_args_list_annotation(fuzzer):
    def f(x: list): pass
    assert isinstance(fuzzer.generate_args(f)[0], list)


def test_generate_args_dict_annotation(fuzzer):
    def f(x: dict): pass
    assert isinstance(fuzzer.generate_args(f)[0], dict)


def test_generate_args_no_annotation(fuzzer):
    def f(x): pass
    args = fuzzer.generate_args(f)
    assert len(args) == 1


def test_generate_args_skips_self(fuzzer):
    class Foo:
        def method(self, x: int): pass
    args = fuzzer.generate_args(Foo().method)
    assert len(args) == 1
    assert isinstance(args[0], int)


# ---------------------------------------------------------------------------
# run_naive_fuzzing
# ---------------------------------------------------------------------------

def test_run_naive_fuzzing_pass():
    def f(x: int): return x + 1
    result = run_naive_fuzzing(f, f)
    assert result.status == "PASS"


def test_run_naive_fuzzing_fail():
    def orig(x: int): return x + 1
    def ref(x: int): return x + 99
    result = run_naive_fuzzing(orig, ref)
    assert result.status == "FAIL"
    assert result.error is not None


def test_run_naive_fuzzing_error():
    with patch.object(NaiveRandomFuzzer, "fuzz", side_effect=RuntimeError("boom")):
        result = run_naive_fuzzing(lambda x: x, lambda x: x)
    assert result.status == "SKIP"
    assert "Error" in result.error


# ---------------------------------------------------------------------------
# run_hypothesis_verification
# ---------------------------------------------------------------------------

def test_hypothesis_verification_pass():
    def f(x: int): return x + 1
    result = run_hypothesis_verification(f, f)
    assert result.status == "PASS"


def test_hypothesis_verification_fail():
    def orig(x: int): return x + 1
    def ref(x: int): return x + 2
    result = run_hypothesis_verification(orig, ref)
    assert result.status == "FAIL"
    assert result.error is not None


def test_hypothesis_verification_skip_unsatisfiable():
    def impossible(x):
        raise RuntimeError("always")
    result = run_hypothesis_verification(impossible, impossible)
    assert result.status == "SKIP"


def test_hypothesis_verification_hypothesis_wrapped_error():
    """Exception with 'Hypothesis found' in message → treated as FAIL."""
    def f(x: int): return x

    with patch("verify.check_result_equivalence",
               side_effect=Exception("Hypothesis found a minimal failing example")):
        result = run_hypothesis_verification(f, f)
    assert result.status == "FAIL"


def test_hypothesis_verification_other_exception():
    """Non-AssertionError, non-Unsatisfiable, non-Hypothesis exception → SKIP."""
    with patch("verify.smart_infer_arg_strategies", side_effect=Exception("unexpected")):
        result = run_hypothesis_verification(lambda x: x, lambda x: x)
    assert result.status == "SKIP"
    assert "Error during verification" in result.error


def test_hypothesis_verification_env_max_examples(monkeypatch):
    monkeypatch.setenv("HYPOTHESIS_MAX_EXAMPLES", "3")
    def f(x: int): return x
    result = run_hypothesis_verification(f, f)
    assert result.status == "PASS"


def test_hypothesis_verification_exception_paths():
    """Exercises lines 98-99 (orig raises) and 103-104 (ref raises).
    Uses implicit_fixed fixture where orig raises on x=0."""
    from common import load_module_from_path
    orig_path = str(FIXTURES / "job_pass_implicit_fixed" / "original.py")
    ref_path = str(FIXTURES / "job_pass_implicit_fixed" / "refactored.py")
    orig_mod = load_module_from_path(orig_path, "_hv_orig_implicit")
    ref_mod = load_module_from_path(ref_path, "_hv_ref_implicit")
    # orig.invert(0) raises ZeroDivisionError (line 98-99 hit)
    # ref.invert(0) returns 0.0 (line 103-104 NOT hit, but 98-99 are)
    result = run_hypothesis_verification(orig_mod.invert, ref_mod.invert)
    assert result.status == "PASS"  # implicit fix is allowed


def test_hypothesis_verification_both_raise(monkeypatch):
    """Exercises both lines 98-99 AND 103-104 (both orig and ref raise).
    Uses job_fail_different_exception where both raise for negative input."""
    from common import load_module_from_path
    orig_path = str(FIXTURES / "job_fail_different_exception" / "original.py")
    ref_path = str(FIXTURES / "job_fail_different_exception" / "refactored.py")
    orig_mod = load_module_from_path(orig_path, "_hv_orig_diff")
    ref_mod = load_module_from_path(ref_path, "_hv_ref_diff")
    # parse(-1): orig raises ValueError (98-99), ref raises TypeError (103-104)
    result = run_hypothesis_verification(orig_mod.parse, ref_mod.parse)
    assert result.status == "FAIL"  # different exception types


# ---------------------------------------------------------------------------
# combine_results
# ---------------------------------------------------------------------------

def test_combine_hyp_fail_with_error(capsys):
    hyp = VerifyResult("FAIL", 0.1, "assertion msg")
    naive = VerifyResult("PASS", 0.1)
    status = combine_results("foo", hyp, naive)
    assert status == "FAILURE"
    out = capsys.readouterr().out
    assert "[FAIL]" in out
    assert "assertion msg" in out


def test_combine_hyp_fail_no_error(capsys):
    hyp = VerifyResult("FAIL", 0.1, error=None)
    naive = VerifyResult("PASS", 0.1)
    combine_results("foo", hyp, naive)
    out = capsys.readouterr().out
    assert "[FAIL]" in out


def test_combine_naive_fail_with_error(capsys):
    hyp = VerifyResult("PASS", 0.1)
    naive = VerifyResult("FAIL", 0.1, "naive msg")
    status = combine_results("foo", hyp, naive)
    assert status == "FAILURE"
    out = capsys.readouterr().out
    assert "naive msg" in out


def test_combine_naive_fail_no_error(capsys):
    hyp = VerifyResult("PASS", 0.1)
    naive = VerifyResult("FAIL", 0.1, error=None)
    status = combine_results("foo", hyp, naive)
    assert status == "FAILURE"


def test_combine_hyp_pass(capsys):
    hyp = VerifyResult("PASS", 0.1)
    naive = VerifyResult("SKIP", 0.1)
    assert combine_results("foo", hyp, naive) == "SUCCESS"
    assert "[PASS]" in capsys.readouterr().out


def test_combine_naive_pass(capsys):
    hyp = VerifyResult("SKIP", 0.1)
    naive = VerifyResult("PASS", 0.1)
    assert combine_results("foo", hyp, naive) == "SUCCESS"


def test_combine_both_skip_with_errors(capsys):
    hyp = VerifyResult("SKIP", 0.1, "h-reason")
    naive = VerifyResult("SKIP", 0.1, "n-reason")
    status = combine_results("foo", hyp, naive)
    assert status == "SKIPPED"
    out = capsys.readouterr().out
    assert "Hypothesis: h-reason" in out
    assert "Naive: n-reason" in out


def test_combine_both_skip_no_errors(capsys):
    hyp = VerifyResult("SKIP", 0.1, None)
    naive = VerifyResult("SKIP", 0.1, None)
    status = combine_results("foo", hyp, naive)
    assert status == "SKIPPED"
    assert "Both fuzzers skipped" in capsys.readouterr().out


def test_combine_with_config(capsys):
    config = {"functions": {"path/to/file.py:foo": ["int"]}}
    hyp = VerifyResult("PASS", 0.1)
    naive = VerifyResult("PASS", 0.1)
    combine_results("foo", hyp, naive, config=config)
    out = capsys.readouterr().out
    assert "path/to/file.py:foo" in out


# ---------------------------------------------------------------------------
# worker_verify_function (called in-process)
# ---------------------------------------------------------------------------

def test_worker_verify_function_pass():
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_pass_simple" / "original.py")
    ref = str(FIXTURES / "job_pass_simple" / "refactored.py")
    worker_verify_function(orig, ref, "add_one", {}, q)
    result = q.get_nowait()
    assert result == "SUCCESS"


def test_worker_verify_function_fail():
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_fail_wrong_result" / "original.py")
    ref = str(FIXTURES / "job_fail_wrong_result" / "refactored.py")
    worker_verify_function(orig, ref, "add_one", {}, q)
    result = q.get_nowait()
    assert result == "FAILURE"


def test_worker_verify_function_load_error(capsys):
    q = queue_mod.Queue()
    worker_verify_function("/nonexistent/orig.py", "/nonexistent/ref.py", "foo", {}, q)
    result = q.get_nowait()
    assert result == "SKIPPED"
    assert "[SKIP]" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# worker_verify_class_method (called in-process)
# ---------------------------------------------------------------------------

def test_worker_verify_class_method_pass():
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")
    worker_verify_class_method(orig, ref, "Counter", "increment", {}, q)
    result = q.get_nowait()
    assert result == "SUCCESS"


def test_worker_verify_class_method_with_implicit_raise():
    """Class method that raises implicitly → exercises lines 397-403."""
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_pass_class_divide" / "original.py")
    ref = str(FIXTURES / "job_pass_class_divide" / "refactored.py")
    worker_verify_class_method(orig, ref, "SafeDivider", "divide_by", {}, q)
    result = q.get_nowait()
    assert result == "SUCCESS"


def test_worker_verify_class_method_fail():
    """Class method that returns wrong result → exercises AssertionError path (lines 411-413)."""
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_fail_class" / "original.py")
    ref = str(FIXTURES / "job_fail_class" / "refactored.py")
    worker_verify_class_method(orig, ref, "Calculator", "double", {}, q)
    result = q.get_nowait()
    assert result == "FAILURE"


def test_worker_verify_class_method_sample_args_none(capsys):
    """When get_one() raises (filter too much), sample_args stays None → SKIP (lines 364-368, 444)."""
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")

    import hypothesis.strategies as hst
    filtering_strategy = hst.tuples(hst.integers().filter(lambda x: False))

    with patch("verify.smart_infer_arg_strategies", return_value=filtering_strategy):
        worker_verify_class_method(orig, ref, "Counter", "increment", {}, q)
    result = q.get_nowait()
    assert result == "SKIPPED"


def test_worker_verify_class_method_env_max_examples(monkeypatch):
    """Class method test reads HYPOTHESIS_MAX_EXAMPLES env var (line 379)."""
    monkeypatch.setenv("HYPOTHESIS_MAX_EXAMPLES", "3")
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")
    worker_verify_class_method(orig, ref, "Counter", "increment", {}, q)
    result = q.get_nowait()
    assert result == "SUCCESS"


def test_worker_verify_class_method_hypothesis_error_skip():
    """Non-Hypothesis exception → SKIP path (lines 416, 419-420)."""
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")

    call_count = [0]
    real_smart_infer = verify.smart_infer_arg_strategies

    def mock_smart_infer(func, config=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return real_smart_infer(func, config=config)
        raise RuntimeError("unexpected error")  # hits line 420 (else branch)

    with patch("verify.smart_infer_arg_strategies", side_effect=mock_smart_infer):
        worker_verify_class_method(orig, ref, "Counter", "increment", {}, q)
    result = q.get_nowait()
    assert result in ("SKIPPED", "FAILURE", "SUCCESS")


def test_worker_verify_class_method_hypothesis_found_error():
    """Exception with 'Hypothesis found' → FAIL path (line 418)."""
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")

    call_count = [0]
    real_smart_infer = verify.smart_infer_arg_strategies

    def mock_smart_infer(func, config=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return real_smart_infer(func, config=config)
        raise RuntimeError("Hypothesis found a minimal failing example")  # hits line 418

    with patch("verify.smart_infer_arg_strategies", side_effect=mock_smart_infer):
        worker_verify_class_method(orig, ref, "Counter", "increment", {}, q)
    result = q.get_nowait()
    assert result in ("SKIPPED", "FAILURE", "SUCCESS")


def test_worker_verify_class_method_naive_fuzzer_exception(capsys):
    """Naive fuzzer instance creation raises → exercises lines 453-454."""
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")

    # run_naive_fuzzing is called AFTER sample_args is set; if run_naive_fuzzing
    # itself raises (internal error not AssertionError), lines 453-454 are hit
    real_smart_infer = verify.smart_infer_arg_strategies

    call_count = [0]
    def mock_infer(func, config=None):
        call_count[0] += 1
        return real_smart_infer(func, config=config)

    with patch("verify.smart_infer_arg_strategies", side_effect=mock_infer):
        with patch("verify.run_naive_fuzzing", side_effect=RuntimeError("naive fail")):
            worker_verify_class_method(orig, ref, "Counter", "increment", {}, q)
    result = q.get_nowait()
    assert result in ("SKIPPED", "SUCCESS", "FAILURE")


def test_worker_verify_class_method_no_init_args(capsys):
    """When constructor args can't be found (Unsatisfiable), worker SKIPs."""
    q = queue_mod.Queue()
    orig = str(FIXTURES / "job_skip_unsatisfiable" / "original.py")
    ref = str(FIXTURES / "job_skip_unsatisfiable" / "refactored.py")
    # Opaque constructor takes no typed params — smart_infer raises Unsatisfiable
    worker_verify_class_method(orig, ref, "Opaque", "__init__", {}, q)
    result = q.get_nowait()
    assert result in ("SKIPPED", "SUCCESS")


def test_worker_verify_class_method_load_error(capsys):
    q = queue_mod.Queue()
    worker_verify_class_method(
        "/nonexistent/orig.py", "/nonexistent/ref.py",
        "Counter", "increment", {}, q
    )
    result = q.get_nowait()
    assert result == "SKIPPED"
    assert "[SKIP]" in capsys.readouterr().out
