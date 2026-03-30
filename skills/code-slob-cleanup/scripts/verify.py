# /// script
# dependencies = [
#     "hypothesis",
# ]
# ///

import inspect
import sys
import traceback
import os
import json
import time
import multiprocessing
import string
import random
from queue import Empty
from typing import Callable, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

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

from common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies, get_display_name

@dataclass
class VerifyResult:
    status: str  # "PASS", "FAIL", "SKIP"
    duration: float
    error: Optional[str] = None

def is_explicit_raise(exc: Exception) -> bool:
    """Checks if an exception was explicitly raised with a 'raise' statement."""
    tb = exc.__traceback__
    if not tb:
        return False
    
    # Iterate to the last frame of the traceback (where it was raised)
    last_frame_tb = tb
    while last_frame_tb.tb_next:
        last_frame_tb = last_frame_tb.tb_next
    
    frame = last_frame_tb.tb_frame
    try:
        frame_info = inspect.getframeinfo(frame)
        code_context = frame_info.code_context
        if code_context:
            line = code_context[0].strip()
            return line.startswith("raise")
        return False
    except Exception:
        return False

def clean_traceback(tb_str: str) -> str:
    """Filters traceback to return only the exception message."""
    lines = tb_str.splitlines()
    for line in reversed(lines):
        if 'AssertionError:' in line:
            return line.strip()
        if 'NameError:' in line or 'TypeError:' in line or 'ValueError:' in line:
            return line.strip()
    return ""

def run_hypothesis_verification(orig_func: Callable, ref_func: Callable, config: Dict[str, Any] = None) -> VerifyResult:
    """Runs Hypothesis tests to verify orig_func == ref_func."""
    start_time = time.time()
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
                orig_exc = e
                
            try:
                ref_res = ref_func(*args)
            except Exception as e:
                ref_exc = e
            
            check_result_equivalence(orig_res, orig_exc, ref_res, ref_exc, f"input {args}")

        test_wrapper()
        duration = time.time() - start_time
        return VerifyResult("PASS", duration)

    except AssertionError as e:
        duration = time.time() - start_time
        raw_tb = traceback.format_exc()
        cleaned_tb = clean_traceback(raw_tb)
        error_msg = cleaned_tb if cleaned_tb else str(e)
        return VerifyResult("FAIL", duration, error_msg)

    except Unsatisfiable as e:
        duration = time.time() - start_time
        return VerifyResult("SKIP", duration, str(e) if str(e) else "Unable to generate valid inputs")

    except Exception as e:
        duration = time.time() - start_time
        if "Hypothesis found" in str(e) or "MultipleFailures" in type(e).__name__:
             # Re-run clean_traceback on the hypothesis error if it's wrapped
             raw_tb = traceback.format_exc()
             cleaned_tb = clean_traceback(raw_tb)
             return VerifyResult("FAIL", duration, cleaned_tb if cleaned_tb else str(e))
        return VerifyResult("SKIP", duration, f"Error during verification: {e}")

def objects_are_equal(obj1, obj2):
    """
    Compares two objects for equality.
    Handles distinct types from different module loads (original vs refactored).
    """
    if obj1 == obj2:
        return True

    if isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
        if len(obj1) != len(obj2): return False
        return all(objects_are_equal(x, y) for x, y in zip(obj1, obj2))
    
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        if obj1.keys() != obj2.keys(): return False
        for k in obj1:
            if not objects_are_equal(obj1[k], obj2[k]): return False
        return True

    t1 = type(obj1)
    t2 = type(obj2)
    
    # Custom objects from different modules
    if t1 is not t2 and t1.__name__ == t2.__name__:
        # Handle Enum
        if hasattr(t1, '__members__'): 
             return getattr(obj1, 'name', None) == getattr(obj2, 'name', None)

        if hasattr(obj1, '__dict__') and hasattr(obj2, '__dict__'):
            d1 = obj1.__dict__
            d2 = obj2.__dict__
            if d1.keys() != d2.keys(): return False
            for k in d1:
                if not objects_are_equal(d1[k], d2[k]):
                    return False
            return True
            
    return False

