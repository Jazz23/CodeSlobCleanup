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
    
    # We want to keep lines that mention original.py or refactored.py
    # or the actual error message.
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
            
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=max_examples, deadline=None)
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
    except Exception as e:
        raw_tb = traceback.format_exc()
        cleaned_tb = clean_traceback(raw_tb)
        print(f"[FAIL] {orig_func.__name__}")
        if cleaned_tb:
            print(cleaned_tb)
        raise e

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
        except:
            pass

    orig_mod = load_module_from_path(args.original, "original_mod")
    ref_mod = load_module_from_path(args.refactored, "refactored_mod")

    common_funcs = get_common_functions(orig_mod, ref_mod)
    success = True

    for func_name in common_funcs:
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        try:
            run_hypothesis_verification(orig_func, ref_func, config=config)
        except Exception:
            success = False
        
    common_classes = get_common_classes(orig_mod, ref_mod)
    for cls_name in common_classes:
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        # Class verification logic could be cleaned up too, but sticking to functions for now
        # as per the current failure case.
            
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()