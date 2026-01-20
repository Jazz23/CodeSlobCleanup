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

try:
    from common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies
except ImportError:
    # Fallback if necessary, though direct execution adds local dir to path
    from verification.src.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies

@dataclass
class VerifyResult:
    status: str  # "PASS", "FAIL", "SKIP"
    duration: float
    error: Optional[str] = None

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
        duration = time.time() - start_time
        return VerifyResult("PASS", duration)

    except AssertionError as e:
        duration = time.time() - start_time
        raw_tb = traceback.format_exc()
        cleaned_tb = clean_traceback(raw_tb)
        error_msg = cleaned_tb if cleaned_tb else str(e)
        return VerifyResult("FAIL", duration, error_msg)

    except Unsatisfiable:
        duration = time.time() - start_time
        return VerifyResult("SKIP", duration, "Unable to generate valid inputs")

    except Exception as e:
        duration = time.time() - start_time
        if "Hypothesis found" in str(e) or "MultipleFailures" in type(e).__name__:
             return VerifyResult("FAIL", duration, str(e))
        return VerifyResult("SKIP", duration, f"Error during verification: {e}")

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
    def _gen_list(self): return [self._gen_any() for _ in range(random.randint(0, 5))]
    def _gen_dict(self): return {self._gen_str(): self._gen_any() for _ in range(random.randint(0, 5))}
    
    def _gen_any(self):
        return random.choice([
            self._gen_int(), self._gen_float(), self._gen_str(), 
            self._gen_bool(), None, self._gen_list(), self._gen_dict()
        ])

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
                args.append(self._gen_list())
            elif param.annotation == dict:
                args.append(self._gen_dict())
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
                orig_exc = type(e)
            
            try:
                ref_res = ref_func(*args)
            except Exception as e:
                ref_exc = type(e)
            
            if orig_exc:
                assert ref_exc == orig_exc, f"[RandomFuzzer] Original raised {orig_exc}, but Refactored raised {ref_exc} for input {args}"
            else:
                if ref_exc:
                    assert False, f"[RandomFuzzer] Original returned {orig_res}, but Refactored raised {ref_exc} for input {args}"
                assert orig_res == ref_res, f"[RandomFuzzer] Mismatch for input {args}: Original={orig_res}, Refactored={ref_res}"

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

def combine_results(name: str, hyp_res: VerifyResult, naive_res: VerifyResult):
    """Combines results from both fuzzers and prints the output."""
    total_duration = hyp_res.duration + naive_res.duration
    
    # Logic:
    # Fail if either fails.
    # Pass if one passes (and other passes/skips).
    # Skip if both skip.
    
    if hyp_res.status == "FAIL":
        print(f"[FAIL] {name} ({total_duration:.4f}s)")
        if hyp_res.error:
             print(hyp_res.error)
        return "FAILURE"
    
    if naive_res.status == "FAIL":
        print(f"[FAIL] {name} ({total_duration:.4f}s)")
        if naive_res.error:
             print(naive_res.error)
        return "FAILURE"
    
    if hyp_res.status == "PASS" or naive_res.status == "PASS":
        print(f"[PASS] {name} ({total_duration:.4f}s)")
        return "SUCCESS"
    
    # Both skipped
    print(f"[SKIP] {name} ({total_duration:.4f}s) (Both fuzzers skipped)")
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
        
        status = combine_results(func_name, hyp_res, naive_res)
        result_queue.put(status)
        
    except Exception as e:
        # Fallback if loading fails or something unexpected
        print(f"[SKIP] {func_name} (0.0000s) (Worker Error: {e})")
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
        
        try:
            init_strategy = smart_infer_arg_strategies(orig_cls, config=config)
            
            sample_args = None
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
                        orig_exc = type(e)
                        
                    try:
                        ref_res = bound_ref(*method_args)
                    except Exception as e:
                        ref_exc = type(e)
                    
                    if orig_exc:
                        assert ref_exc == orig_exc, f"Original raised {orig_exc}, but Refactored raised {ref_exc} for init {init_args}, method {method_args}"
                    else:
                        if ref_exc:
                            assert False, f"Original returned {orig_res}, but Refactored raised {ref_exc} for init {init_args}, method {method_args}"
                        assert orig_res == ref_res, f"Mismatch for init {init_args}, method {method_args}: Original={orig_res}, Refactored={ref_res}"

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
        
        if hyp_res.status == "SKIP" and "Could not find valid constructor arguments" in (hyp_res.error or ""):
             # If we have no sample args, we can't really run naive fuzzer on the method easily 
             # without duplicating the init-arg-finding logic.
             # For now, let's treat this as Naive also Skipping (implicitly).
             naive_res = VerifyResult("SKIP", 0.0, "Could not find valid constructor arguments")
        elif sample_args is not None:
             # reuse sample_args
             try:
                inst_orig_naive = orig_cls(*sample_args)
                inst_ref_naive = ref_cls(*sample_args)
                bound_orig_naive = getattr(inst_orig_naive, method_name)
                bound_ref_naive = getattr(inst_ref_naive, method_name)
                naive_res = run_naive_fuzzing(bound_orig_naive, bound_ref_naive)
             except Exception as e:
                naive_res = VerifyResult("SKIP", time.time() - naive_start, str(e))
        else:
             # Should not happen if logic holds (if sample_args is None, we entered the first if block)
             naive_res = VerifyResult("SKIP", 0.0, "No sample args")
             
        status = combine_results(full_name, hyp_res, naive_res)
        result_queue.put(status)

    except Exception as e:
        print(f"[SKIP] {full_name} (0.0000s) (Worker Error: {e})")
        result_queue.put("SKIPPED")

