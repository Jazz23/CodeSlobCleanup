"""Unit tests for orchestrator.py — 100% branch coverage."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import orchestrator
from orchestrator import (
    run_command,
    parse_verify_output,
    parse_benchmark_output,
    process_job,
    main,
)

FIXTURES = Path(__file__).parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "skills" / "code-slob-cleanup" / "scripts"


# ---------------------------------------------------------------------------
# run_command
# ---------------------------------------------------------------------------

def test_run_command_success():
    rc, out, err = run_command(["echo", "hello"], cwd="/tmp")
    assert rc == 0
    assert "hello" in out


def test_run_command_failure():
    rc, out, err = run_command(["false"], cwd="/tmp")
    assert rc != 0


# ---------------------------------------------------------------------------
# parse_verify_output
# ---------------------------------------------------------------------------

def test_parse_verify_pass_with_duration():
    output = "[PASS] foo (1.2345s)\n"
    results = parse_verify_output(output)
    assert "foo" in results
    assert results["foo"]["status"] == "PASS"
    assert results["foo"]["duration"] == "1.2345s"


def test_parse_verify_skip():
    # The parser strips duration but leaves the rest of the name intact
    output = "[SKIP] bar (0.0001s) (Unsatisfiable)\n"
    results = parse_verify_output(output)
    # name = "bar (0.0001s) (Unsatisfiable)" with duration removed → "bar (Unsatisfiable)"
    assert len(results) == 1
    entry = next(iter(results.values()))
    assert entry["status"] == "SKIP"


def test_parse_verify_fail_with_multiline_logs():
    output = "[FAIL] baz (0.5s)\nAssertionError: x != y\nmore detail\n"
    results = parse_verify_output(output)
    assert results["baz"]["status"] == "FAIL"
    assert "AssertionError" in results["baz"]["logs"]
    assert "more detail" in results["baz"]["logs"]


def test_parse_verify_no_duration():
    output = "[PASS] noduration\n"
    results = parse_verify_output(output)
    assert "noduration" in results
    assert results["noduration"]["duration"] is None


def test_parse_verify_empty_name_after_strip():
    # Raw after stripping becomes "(1.0s)" — after removing duration name is empty,
    # should fall back to raw
    output = "[PASS] (1.0s)\n"
    results = parse_verify_output(output)
    # The key is the raw value since name is empty → reverts to raw
    assert len(results) == 1


def test_parse_verify_empty_input():
    assert parse_verify_output("") == {}


def test_parse_verify_multiple_functions():
    output = (
        "[PASS] f1 (1.0s)\n"
        "[FAIL] f2 (0.1s)\nsome error\n"
        "[SKIP] f3 (0.0s)\n"
    )
    results = parse_verify_output(output)
    assert len(results) == 3
    assert results["f1"]["status"] == "PASS"
    assert results["f2"]["status"] == "FAIL"
    assert results["f3"]["status"] == "SKIP"


# ---------------------------------------------------------------------------
# parse_benchmark_output
# ---------------------------------------------------------------------------

def test_parse_benchmark_speedup():
    output = "[SPEEDUP] foo: 2.50x\n"
    speedups = parse_benchmark_output(output)
    assert speedups["foo"] == "2.50x"


def test_parse_benchmark_skip_is_ignored():
    output = "[SKIP] bar (reason)\n"
    speedups = parse_benchmark_output(output)
    assert speedups == {}


def test_parse_benchmark_malformed_bare_except():
    # Missing ": " separator — bare except in parser, continue
    output = "[SPEEDUP] malformed_no_separator\n"
    speedups = parse_benchmark_output(output)
    assert speedups == {}


def test_parse_benchmark_empty():
    assert parse_benchmark_output("") == {}


# ---------------------------------------------------------------------------
# process_job
# ---------------------------------------------------------------------------

@patch("orchestrator.run_command")
def test_process_job_missing_both_files(mock_run, tmp_path):
    result = process_job(tmp_path, tmp_path, SCRIPTS_DIR)
    assert result is None
    mock_run.assert_not_called()


@patch("orchestrator.run_command")
def test_process_job_missing_refactored(mock_run, tmp_path):
    (tmp_path / "original.py").write_text("def f(): pass")
    result = process_job(tmp_path, tmp_path, SCRIPTS_DIR)
    assert result is None


@patch("orchestrator.run_command")
def test_process_job_pass(mock_run, tmp_path):
    (tmp_path / "original.py").write_text("def f(): pass")
    (tmp_path / "refactored.py").write_text("def f(): pass")
    mock_run.return_value = (0, "[PASS] f (1.0s)\n", "")
    result = process_job(tmp_path, tmp_path, SCRIPTS_DIR)
    assert result is not None
    assert result["status"] == "PASS"
    assert result["job_name"] == tmp_path.name


@patch("orchestrator.run_command")
def test_process_job_fail(mock_run, tmp_path):
    (tmp_path / "original.py").write_text("def f(): pass")
    (tmp_path / "refactored.py").write_text("def f(): pass")
    mock_run.return_value = (1, "[FAIL] f (0.5s)\nsome error\n", "")
    result = process_job(tmp_path, tmp_path, SCRIPTS_DIR)
    assert result["status"] == "FAIL"


@patch("orchestrator.run_command")
def test_process_job_with_type_hints_modules(mock_run, tmp_path):
    (tmp_path / "original.py").write_text("def f(): pass")
    (tmp_path / "refactored.py").write_text("def f(): pass")
    (tmp_path / "type_hints.json").write_text('{"modules": ["numpy"]}')
    mock_run.return_value = (0, "[PASS] f (1.0s)\n", "")
    process_job(tmp_path, tmp_path, SCRIPTS_DIR)
    # Both verify and bench calls should include --with numpy
    for call_args in mock_run.call_args_list:
        cmd = call_args[0][0]
        assert "--with" in cmd
        assert "numpy" in cmd


@patch("orchestrator.run_command")
def test_process_job_type_hints_invalid_json(mock_run, tmp_path):
    (tmp_path / "original.py").write_text("def f(): pass")
    (tmp_path / "refactored.py").write_text("def f(): pass")
    (tmp_path / "type_hints.json").write_text("{not: valid json")
    mock_run.return_value = (0, "[PASS] f (1.0s)\n", "")
    result = process_job(tmp_path, tmp_path, SCRIPTS_DIR)
    assert result is not None  # invalid JSON caught; extra_modules stays []


@patch("orchestrator.run_command")
def test_process_job_type_hints_modules_not_list(mock_run, tmp_path):
    (tmp_path / "original.py").write_text("def f(): pass")
    (tmp_path / "refactored.py").write_text("def f(): pass")
    (tmp_path / "type_hints.json").write_text('{"modules": {"bad": "type"}}')
    mock_run.return_value = (0, "[PASS] f (1.0s)\n", "")
    result = process_job(tmp_path, tmp_path, SCRIPTS_DIR)
    # modules is not a list → extra_modules stays []
    for call_args in mock_run.call_args_list:
        cmd = call_args[0][0]
        assert "--with" not in cmd


@patch("orchestrator.run_command")
def test_process_job_with_speedup(mock_run, tmp_path):
    (tmp_path / "original.py").write_text("def f(): pass")
    (tmp_path / "refactored.py").write_text("def f(): pass")
    mock_run.side_effect = [
        (0, "[PASS] f (1.0s)\n", ""),
        (0, "[SPEEDUP] f: 2.50x\n", ""),
    ]
    result = process_job(tmp_path, tmp_path, SCRIPTS_DIR)
    assert result["functions"][0]["speedup"] == "2.50x"


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def test_main_nonexistent_dir(monkeypatch):
    monkeypatch.setattr("sys.argv", ["orchestrator.py", "/nonexistent_xyz_dir"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


@patch("orchestrator.process_job")
def test_main_pass_job(mock_process, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["orchestrator.py", str(tmp_path)])
    job_dir = tmp_path / "job1"
    job_dir.mkdir()
    mock_process.return_value = {
        "job_name": "job1",
        "status": "PASS",
        "functions": [{"name": "f", "status": "PASS", "duration": "1.0s", "logs": ""}],
    }
    main()
    out = capsys.readouterr().out
    assert "[PASS] job1" in out
    assert "[PASS] f" in out


@patch("orchestrator.process_job")
def test_main_fail_job_exits_1(mock_process, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["orchestrator.py", str(tmp_path)])
    job_dir = tmp_path / "job1"
    job_dir.mkdir()
    mock_process.return_value = {
        "job_name": "job1",
        "status": "FAIL",
        "functions": [{"name": "f", "status": "FAIL", "duration": "0.5s", "logs": "err msg"}],
    }
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[FAIL] f" in out
    assert "err msg" in out


@patch("orchestrator.process_job")
def test_main_with_speedups(mock_process, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["orchestrator.py", str(tmp_path)])
    job_dir = tmp_path / "job1"
    job_dir.mkdir()
    mock_process.return_value = {
        "job_name": "job1",
        "status": "PASS",
        "functions": [
            {"name": "f", "status": "PASS", "duration": "1.0s",
             "speedup": "3.00x", "logs": ""}
        ],
    }
    main()
    out = capsys.readouterr().out
    assert "Average Speedup" in out
    assert "3.00x" in out


@patch("orchestrator.process_job", return_value=None)
def test_main_job_returns_none(mock_process, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["orchestrator.py", str(tmp_path)])
    (tmp_path / "empty_job").mkdir()
    main()  # None results filtered — should not crash


@patch("orchestrator.process_job")
def test_main_skip_func(mock_process, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["orchestrator.py", str(tmp_path)])
    job_dir = tmp_path / "job1"
    job_dir.mkdir()
    mock_process.return_value = {
        "job_name": "job1",
        "status": "PASS",
        "functions": [{"name": "f", "status": "SKIP", "duration": "0.1s", "logs": ""}],
    }
    main()
    assert "[SKIP]" in capsys.readouterr().out


@patch("orchestrator.process_job")
def test_main_speedup_na_filtered(mock_process, tmp_path, monkeypatch, capsys):
    """Speedup value 'N/A' should be skipped (not appended to all_speedups)."""
    monkeypatch.setattr("sys.argv", ["orchestrator.py", str(tmp_path)])
    job_dir = tmp_path / "job1"
    job_dir.mkdir()
    mock_process.return_value = {
        "job_name": "job1",
        "status": "PASS",
        "functions": [{"name": "f", "status": "PASS", "duration": "1.0s",
                       "speedup": "N/A", "logs": ""}],
    }
    main()
    out = capsys.readouterr().out
    assert "Average Speedup" not in out


@patch("orchestrator.process_job")
def test_main_speedup_bad_parse(mock_process, tmp_path, monkeypatch, capsys):
    """Unparseable speedup value (bare except) should not crash."""
    monkeypatch.setattr("sys.argv", ["orchestrator.py", str(tmp_path)])
    job_dir = tmp_path / "job1"
    job_dir.mkdir()
    mock_process.return_value = {
        "job_name": "job1",
        "status": "PASS",
        "functions": [{"name": "f", "status": "PASS", "duration": "1.0s",
                       "speedup": "not_a_number_x", "logs": ""}],
    }
    main()  # bare except in orchestrator catches the float() parse failure


@patch("orchestrator.process_job")
def test_main_func_no_duration_no_speedup(mock_process, tmp_path, monkeypatch, capsys):
    """Functions with no duration/speedup extras print cleanly."""
    monkeypatch.setattr("sys.argv", ["orchestrator.py", str(tmp_path)])
    job_dir = tmp_path / "job1"
    job_dir.mkdir()
    mock_process.return_value = {
        "job_name": "job1",
        "status": "PASS",
        "functions": [{"name": "f", "status": "PASS", "duration": None, "logs": ""}],
    }
    main()
    out = capsys.readouterr().out
    assert "[PASS] f" in out