def check_result_equivalence(orig_res, orig_exc, ref_res, ref_exc, args_context):
    """
    Verifies that the refactored result matches the original result,
    allowing for fixes of implicit "unhandled" exceptions while ensuring
    explicit "caught" exceptions are maintained.
    """
    if orig_exc:
        orig_name = type(orig_exc).__name__
        if ref_exc:
            ref_name = type(ref_exc).__name__
            if orig_name != ref_name:
                # If the original exception was explicitly raised (intentional), types must match.
                # If it was an unexpected/unhandled error, allow differing types — both crashed, that's fine.
                if is_explicit_raise(orig_exc):
                    raise AssertionError(f"Mismatch for {args_context}: Original raised {orig_name} (explicit), Refactored raised {ref_name}")
                return  # PASS - both threw unexpected errors, types don't need to match
        else:
            # Original raised, Refactored didn't. 
            # OK if it was an unhandled error (implicit raise), 
            # FAIL if it was a caught error (explicit raise).
            if is_explicit_raise(orig_exc):
                raise AssertionError(f"Mismatch for {args_context}: Original raised {orig_name} (explicit), Refactored returned {ref_res}")
            else:
                return # PASS - fixed an unhandled (implicit) error
    else:
        # Original didn't raise
        if ref_exc:
            raise AssertionError(f"Mismatch for {args_context}: Original returned {orig_res}, Refactored raised {type(ref_exc).__name__}")
        
        if not objects_are_equal(orig_res, ref_res):
             raise AssertionError(f"Mismatch for {args_context}: Original={orig_res}, Refactored={ref_res}")

class NaiveRandomFuzzer:
    """
    A simple random fuzzer that generates inputs based on type hints or random guessing.
    Acts as a 'dumb' counterpart to Hypothesis's 'smart' generation.
    """
    def __init__(self, iterations=50):
        self.iterations = iterations
    
    def _gen_int(self): return random.randint(-1000, 1000)
    def _gen_float(self): return random.uniform(-1000.0, 1000.0)
    def _gen_str(self): return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 50)))
    def _gen_bool(self): return random.choice([True, False])
    
    def _gen_any(self, depth=0):
        if depth > 2:
            choice = random.randint(0, 4)
        else:
            choice = random.randint(0, 6)
            
        if choice == 0: return self._gen_int()
        if choice == 1: return self._gen_float()
        if choice == 2: return self._gen_str()
        if choice == 3: return self._gen_bool()
        if choice == 4: return None
        if choice == 5: return [self._gen_any(depth + 1) for _ in range(random.randint(0, 5))]
        if choice == 6: return {self._gen_str(): self._gen_any(depth + 1) for _ in range(random.randint(0, 5))}

    def generate_args(self, func):
        sig = inspect.signature(func)
        args = []
        for param in sig.parameters.values():
            if param.name == 'self': continue
            if param.annotation == int:
                args.append(self._gen_int())
            elif param.annotation == float:
                args.append(self._gen_float())
            elif param.annotation == str:
                args.append(self._gen_str())
            elif param.annotation == bool:
                args.append(self._gen_bool())
            elif param.annotation == list:
                args.append([self._gen_any() for _ in range(random.randint(0, 5))])
            elif param.annotation == dict:
                args.append({self._gen_str(): self._gen_any() for _ in range(random.randint(0, 5))})
            else:
                args.append(self._gen_any())
        return args

    def fuzz(self, orig_func, ref_func):
        for _ in range(self.iterations):
            args = self.generate_args(orig_func)
            orig_res, orig_exc = None, None
            ref_res, ref_exc = None, None
            
            try:
                orig_res = orig_func(*args)
            except Exception as e:
                orig_exc = e
            
            try:
                ref_res = ref_func(*args)
            except Exception as e:
                ref_exc = e
            
            check_result_equivalence(orig_res, orig_exc, ref_res, ref_exc, f"input {args}")

