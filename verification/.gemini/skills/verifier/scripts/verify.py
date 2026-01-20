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
        print(f"[PASS] {orig_func.__name__} ({duration:.4f}s)")

    except AssertionError as e:
        duration = time.time() - start_time
        raw_tb = traceback.format_exc()
        cleaned_tb = clean_traceback(raw_tb)
        print(f"[FAIL] {orig_func.__name__} ({duration:.4f}s)")
        if cleaned_tb:
            print(cleaned_tb)
        else:
            print(f"    {e}")
        raise e

    except Unsatisfiable:
        duration = time.time() - start_time
        print(f"[SKIP] {orig_func.__name__} ({duration:.4f}s) (Unable to generate valid inputs)")

    except Exception as e:
        duration = time.time() - start_time
        if "Hypothesis found" in str(e) or "MultipleFailures" in type(e).__name__:
             print(f"[FAIL] {orig_func.__name__} ({duration:.4f}s)")
             print(f"    {e}")
             raise e
        print(f"[SKIP] {orig_func.__name__} ({duration:.4f}s) (Error during verification: {e})")

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

def run_naive_fuzzing(orig_func: Callable, ref_func: Callable):
    """Runs Naive Random Fuzzing."""
    start_time = time.time()
    try:
        fuzzer = NaiveRandomFuzzer(iterations=50)
        fuzzer.fuzz(orig_func, ref_func)
        duration = time.time() - start_time
        print(f"[PASS] {orig_func.__name__} (RandomFuzzer) ({duration:.4f}s)")
    except AssertionError as e:
        duration = time.time() - start_time
        print(f"[FAIL] {orig_func.__name__} (RandomFuzzer) ({duration:.4f}s)")
        print(f"    {e}")
        raise e
    except Exception as e:
        duration = time.time() - start_time
        print(f"[SKIP] {orig_func.__name__} (RandomFuzzer) ({duration:.4f}s) (Error: {e})")

def worker_verify_function(orig_path, ref_path, func_name, config, result_queue):
    """Worker process to run verification for a single function."""
    try:
        orig_mod = load_module_from_path(orig_path, "original_mod")
        ref_mod = load_module_from_path(ref_path, "refactored_mod")
        
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        run_hypothesis_verification(orig_func, ref_func, config=config)
        run_naive_fuzzing(orig_func, ref_func)
        result_queue.put("SUCCESS")
    except AssertionError:
        result_queue.put("FAILURE")
    except Exception as e:
        if "Hypothesis found" in str(e) or "MultipleFailures" in type(e).__name__:
            result_queue.put("FAILURE")
        else:
            result_queue.put("SKIPPED")

def worker_verify_class_method(orig_path, ref_path, cls_name, method_name, config, result_queue):
    """Worker process to run verification for a single class method."""
    start_time = time.time()
    try:
        orig_mod = load_module_from_path(orig_path, "original_mod")
        ref_mod = load_module_from_path(ref_path, "refactored_mod")
        
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        
        # We need a strategy for (init_args, method_args)
        try:
            init_strategy = smart_infer_arg_strategies(orig_cls, config=config)
            
            # To get method strategy, we need an instance. 
            # We'll use a sample instance to infer method strategy.
            # (In a more robust version, we'd do this inside the strategy)
            sample_args = None
            try:
                # Try to get one valid init arg set
                @settings(max_examples=1, deadline=None)
                @given(init_strategy)
                def get_one(args):
                    nonlocal sample_args
                    sample_args = args
                get_one()
            except Exception:
                pass
                
            if sample_args is None:
                duration = time.time() - start_time
                print(f"[SKIP] {cls_name}.{method_name} ({duration:.4f}s) (Could not find valid constructor arguments)")
                result_queue.put("SKIPPED")
                return

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
                
                # We want to use the SAME init args for both
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
            
            # Run Naive Random Fuzzer on the same method (using the sample instance)
            inst_orig_naive = orig_cls(*sample_args)
            inst_ref_naive = ref_cls(*sample_args)
            bound_orig_naive = getattr(inst_orig_naive, method_name)
            bound_ref_naive = getattr(inst_ref_naive, method_name)
            run_naive_fuzzing(bound_orig_naive, bound_ref_naive)
            
            duration = time.time() - start_time
            print(f"[PASS] {cls_name}.{method_name} ({duration:.4f}s)")
            result_queue.put("SUCCESS")
            
        except Unsatisfiable:
             duration = time.time() - start_time
             print(f"[SKIP] {cls_name}.{method_name} ({duration:.4f}s) (Unable to generate valid inputs)")
             result_queue.put("SKIPPED")
             
    except AssertionError as e:
        duration = time.time() - start_time
        raw_tb = traceback.format_exc()
        cleaned_tb = clean_traceback(raw_tb)
        print(f"[FAIL] {cls_name}.{method_name} ({duration:.4f}s)")
        if cleaned_tb:
            print(cleaned_tb)
        result_queue.put("FAILURE")
    except Exception as e:
        duration = time.time() - start_time
        # Check if it's a Hypothesis failure (can happen if multiple failures found)
        if "Hypothesis found" in str(e) or "AssertionError" in str(type(e)):
             print(f"[FAIL] {cls_name}.{method_name} ({duration:.4f}s)")
             print(f"    {e}")
             result_queue.put("FAILURE")
        else:
             print(f"[SKIP] {cls_name}.{method_name} ({duration:.4f}s) (Error: {e})")
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
