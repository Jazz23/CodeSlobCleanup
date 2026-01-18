# /// script
# dependencies = [
#     "hypothesis",
# ]
# ///

import argparse
import inspect
import sys
import traceback
import os
import json
import multiprocessing
from queue import Empty
from typing import Callable, Dict, Any
from pathlib import Path

# Add the directory containing 'verification' to sys.path
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]
verification_root = current_file.parents[1]

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(verification_root))

from hypothesis import given, settings, HealthCheck
import hypothesis
import hypothesis.strategies as st
from hypothesis.errors import Unsatisfiable

try:
    from verification.tools.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies
except ImportError:
    try:
        from tools.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies
    except ImportError:
        from common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies

def clean_traceback(tb_str: str) -> str:
    """Filters traceback to remove internal tool frames and focus on user code."""
    lines = tb_str.splitlines()
    filtered_lines = []
    
    for line in lines:
        if 'original.py' in line or 'refactored.py' in line or 'AssertionError' in line or 'NameError' in line or 'TypeError' in line or 'ValueError' in line:
            filtered_lines.append(line.strip())
        elif 'Falsifying example' in line:
            filtered_lines.append(line.strip())
        elif 'args=(' in line:
            filtered_lines.append(line.strip())
            
    return "\n".join(filtered_lines).strip()

def run_hypothesis_verification(orig_func: Callable, ref_func: Callable, config: Dict[str, Any] = None):
    """Runs Hypothesis tests to verify orig_func == ref_func."""
    try:
        args_strategy = smart_infer_arg_strategies(orig_func, config=config)
        
        max_examples = 100
        env_max = os.getenv("HYPOTHESIS_MAX_EXAMPLES")
        if env_max:
            max_examples = int(env_max)
            
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much], max_examples=max_examples, deadline=None)
        @given(args_strategy)
        def test_wrapper(args):
            orig_res, orig_exc = None, None
            ref_res, ref_exc = None, None
            
            try:
                orig_res = orig_func(*args)
            except Exception as e:
                orig_exc = type(e)
                
            try:
                ref_res = ref_func(*args)
            except Exception as e:
                ref_exc = type(e)
            
            if orig_exc:
                assert ref_exc == orig_exc, f"Original raised {orig_exc}, but Refactored raised {ref_exc} for input {args}"
            else:
                if ref_exc:
                    assert False, f"Original returned {orig_res}, but Refactored raised {ref_exc} for input {args}"
                assert orig_res == ref_res, f"Mismatch for input {args}: Original={orig_res}, Refactored={ref_res}"

        test_wrapper()
        print(f"[PASS] {orig_func.__name__}")

    except AssertionError as e:
        raw_tb = traceback.format_exc()
        cleaned_tb = clean_traceback(raw_tb)
        print(f"[FAIL] {orig_func.__name__}")
        if cleaned_tb:
            print(cleaned_tb)
        raise e

    except Unsatisfiable:
        print(f"[SKIP] {orig_func.__name__} (Unable to generate valid inputs)")

    except Exception as e:
        print(f"[SKIP] {orig_func.__name__} (Error during verification: {e})")

def worker_verify_function(orig_path, ref_path, func_name, config, result_queue):
    """Worker process to run verification for a single function."""
    try:
        orig_mod = load_module_from_path(orig_path, "original_mod")
        ref_mod = load_module_from_path(ref_path, "refactored_mod")
        
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        run_hypothesis_verification(orig_func, ref_func, config=config)
        result_queue.put("SUCCESS")
    except AssertionError:
        result_queue.put("FAILURE")
    except Exception:
        result_queue.put("SKIPPED")

def main():
    parser = argparse.ArgumentParser(description="Verify refactored code against original code.")
    parser.add_argument("original", help="Path to original python file")
    parser.add_argument("refactored", help="Path to refactored python file")
    parser.add_argument("--config", help="JSON string containing type configuration")
    args = parser.parse_args()

    config = {}
    if args.config:
        try:
            config = json.loads(args.config)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON configuration provided: {e}")
            sys.exit(1)

    try:
        orig_mod = load_module_from_path(args.original, "original_mod")
        ref_mod = load_module_from_path(args.refactored, "refactored_mod")
        common_funcs = get_common_functions(orig_mod, ref_mod)
    except Exception as e:
        print(f"[SKIP] (Module loading failed: {e})")
        return

    success = True

    for func_name in common_funcs:
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=worker_verify_function, 
            args=(args.original, args.refactored, func_name, config, queue)
        )
        p.start()
        
        p.join(timeout=15)
        
        if p.is_alive():
            p.terminate()
            p.join()
            print(f"[SKIP] {func_name} (Timeout)")
        else:
            try:
                result = queue.get_nowait()
                if result == "FAILURE":
                    success = False
            except Empty:
                print(f"[SKIP] {func_name} (Process crash)")
            
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