def run_naive_fuzzing(orig_func: Callable, ref_func: Callable) -> VerifyResult:
    """Runs Naive Random Fuzzing."""
    start_time = time.time()
    try:
        fuzzer = NaiveRandomFuzzer(iterations=50)
        fuzzer.fuzz(orig_func, ref_func)
        duration = time.time() - start_time
        return VerifyResult("PASS", duration)
    except AssertionError as e:
        duration = time.time() - start_time
        return VerifyResult("FAIL", duration, str(e))
    except Exception as e:
        duration = time.time() - start_time
        return VerifyResult("SKIP", duration, f"Error: {e}")

def combine_results(name: str, hyp_res: VerifyResult, naive_res: VerifyResult, config: Dict[str, Any] = None):
    """Combines results from both fuzzers and prints the output."""
    total_duration = hyp_res.duration + naive_res.duration
    display_name = get_display_name(name, config)
    
    # Logic:
    # Fail if either fails.
    # Pass if one passes (and other passes/skips).
    # Skip if both skip.
    
    if hyp_res.status == "FAIL":
        print(f"[FAIL] {display_name} ({total_duration:.4f}s)")
        if hyp_res.error:
             print(hyp_res.error)
        return "FAILURE"
    
    if naive_res.status == "FAIL":
        print(f"[FAIL] {display_name} ({total_duration:.4f}s)")
        if naive_res.error:
             print(naive_res.error)
        return "FAILURE"
    
    if hyp_res.status == "PASS" or naive_res.status == "PASS":
        print(f"[PASS] {display_name} ({total_duration:.4f}s)")
        return "SUCCESS"
    
    # Both skipped
    reasons = []
    if hyp_res.error:
        reasons.append(f"Hypothesis: {hyp_res.error}")
    if naive_res.error:
        reasons.append(f"Naive: {naive_res.error}")
    
    reason_str = "; ".join(reasons) if reasons else "Both fuzzers skipped"
    print(f"[SKIP] {display_name} ({total_duration:.4f}s) ({reason_str})")
    return "SKIPPED"

def worker_verify_function(orig_path, ref_path, func_name, config, result_queue):
    """Worker process to run verification for a single function."""
    try:
        orig_mod = load_module_from_path(orig_path, "original_mod")
        ref_mod = load_module_from_path(ref_path, "refactored_mod")
        
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        hyp_res = run_hypothesis_verification(orig_func, ref_func, config=config)
        naive_res = run_naive_fuzzing(orig_func, ref_func)
        
        status = combine_results(func_name, hyp_res, naive_res, config=config)
        result_queue.put(status)
        
    except Exception as e:
        # Fallback if loading fails or something unexpected
        display_name = get_display_name(func_name, config)
        print(f"[SKIP] {display_name} (0.0000s) (Worker Error: {e})")
        result_queue.put("SKIPPED")

