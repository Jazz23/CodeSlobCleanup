# /// script
# dependencies = [
#     "hypothesis",
#     "matplotlib",
#     "numpy",
# ]
# ///

import time
import os
import sys

import inspect
import numpy as np
import matplotlib.pyplot as plt
import json
from typing import Callable, List, Any, Dict
from pathlib import Path
from hypothesis import given, settings, Phase, HealthCheck
import hypothesis.strategies as st

# Add paths for imports
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]
verification_root = current_file.parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(verification_root))

from common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies, get_display_name

def generate_benchmark_inputs(func: Callable, num_inputs: int = 100, validate: bool = True, config: Dict[str, Any] = None) -> List[Any]:
    """Generates a list of input tuples for the given function using Hypothesis."""
    args_strategy = smart_infer_arg_strategies(func, config=config)
    
    inputs = []
    target_count = num_inputs * 10 if validate else num_inputs
    candidates = []
    
    @settings(max_examples=target_count, phases=[Phase.generate], database=None, suppress_health_check=[HealthCheck.filter_too_much])
    @given(args_strategy)
    def collector(args):
        candidates.append(args)
        
    try:
        collector()
    except Exception:  # pragma: no cover
        pass
            
    if not validate:
        return candidates[:num_inputs]
        
    valid_inputs = []
    for args in candidates:
        try:
            func(*args)
            valid_inputs.append(args)
        except Exception:
            pass
        if len(valid_inputs) >= num_inputs:
            break
            
    return valid_inputs

def measure_execution_time(func: Callable, input_args_list: List[tuple], num_runs: int = 50) -> List[float]:
    """Measures execution time of func(*args) for the list of inputs."""
    env_runs = os.getenv("BENCHMARK_RUNS")
    if env_runs:
        num_runs = int(env_runs)
        
    times = []
    for _ in range(5):
        for args in input_args_list:
            try:
                func(*args)
            except:
                pass

    for _ in range(num_runs):
        start = time.perf_counter()
        for args in input_args_list:
            try:
                func(*args)
            except Exception:
                pass
        end = time.perf_counter()
        times.append(end - start)
        
    return times

import multiprocessing
from queue import Empty

# ... (imports remain)

def worker_benchmark_func(orig_path, ref_path, func_name, config):
    try:
        orig_mod = load_module_from_path(orig_path, "original_mod")
        ref_mod = load_module_from_path(ref_path, "refactored_mod")
        
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        display_name = get_display_name(func_name, config)
        
        inputs = generate_benchmark_inputs(orig_func, config=config)
        if not inputs:
            print(f"[SKIP] {display_name} (Unable to generate benchmark inputs)")
            return
            
        try:
            orig_times = measure_execution_time(orig_func, inputs)
            ref_times = measure_execution_time(ref_func, inputs)
            
            if not orig_times or not ref_times:
                print(f"[SKIP] {display_name} (Benchmark execution failed)")
                return

            orig_avg = np.mean(orig_times)
            ref_avg = np.mean(ref_times)
            
            speedup = f"{orig_avg / ref_avg:.2f}x" if ref_avg > 0 else "N/A"
            print(f"[SPEEDUP] {display_name}: {speedup}")
        except Exception as e:
            print(f"[SKIP] {display_name} (Error during benchmark: {e})")
    except Exception as e:
        display_name = get_display_name(func_name, config)
        print(f"[SKIP] {display_name} (Worker Error: {e})")

def worker_benchmark_class_method(orig_path, ref_path, cls_name, method_name, config):
    # Similar logic for class methods
    try:
        orig_mod = load_module_from_path(orig_path, "original_mod")
        ref_mod = load_module_from_path(ref_path, "refactored_mod")
        
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        
        full_name = f"{cls_name}.{method_name}"
        display_name = get_display_name(full_name, config)
        
        try:
            init_inputs = generate_benchmark_inputs(orig_cls, 1, config=config)
            if not init_inputs:
                print(f"[SKIP] {display_name} (Unable to generate constructor arguments)")
                return
            init_args = init_inputs[0]
            inst_orig = orig_cls(*init_args)
            inst_ref = ref_cls(*init_args)
        except Exception as e:
            print(f"[SKIP] {display_name} (Error during constructor: {e})")
            return
            
        bound_orig = getattr(inst_orig, method_name)
        bound_ref = getattr(inst_ref, method_name)
        
        inputs = generate_benchmark_inputs(bound_orig, config=config)
        if not inputs:
            print(f"[SKIP] {display_name} (Unable to generate benchmark inputs)")
            return
            
        orig_times = measure_execution_time(bound_orig, inputs)
        ref_times = measure_execution_time(bound_ref, inputs)
        
        orig_avg = np.mean(orig_times)
        ref_avg = np.mean(ref_times)
        
        speedup = f"{orig_avg / ref_avg:.2f}x" if ref_avg > 0 else "N/A"
        print(f"[SPEEDUP] {display_name}: {speedup}")
    except Exception:
        pass

def run_with_timeout(target, args, name, timeout=15):
    p = multiprocessing.Process(target=target, args=args)
    p.start()
    p.join(timeout=timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        print(f"[SKIP] {name} (Timeout)")

