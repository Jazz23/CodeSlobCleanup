import time
import matplotlib.pyplot as plt
import numpy as np
from typing import Callable, List, Any, Dict
import os

class BenchmarkRunner:
    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def measure_execution_time(self, func: Callable, inputs: List[Any], num_runs: int = 100) -> List[float]:
        """
        Measures execution time for a function over multiple runs.
        Returns a list of execution times in seconds.
        """
        times = []
        # Warmup
        for _ in range(max(1, int(num_runs * 0.1))):
            for i in inputs:
                func(i)

        for _ in range(num_runs):
            start_time = time.perf_counter()
            for i in inputs:
                func(i)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        return times

    def compare(self, 
                name: str,
                original_func: Callable, 
                refactored_func: Callable, 
                input_generator: Callable[[], List[Any]], 
                num_runs: int = 100):
        """
        Compares original and refactored functions.
        """
        print(f"Benchmarking {name}...")
        inputs = input_generator()
        
        # Measure Original
        original_times = self.measure_execution_time(original_func, inputs, num_runs)
        original_avg = np.mean(original_times)
        original_std = np.std(original_times)
        
        # Measure Refactored
        refactored_times = self.measure_execution_time(refactored_func, inputs, num_runs)
        refactored_avg = np.mean(refactored_times)
        refactored_std = np.std(refactored_times)

        print(f"  Original:   {original_avg:.6f}s ± {original_std:.6f}s")
        print(f"  Refactored: {refactored_avg:.6f}s ± {refactored_std:.6f}s")
        
        speedup = original_avg / refactored_avg if refactored_avg > 0 else 0.0
        print(f"  Speedup:    {speedup:.2f}x")

        self.plot_results(name, original_times, refactored_times)
        return {
            "name": name,
            "original_avg": original_avg,
            "refactored_avg": refactored_avg,
            "speedup": speedup
        }

    def plot_results(self, name: str, original_times: List[float], refactored_times: List[float]):
        plt.figure(figsize=(10, 6))
        
        labels = ['Original', 'Refactored']
        means = [np.mean(original_times), np.mean(refactored_times)]
        stds = [np.std(original_times), np.std(refactored_times)]
        
        x = np.arange(len(labels))
        width = 0.35
        
        fig, ax = plt.subplots()
        rects = ax.bar(x, means, width, yerr=stds, capsize=5, label=labels, color=['red', 'green'])
        
        ax.set_ylabel('Execution Time (seconds)')
        ax.set_title(f'Performance Comparison: {name}')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        
        # Add speedup text
        speedup = means[0] / means[1] if means[1] > 0 else 0
        ax.text(0.5, 0.95, f'Speedup: {speedup:.2f}x', transform=ax.transAxes, 
                ha='center', va='top', fontsize=12, fontweight='bold')

        plt.tight_layout()
        output_path = os.path.join(self.output_dir, f"{name.lower().replace(' ', '_')}_benchmark.png")
        plt.savefig(output_path)
        plt.close()
        print(f"  Plot saved to {output_path}")

if __name__ == "__main__":
    print("This is a library. Import it to use.")