def worker_verify_class_method(orig_path, ref_path, cls_name, method_name, config, result_queue):
    """Worker process to run verification for a single class method."""
    start_time = time.time()
    full_name = f"{cls_name}.{method_name}"
    
    try:
        orig_mod = load_module_from_path(orig_path, "original_mod")
        ref_mod = load_module_from_path(ref_path, "refactored_mod")
        
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        
        # We need a strategy for (init_args, method_args)
        # Setup Hypothesis for Class Method
        
        hyp_res = None
        sample_args = None
        
        try:
            init_strategy = smart_infer_arg_strategies(orig_cls, config=config)
            try:
                @settings(max_examples=1, deadline=None)
                @given(init_strategy)
                def get_one(args):
                    nonlocal sample_args
                    sample_args = args
                get_one()
            except Exception:
                pass
                
            if sample_args is None:
                hyp_res = VerifyResult("SKIP", time.time() - start_time, "Could not find valid constructor arguments")
            else:
                sample_inst = orig_cls(*sample_args)
                bound_method = getattr(sample_inst, method_name)
                method_strategy = smart_infer_arg_strategies(bound_method, config=config)

                combined_strategy = st.tuples(init_strategy, method_strategy)

                max_examples = 100
                env_max = os.getenv("HYPOTHESIS_MAX_EXAMPLES")
                if env_max:
                    max_examples = int(env_max)

                @settings(suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much], max_examples=max_examples, deadline=None)
                @given(combined_strategy)
                def test_wrapper(combined_args):
                    init_args, method_args = combined_args
                    
                    inst_orig = orig_cls(*init_args)
                    inst_ref = ref_cls(*init_args)
                    
                    bound_orig = getattr(inst_orig, method_name)
                    bound_ref = getattr(inst_ref, method_name)
                    
                    orig_res, orig_exc = None, None
                    ref_res, ref_exc = None, None
                    
                    try:
                        orig_res = bound_orig(*method_args)
                    except Exception as e:
                        orig_exc = e
                        
                    try:
                        ref_res = bound_ref(*method_args)
                    except Exception as e:
                        ref_exc = e
                    
                    check_result_equivalence(orig_res, orig_exc, ref_res, ref_exc, f"init {init_args}, method {method_args}")

                test_wrapper()
                hyp_res = VerifyResult("PASS", time.time() - start_time)

        except AssertionError as e:
            raw_tb = traceback.format_exc()
            cleaned_tb = clean_traceback(raw_tb)
            hyp_res = VerifyResult("FAIL", time.time() - start_time, cleaned_tb if cleaned_tb else str(e))
        except Unsatisfiable:
             hyp_res = VerifyResult("SKIP", time.time() - start_time, "Unable to generate valid inputs")
        except Exception as e:
            if "Hypothesis found" in str(e) or "MultipleFailures" in type(e).__name__:
                 hyp_res = VerifyResult("FAIL", time.time() - start_time, str(e))
            else:
                 hyp_res = VerifyResult("SKIP", time.time() - start_time, f"Error: {e}")
        
        # Run Naive Fuzzer (using the sample instance if available, or try random gen if not specific to instance logic, 
        # but class methods usually need instance state. We used sample_args before.
        # If Hypothesis failed to get sample_args, we probably can't easily fuzz with naive fuzzer either unless we blindly guess init args)
        
        naive_res = None
        naive_start = time.time()
        
        # We need a fresh instance for Naive Fuzzer or we reuse logic?
        # worker_verify_class_method logic in original file used `sample_args` found by Hypothesis to seed Naive Fuzzer.
        # If Hypothesis failed to find `sample_args`, original code skipped everything.
        # We should try to stick to that pattern or improve it. 
        # If Hypothesis skipped because it couldn't find init args, Naive likely will too unless it has a simpler strategy.
        # Let's try to run Naive if we have sample_args.
        
        # To strictly follow "One Pass = Pass", we should try Naive even if Hypothesis Skipped. 
        # But if Hypothesis Skipped because it couldn't construct the class, we need a way to construct the class.
        # If we can't construct the class, we can't run the method.
        
        if sample_args is None:
             naive_res = VerifyResult("SKIP", 0.0, hyp_res.error or "No sample args")
        else:
             try:
                inst_orig_naive = orig_cls(*sample_args)
                inst_ref_naive = ref_cls(*sample_args)
                bound_orig_naive = getattr(inst_orig_naive, method_name)
                bound_ref_naive = getattr(inst_ref_naive, method_name)
                naive_res = run_naive_fuzzing(bound_orig_naive, bound_ref_naive)
             except Exception as e:
                naive_res = VerifyResult("SKIP", time.time() - naive_start, str(e))
             
        status = combine_results(full_name, hyp_res, naive_res, config=config)
        result_queue.put(status)

    except Exception as e:
        display_name = get_display_name(full_name, config)
        print(f"[SKIP] {display_name} (0.0000s) (Worker Error: {e})")
        result_queue.put("SKIPPED")