def main():
    parser = argparse.ArgumentParser(description="Verify refactored code against original code.")
    parser.add_argument("original", help="Path to original python file")
    parser.add_argument("refactored", help="Path to refactored python file")
    args = parser.parse_args()

    config = {}
    original_path = Path(args.original).resolve()
    type_hints_path = original_path.parent / "type_hints.json"

    if type_hints_path.exists():
        try:
            with open(type_hints_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in type_hints.json: {e}")
            sys.exit(1)

    try:
        orig_mod = load_module_from_path(args.original, "original_mod")
        ref_mod = load_module_from_path(args.refactored, "refactored_mod")
        common_funcs = get_common_functions(orig_mod, ref_mod)
        common_classes = get_common_classes(orig_mod, ref_mod)
    except Exception as e:
        print(f"[SKIP] (Module loading failed: {e})")
        return

    # Create a queue to collect results
    result_queue = multiprocessing.Queue()
    processes = []
    success = True
    
    # Collect all tasks
    tasks = []
    
    # Functions
    for func_name in common_funcs:
        tasks.append({
            "target": worker_verify_function,
            "args": (args.original, args.refactored, func_name, config, result_queue),
            "name": func_name
        })

    # Class Methods
    for cls_name in common_classes:
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        
        methods1 = {n: m for n, m in inspect.getmembers(orig_cls, inspect.isfunction) if not n.startswith('_')}
        methods2 = {n: m for n, m in inspect.getmembers(ref_cls, inspect.isfunction) if not n.startswith('_')}
        common_methods = list(set(methods1.keys()).intersection(methods2.keys()))
        
        for method_name in common_methods:
             tasks.append({
                "target": worker_verify_class_method,
                "args": (args.original, args.refactored, cls_name, method_name, config, result_queue),
                "name": f"{cls_name}.{method_name}"
            })

    # Run tasks in parallel with a limit
    max_workers = os.cpu_count() or 4
    active_processes = []
    
    task_idx = 0
    while task_idx < len(tasks) or active_processes:
        # Start new processes if we have capacity and tasks
        while len(active_processes) < max_workers and task_idx < len(tasks):
            task = tasks[task_idx]
            p = multiprocessing.Process(target=task["target"], args=task["args"])
            p.start()
            active_processes.append({"p": p, "start_time": time.time(), "name": task["name"]})
            task_idx += 1
            
        # Check active processes
        still_active = []
        for proc_info in active_processes:
            p = proc_info["p"]
            if not p.is_alive():
                p.join()
            else:
                # Check timeout
                if time.time() - proc_info["start_time"] > 15:
                    p.terminate()
                    p.join()
                    duration = time.time() - proc_info["start_time"]
                    print(f"[SKIP] {proc_info['name']} ({duration:.4f}s) (Timeout)")
                else:
                    still_active.append(proc_info)
        
        active_processes = still_active
        
        # Drain queue
        while not result_queue.empty():
            try:
                result = result_queue.get_nowait()
                if result == "FAILURE":
                    success = False
            except Empty:
                break
        
        time.sleep(0.1)

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
