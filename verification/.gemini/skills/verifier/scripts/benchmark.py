# /// script
# dependencies = [
#     "hypothesis",
#     "matplotlib",
#     "numpy",
# ]
# ///

import argparse
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

try:
    from verification.tools.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies
except ImportError:
    try:
        from tools.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies
    except ImportError:
        from common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy, smart_infer_arg_strategies

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
    except Exception:
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

def main():
    parser = argparse.ArgumentParser(description="Benchmark refactored code against original code.")
    parser.add_argument("original", help="Path to original python file")
    parser.add_argument("refactored", help="Path to refactored python file")
    parser.add_argument("--plot", action="store_true", help="Generate benchmark plots")
    parser.add_argument("--output-dir", default="benchmark_results", help="Directory for plots")
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

    for func_name in common_funcs:
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        inputs = generate_benchmark_inputs(orig_func, config=config)
        if not inputs:
            continue
            
        orig_times = measure_execution_time(orig_func, inputs)
        ref_times = measure_execution_time(ref_func, inputs)
        
        orig_avg = np.mean(orig_times)
        ref_avg = np.mean(ref_times)
        
        speedup = f"{orig_avg / ref_avg:.2f}x" if ref_avg > 0 else "N/A"
        print(f"[SPEEDUP] {func_name}: {speedup}")

    common_classes = get_common_classes(orig_mod, ref_mod)
    
    for cls_name in common_classes:
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        
        try:
            init_inputs = generate_benchmark_inputs(orig_cls, 1, config=config)
            if not init_inputs:
                continue
            init_args = init_inputs[0]
            inst_orig = orig_cls(*init_args)
            inst_ref = ref_cls(*init_args)
        except Exception:
            continue
            
        methods1 = {n: m for n, m in inspect.getmembers(orig_cls, inspect.isfunction) if not n.startswith('_')}
        methods2 = {n: m for n, m in inspect.getmembers(ref_cls, inspect.isfunction) if not n.startswith('_')}
        common_methods = list(set(methods1.keys()).intersection(methods2.keys()))
        
        for method_name in common_methods:
            bound_orig = getattr(inst_orig, method_name)
            bound_ref = getattr(inst_ref, method_name)
            
            inputs = generate_benchmark_inputs(bound_orig, config=config)
            if not inputs:
                continue
                
            orig_times = measure_execution_time(bound_orig, inputs)
            ref_times = measure_execution_time(bound_ref, inputs)
            
            orig_avg = np.mean(orig_times)
            ref_avg = np.mean(ref_times)
            
            speedup = f"{orig_avg / ref_avg:.2f}x" if ref_avg > 0 else "N/A"
            # Use qualname style for class methods
            print(f"[SPEEDUP] {cls_name}.{method_name}: {speedup}")

if __name__ == "__main__":
    main()