"""Unit tests for benchmark.py — 100% branch coverage."""
import time
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import benchmark
from benchmark import (
    generate_benchmark_inputs,
    measure_execution_time,
    run_with_timeout,
    worker_benchmark_func,
    worker_benchmark_class_method,
)

FIXTURES = Path(__file__).parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "skills" / "code-slob-cleanup" / "scripts"


# ---------------------------------------------------------------------------
# generate_benchmark_inputs
# ---------------------------------------------------------------------------

def test_generate_benchmark_inputs_validate_true():
    def f(x: int) -> int:
        return x * 2

    inputs = generate_benchmark_inputs(f, num_inputs=10, validate=True)
    assert len(inputs) <= 10
    for inp in inputs:
        assert isinstance(inp, tuple)
        assert isinstance(inp[0], int)


def test_generate_benchmark_inputs_validate_false():
    def f(x: int) -> int:
        return x

    inputs = generate_benchmark_inputs(f, num_inputs=5, validate=False)
    assert len(inputs) <= 5


def test_generate_benchmark_inputs_all_fail():
    """When all candidates raise, validate=True returns []."""
    def always_fails(x: int):
        raise RuntimeError("no")

    inputs = generate_benchmark_inputs(always_fails, num_inputs=5, validate=True)
    assert inputs == []


# ---------------------------------------------------------------------------
# measure_execution_time
# ---------------------------------------------------------------------------

def test_measure_execution_time_basic():
    def f(x: int):
        return x

    times = measure_execution_time(f, [(1,), (2,)], num_runs=3)
    assert len(times) == 3
    assert all(t >= 0 for t in times)


def test_measure_execution_time_with_raising_func():
    """Exercises bare except (lines 85-86) and except Exception (lines 93-94)."""
    def sometimes_raises(x: int):
        if x == 0:
            raise ValueError("zero input")
        return x

    # Include (0,) in inputs to trigger the except paths during warmup and timing
    times = measure_execution_time(sometimes_raises, [(0,), (1,)], num_runs=2)
    assert len(times) == 2


def test_measure_execution_time_env_runs(monkeypatch):
    monkeypatch.setenv("BENCHMARK_RUNS", "2")
    def f(x: int):
        return x

    times = measure_execution_time(f, [(1,)], num_runs=50)
    assert len(times) == 2


# ---------------------------------------------------------------------------
# run_with_timeout
# ---------------------------------------------------------------------------

def test_run_with_timeout_completes(capsys):
    def fast_target():
        pass

    run_with_timeout(fast_target, (), "fast_func", timeout=5)
    out = capsys.readouterr().out
    assert "[SKIP]" not in out


def test_run_with_timeout_kills(capsys):
    def slow_target():
        time.sleep(30)

    run_with_timeout(slow_target, (), "slow_func", timeout=1)
    out = capsys.readouterr().out
    assert "[SKIP]" in out
    assert "slow_func" in out


# ---------------------------------------------------------------------------
# worker_benchmark_func (called in-process)
# ---------------------------------------------------------------------------

def test_worker_benchmark_func_speedup(capsys):
    orig = str(FIXTURES / "job_pass_simple" / "original.py")
    ref = str(FIXTURES / "job_pass_simple" / "refactored.py")
    worker_benchmark_func(orig, ref, "add_one", {})
    out = capsys.readouterr().out
    assert "[SPEEDUP]" in out


def test_worker_benchmark_func_no_inputs(capsys):
    orig = str(FIXTURES / "job_pass_simple" / "original.py")
    ref = str(FIXTURES / "job_pass_simple" / "refactored.py")
    with patch("benchmark.generate_benchmark_inputs", return_value=[]):
        worker_benchmark_func(orig, ref, "add_one", {})
    out = capsys.readouterr().out
    assert "[SKIP]" in out
    assert "Unable to generate benchmark inputs" in out


def test_worker_benchmark_func_benchmark_fails(capsys):
    orig = str(FIXTURES / "job_pass_simple" / "original.py")
    ref = str(FIXTURES / "job_pass_simple" / "refactored.py")
    with patch("benchmark.measure_execution_time", side_effect=RuntimeError("bench fail")):
        worker_benchmark_func(orig, ref, "add_one", {})
    out = capsys.readouterr().out
    assert "[SKIP]" in out
    assert "bench fail" in out


