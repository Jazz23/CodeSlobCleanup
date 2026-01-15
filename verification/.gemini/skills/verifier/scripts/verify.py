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

# Add the directory containing 'verification' to sys.path to allow absolute imports
# and the 'verification' directory itself to allow 'from tools' if running from there
current_file = Path(__file__).resolve()
project_root = current_file.parents[2] # G:\GitHub\CodeSlobCleanup
verification_root = current_file.parents[1] # G:\GitHub\CodeSlobCleanup\verification

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
        # Fallback if running directly inside tools/
        from common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies

import random

def run_hypothesis_verification(orig_func: Callable, ref_func: Callable, raise_on_error: bool = False, config: Dict[str, Any] = None):
    """Runs Hypothesis tests to verify orig_func == ref_func."""
    try:
        print(f"  - Verifying {orig_func.__name__} with Hypothesis...")
        
        # Use smart inference to generate valid inputs even for untyped code
        args_strategy = smart_infer_arg_strategies(orig_func, config=config)
        
        max_examples = 100
        env_max = os.getenv("HYPOTHESIS_MAX_EXAMPLES")
        if env_max:
            max_examples = int(env_max)
            
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=max_examples, deadline=None)
        @given(args_strategy)
        def test_wrapper(args):
            # Capture exceptions to ensure both behave identically even in error states
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

        # Manually executing the test wrapper
        test_wrapper()
        print("    [PASS] Hypothesis verification successful.")
    except Exception as e:
        sys.stderr.write(f"    [FAIL] Hypothesis found a mismatch! {e}\n")
        traceback.print_exc() # detailed traceback
        if raise_on_error:
            raise e

def run_class_verification(cls_name: str, orig_cls: type, ref_cls: type, raise_on_error: bool = False, config: Dict[str, Any] = None):
    """Verifies public methods of a class."""
    print(f"\nVerifying Class: {cls_name}")
    
    # Identify common methods (excluding dunder methods except maybe __call__?)
    # For simplicity, we ignore __init__ (used for construction) and private methods
    methods1 = {n: m for n, m in inspect.getmembers(orig_cls, inspect.isfunction) if not n.startswith('_')}
    methods2 = {n: m for n, m in inspect.getmembers(ref_cls, inspect.isfunction) if not n.startswith('_')}
    common_methods = set(methods1.keys()).intersection(methods2.keys())
    
    print(f"  Found methods: {list(common_methods)}")
    
    # Prepare strategy for __init__
    try:
        init_sig = inspect.signature(orig_cls.__init__)
        init_strategies = {}
        for name, param in init_sig.parameters.items():
            if name == 'self': continue
            init_strategies[name] = infer_strategy(param)
        init_strategy = st.fixed_dictionaries(init_strategies)
    except Exception:
        # Fallback if __init__ is not introspectable or default
        init_strategy = st.just({})

    for method_name in common_methods:
        print(f"  - Verifying method {method_name}...")
        orig_method = methods1[method_name]
        
        # Strategy for method arguments
        sig = inspect.signature(orig_method)
        method_strategies = {}
        for name, param in sig.parameters.items():
            if name == 'self': continue
            method_strategies[name] = infer_strategy(param)
            
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100, deadline=None)
        @given(init_kwargs=init_strategy, method_kwargs=st.fixed_dictionaries(method_strategies))
        def test_method(init_kwargs, method_kwargs):
            # Instantiate
            try:
                inst_orig = orig_cls(**init_kwargs)
                inst_ref = ref_cls(**init_kwargs)
            except Exception:
                # If instantiation fails, we assume it fails for both (or irrelevant for now)
                return 

            # Call method
            orig_res, orig_exc = None, None
            ref_res, ref_exc = None, None
            
            try:
                orig_res = getattr(inst_orig, method_name)(**method_kwargs)
            except Exception as e:
                orig_exc = type(e)
            
            try:
                ref_res = getattr(inst_ref, method_name)(**method_kwargs)
            except Exception as e:
                ref_exc = type(e)
                
            if orig_exc:
                assert ref_exc == orig_exc, f"Original raised {orig_exc}, Refactored raised {ref_exc}"
            else:
                if ref_exc:
                    assert False, f"Original returned {orig_res}, Refactored raised {ref_exc}"
                assert orig_res == ref_res, f"Mismatch: Orig={orig_res}, Ref={ref_res}"

        try:
            test_method()
            print("    [PASS]")
        except Exception as e:
             print(f"    [FAIL] {e}")
             if raise_on_error:
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
        except Exception as e:
            print(f"    [WARN] Failed to parse --config JSON: {e}")

    print(f"Loading original: {args.original}")
    orig_mod = load_module_from_path(args.original, "original_mod")
    
    print(f"Loading refactored: {args.refactored}")
    ref_mod = load_module_from_path(args.refactored, "refactored_mod")

    common_funcs = get_common_functions(orig_mod, ref_mod)
    print(f"Found {len(common_funcs)} common functions: {common_funcs}")

    success = True

    for func_name in common_funcs:
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        print(f"\nTesting function: {func_name}")
        try:
            run_hypothesis_verification(orig_func, ref_func, raise_on_error=True, config=config)
        except Exception:
            success = False
        
    common_classes = get_common_classes(orig_mod, ref_mod)
    print(f"Found {len(common_classes)} common classes: {common_classes}")
    
    for cls_name in common_classes:
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        try:
            run_class_verification(cls_name, orig_cls, ref_cls, raise_on_error=True, config=config)
        except Exception:
            success = False
            
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()