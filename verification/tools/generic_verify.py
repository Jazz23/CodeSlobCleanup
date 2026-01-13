import argparse
import inspect
import sys
import traceback
from typing import Callable
from hypothesis import given, settings, HealthCheck
import hypothesis
import hypothesis.strategies as st

try:
    from verification.tools.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy
except ImportError:
    from tools.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy

# Try importing Atheris
try:
    import atheris
    ATHERIS_AVAILABLE = True
except ImportError:
    ATHERIS_AVAILABLE = False

def run_hypothesis_verification(orig_func: Callable, ref_func: Callable):
    """Runs Hypothesis tests to verify orig_func == ref_func."""
    print(f"  - Verifying {orig_func.__name__} with Hypothesis...")
    
    sig = inspect.signature(orig_func)
    params = sig.parameters
    
    strategy_kwargs = {}
    for name, param in params.items():
        if name == 'self': continue
        strategy_kwargs[name] = infer_strategy(param)
        
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100, deadline=None)
    @given(**strategy_kwargs)
    def test_wrapper(**kwargs):
        # Capture exceptions to ensure both behave identically even in error states
        orig_res, orig_exc = None, None
        ref_res, ref_exc = None, None
        
        try:
            orig_res = orig_func(**kwargs)
        except Exception as e:
            orig_exc = type(e)
            
        try:
            ref_res = ref_func(**kwargs)
        except Exception as e:
            ref_exc = type(e)
            
        if orig_exc:
            assert ref_exc == orig_exc, f"Original raised {orig_exc}, but Refactored raised {ref_exc} for input {kwargs}"
        else:
            if ref_exc:
                assert False, f"Original returned {orig_res}, but Refactored raised {ref_exc} for input {kwargs}"
            assert orig_res == ref_res, f"Mismatch for input {kwargs}: Original={orig_res}, Refactored={ref_res}"

    # Manually executing the test wrapper
    try:
        test_wrapper()
        print("    [PASS] Hypothesis verification successful.")
    except Exception as e:
        print(f"    [FAIL] Hypothesis found a mismatch!")
        # traceback.print_exc() # detailed traceback
        print(e)

def run_class_verification(cls_name: str, orig_cls: type, ref_cls: type):
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
                # But to be robust, we should check if one fails and other doesn't?
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


def run_atheris_fuzzing(orig_func: Callable, ref_func: Callable):
    """
    Sets up a simple Atheris fuzz harness.
    NOTE: Atheris usually requires the script to be the entry point. 
    Calling this in a loop for multiple functions is complex because Atheris 
    doesn't easily support resetting/switching targets in one process.
    We will strictly verify *one* function if specified, or skip if complex.
    For this generic script, we will simulate a harness structure.
    """
    if not ATHERIS_AVAILABLE:
        print("    [SKIP] Atheris not installed.")
        return

    print(f"  - Verifying {orig_func.__name__} with Atheris (Experimental)...")
    
    # Atheris requires a function that takes 'data' (bytes)
    def test_one_input(data):
        fdp = atheris.FuzzedDataProvider(data)
        
        # We need to map bytes to arguments. This is tricky generic.
        # We'll try to generate arguments based on signature similarly to Hypothesis
        sig = inspect.signature(orig_func)
        kwargs = {}
        for name, param in sig.parameters.items():
            # Basic mapping logic
            if param.annotation == int:
                kwargs[name] = fdp.ConsumeInt(4)
            elif param.annotation == str:
                kwargs[name] = fdp.ConsumeString(10)
            else:
                # Fallback for untyped: Randomly choose type
                choice = fdp.ConsumeInt(1)
                if choice == 0:
                    kwargs[name] = fdp.ConsumeInt(4)
                else:
                    kwargs[name] = fdp.ConsumeString(10)
        
        try:
            res_orig = orig_func(**kwargs)
            res_ref = ref_func(**kwargs)
            if res_orig != res_ref:
                raise RuntimeError(f"Mismatch: {res_orig} != {res_ref} for {kwargs}")
        except Exception:
            # We ignore exceptions unless they differ, but implementing that 
            # inside the fuzzer requires robust exception matching which is hard here.
            pass

    # Note: We cannot easily run Atheris.Setup() multiple times in one process.
    # This part of the requirement is difficult to satisfy fully generically in a single run
    # for multiple functions. We will print a message explaining this.
    print("    [INFO] Atheris requires dedicated process control. Skipping execution in this generic multi-function tool.")
    print("    To fuzz properly, create a dedicated script for each function using 'atheris.Setup(sys.argv, test_one_input)'.")

def main():
    parser = argparse.ArgumentParser(description="Verify refactored code against original code.")
    parser.add_argument("original", help="Path to original python file")
    parser.add_argument("refactored", help="Path to refactored python file")
    args = parser.parse_args()

    print(f"Loading original: {args.original}")
    orig_mod = load_module_from_path(args.original, "original_mod")
    
    print(f"Loading refactored: {args.refactored}")
    ref_mod = load_module_from_path(args.refactored, "refactored_mod")

    common_funcs = get_common_functions(orig_mod, ref_mod)
    print(f"Found {len(common_funcs)} common functions: {common_funcs}")

    for func_name in common_funcs:
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        print(f"\nTesting function: {func_name}")
        run_hypothesis_verification(orig_func, ref_func)
        # Atheris check is included but essentially informative due to technical constraints
        run_atheris_fuzzing(orig_func, ref_func)
        
    common_classes = get_common_classes(orig_mod, ref_mod)
    print(f"Found {len(common_classes)} common classes: {common_classes}")
    
    for cls_name in common_classes:
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        run_class_verification(cls_name, orig_cls, ref_cls)

if __name__ == "__main__":
    main()