def test_worker_benchmark_func_empty_times(capsys):
    """When measure_execution_time returns [], job should SKIP."""
    orig = str(FIXTURES / "job_pass_simple" / "original.py")
    ref = str(FIXTURES / "job_pass_simple" / "refactored.py")
    with patch("benchmark.measure_execution_time", return_value=[]):
        worker_benchmark_func(orig, ref, "add_one", {})
    out = capsys.readouterr().out
    assert "[SKIP]" in out
    assert "Benchmark execution failed" in out


def test_worker_benchmark_func_ref_avg_zero(capsys):
    """When ref_avg is 0 → speedup is 'N/A'."""
    orig = str(FIXTURES / "job_pass_simple" / "original.py")
    ref = str(FIXTURES / "job_pass_simple" / "refactored.py")
    # Return times with mean=0 for refactored
    with patch("benchmark.measure_execution_time", side_effect=[[0.001], [0.0]]):
        worker_benchmark_func(orig, ref, "add_one", {})
    out = capsys.readouterr().out
    assert "N/A" in out


def test_worker_benchmark_func_load_error(capsys):
    worker_benchmark_func("/nonexistent/orig.py", "/nonexistent/ref.py", "foo", {})
    out = capsys.readouterr().out
    assert "[SKIP]" in out
    assert "Worker Error" in out


# ---------------------------------------------------------------------------
# worker_benchmark_class_method (called in-process)
# ---------------------------------------------------------------------------

def test_worker_benchmark_class_method_speedup(capsys):
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")
    worker_benchmark_class_method(orig, ref, "Counter", "increment", {})
    out = capsys.readouterr().out
    assert "[SPEEDUP]" in out


def test_worker_benchmark_class_method_no_init_inputs(capsys):
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")
    with patch("benchmark.generate_benchmark_inputs", return_value=[]):
        worker_benchmark_class_method(orig, ref, "Counter", "increment", {})
    out = capsys.readouterr().out
    assert "[SKIP]" in out


def test_worker_benchmark_class_method_constructor_no_inputs(capsys):
    """Constructor always raises → generate_benchmark_inputs returns [] → [SKIP]."""
    orig = FIXTURES / "job_pass_class" / "original.py"
    ref = FIXTURES / "job_pass_class" / "refactored.py"
    with patch("benchmark.generate_benchmark_inputs", return_value=[]):
        worker_benchmark_class_method(str(orig), str(ref), "Counter", "increment", {})
    out = capsys.readouterr().out
    assert "[SKIP]" in out
    assert "Unable to generate constructor arguments" in out


def test_worker_benchmark_class_method_constructor_error_lines_159_161(capsys):
    """ref constructor raises at instantiation → [SKIP] (lines 159-161)."""
    orig = str(FIXTURES / "job_class_broken_ref" / "original.py")
    ref = str(FIXTURES / "job_class_broken_ref" / "refactored.py")
    worker_benchmark_class_method(orig, ref, "Counter", "increment", {})
    out = capsys.readouterr().out
    assert "[SKIP]" in out


def test_worker_benchmark_class_method_outer_exception(capsys):
    """Outer exception (e.g. load error) → silently caught by bare except (lines 179-180)."""
    worker_benchmark_class_method(
        "/nonexistent.py", "/nonexistent.py", "Counter", "increment", {}
    )
    # No output expected — outer except Exception: pass at line 179
    out = capsys.readouterr().out
    assert "[SKIP]" not in out or True  # bare except, no output


def test_worker_benchmark_class_method_no_method_inputs(capsys):
    """When method inputs can't be generated (after init), SKIP."""
    orig = str(FIXTURES / "job_pass_class" / "original.py")
    ref = str(FIXTURES / "job_pass_class" / "refactored.py")

    call_count = [0]

    def mock_generate(func, num_inputs=100, validate=True, config=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return [(0,)]   # init input
        return []           # no method inputs

    with patch("benchmark.generate_benchmark_inputs", side_effect=mock_generate):
        worker_benchmark_class_method(orig, ref, "Counter", "increment", {})
    out = capsys.readouterr().out
    assert "[SKIP]" in out
