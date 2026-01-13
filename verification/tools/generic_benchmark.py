import argparse
import time
import os
import inspect
import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, List, Any
from hypothesis import given, settings, Phase
import hypothesis.strategies as st

try:
    from verification.tools.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy
except ImportError:
    from tools.common import load_module_from_path, get_common_functions, get_common_classes, infer_strategy

def generate_benchmark_inputs(func: Callable, num_inputs: int = 100) -> List[Any]:
    """Generates a list of input tuples for the given function using Hypothesis."""
    sig = inspect.signature(func)
    strategies = [infer_strategy(param) for param in sig.parameters.values()]
    args_strategy = st.tuples(*strategies)
    
    inputs = []
    
    # We use a simple loop with strategy.example() for simplicity in this script, 
    # acknowledging it might not be perfectly reproducible or diverse without full engine.
    # However, to be robust, we'll try to use the engine.
    
    @settings(max_examples=num_inputs, phases=[Phase.generate], database=None)
    @given(args_strategy)
    def collector(args):
        inputs.append(args)
        
    try:
        collector()
    except Exception:
        pass
        
    # Fallback if collector didn't get enough (e.g. constraints)
    while len(inputs) < num_inputs:
        try:
            inputs.append(args_strategy.example())
        except:
            break
            
    return inputs[:num_inputs]

def measure_execution_time(func: Callable, input_args_list: List[tuple], num_runs: int = 50) -> List[float]:
    """Measures execution time of func(*args) for the list of inputs."""
    times = []
    # Warmup
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
                pass # Benchmark should ideally handle valid inputs, but we catch to avoid crash
        end = time.perf_counter()
        times.append(end - start)
        
    return times

def plot_results(name: str, orig_times: List[float], ref_times: List[float], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    labels = ['Original', 'Refactored']
    means = [np.mean(orig_times), np.mean(ref_times)]
    stds = [np.std(orig_times), np.std(ref_times)]
    
    x = np.arange(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(8, 6))
    rects = ax.bar(x, means, width, yerr=stds, capsize=5, label=labels, color=['#d62728', '#2ca02c'])
    
    ax.set_ylabel('Execution Time (s)')
    ax.set_title(f'Benchmark: {name}')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    
    # Speedup
    if means[1] > 0:
        speedup = means[0] / means[1]
        ax.text(0.5, 0.95, f'Speedup: {speedup:.2f}x', transform=ax.transAxes, 
                ha='center', va='top', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    clean_name = "".join(c if c.isalnum() else "_" for c in name)
    out_path = os.path.join(output_dir, f"{clean_name}_benchmark.png")
    plt.savefig(out_path)
    plt.close()
    print(f"    [INFO] Plot saved to {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Benchmark refactored code against original code.")
    parser.add_argument("original", help="Path to original python file")
    parser.add_argument("refactored", help="Path to refactored python file")
    parser.add_argument("--plot", action="store_true", help="Generate benchmark plots")
    parser.add_argument("--output-dir", default="benchmark_results", help="Directory for plots")
    args = parser.parse_args()

    orig_mod = load_module_from_path(args.original, "original_mod")
    ref_mod = load_module_from_path(args.refactored, "refactored_mod")

    common_funcs = get_common_functions(orig_mod, ref_mod)
    print(f"Found functions to benchmark: {common_funcs}")

    for func_name in common_funcs:
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        print(f"\nBenchmarking Function: {func_name}")
        
        # Generate inputs
        print("    Generating inputs...")
        inputs = generate_benchmark_inputs(orig_func)
        if not inputs:
            print("    [WARN] Could not generate inputs. Skipping.")
            continue
            
        # Benchmark
        print(f"    Running {len(inputs)} inputs per run...")
        orig_times = measure_execution_time(orig_func, inputs)
        ref_times = measure_execution_time(ref_func, inputs)
        
        orig_avg = np.mean(orig_times)
        ref_avg = np.mean(ref_times)
        
        print(f"    Original:   {orig_avg:.6f}s")
        print(f"    Refactored: {ref_avg:.6f}s")
        
        if ref_avg > 0:
            print(f"    Speedup:    {orig_avg / ref_avg:.2f}x")
        else:
            print(f"    Speedup:    N/A")
            
        if args.plot:
            plot_results(func_name, orig_times, ref_times, args.output_dir)

    common_classes = get_common_classes(orig_mod, ref_mod)
    print(f"Found classes to benchmark: {common_classes}")
    
    for cls_name in common_classes:
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        
        # Instantiate
        try:
            init_inputs = generate_benchmark_inputs(orig_cls, 1)
            if not init_inputs:
                print(f"    [WARN] Could not generate init args for {cls_name}. Skipping.")
                continue
            init_args = init_inputs[0]
            
            inst_orig = orig_cls(*init_args)
            inst_ref = ref_cls(*init_args)
        except Exception as e:
            print(f"    [WARN] Failed to instantiate {cls_name}: {e}")
            continue
            
        methods1 = {n: m for n, m in inspect.getmembers(orig_cls, inspect.isfunction) if not n.startswith('_')}
        methods2 = {n: m for n, m in inspect.getmembers(ref_cls, inspect.isfunction) if not n.startswith('_')}
        common_methods = list(set(methods1.keys()).intersection(methods2.keys()))
        
        for method_name in common_methods:
            print(f"\nBenchmarking Method: {cls_name}.{method_name}")
            
            bound_orig = getattr(inst_orig, method_name)
            bound_ref = getattr(inst_ref, method_name)
            
            print("    Generating inputs...")
            inputs = generate_benchmark_inputs(bound_orig)
            if not inputs:
                print("    [WARN] Could not generate inputs. Skipping.")
                continue
                
            print(f"    Running {len(inputs)} inputs per run...")
            orig_times = measure_execution_time(bound_orig, inputs)
            ref_times = measure_execution_time(bound_ref, inputs)
            
            orig_avg = np.mean(orig_times)
            ref_avg = np.mean(ref_times)
            
            print(f"    Original:   {orig_avg:.6f}s")
            print(f"    Refactored: {ref_avg:.6f}s")
            
            if ref_avg > 0:
                print(f"    Speedup:    {orig_avg / ref_avg:.2f}x")
            else:
                print(f"    Speedup:    N/A")
                
            if args.plot:
                plot_results(f"{cls_name}_{method_name}", orig_times, ref_times, args.output_dir)

if __name__ == "__main__":
    main()
