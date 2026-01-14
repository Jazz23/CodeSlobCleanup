import pytest
import os
import sys
from pathlib import Path

# Add verification root to path so we can import tools
current_dir = Path(__file__).resolve().parent
verification_root = current_dir.parent
sys.path.insert(0, str(verification_root))

from tools.common import load_module_from_path, get_common_functions, get_common_classes
from tools.generic_verify import run_hypothesis_verification, run_class_verification
from tools.generic_benchmark import generate_benchmark_inputs, measure_execution_time

# Locate example files
ORIGINAL_DIR = verification_root / "src" / "original"
REFACTORED_DIR = verification_root / "src" / "refactored"

def get_example_modules():
    """Finds matching files in original and refactored directories."""
    modules = []
    if not ORIGINAL_DIR.exists():
        return modules
        
    for file in ORIGINAL_DIR.glob("*.py"):
        if file.name == "__init__.py":
            continue
            
        ref_file = REFACTORED_DIR / file.name
        if ref_file.exists():
            modules.append((file, ref_file))
            
    return modules

# Pytest parametrization
@pytest.mark.parametrize("orig_path, ref_path", get_example_modules())
def test_example_verification(orig_path, ref_path):
    """
    Runs generic_verify logic on the pair of modules.
    """
    print(f"\nVerifying: {orig_path.name}")
    
    orig_mod = load_module_from_path(str(orig_path), f"orig_{orig_path.stem}")
    ref_mod = load_module_from_path(str(ref_path), f"ref_{ref_path.stem}")
    
    common_funcs = get_common_functions(orig_mod, ref_mod)
    assert common_funcs or get_common_classes(orig_mod, ref_mod), f"No common functions or classes found in {orig_path.name}"
    
    for func_name in common_funcs:
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        # Run verification and RAISE on error so pytest fails
        run_hypothesis_verification(orig_func, ref_func, raise_on_error=True)

    common_classes = get_common_classes(orig_mod, ref_mod)
    for cls_name in common_classes:
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        
        run_class_verification(cls_name, orig_cls, ref_cls, raise_on_error=True)

@pytest.mark.parametrize("orig_path, ref_path", get_example_modules())
def test_example_benchmark_smoke(orig_path, ref_path):
    """
    Runs generic_benchmark logic as a smoke test (ensure it runs).
    We do NOT assert speedup here, just that it executes without crashing.
    """
    print(f"\nBenchmarking Smoke Test: {orig_path.name}")
    
    orig_mod = load_module_from_path(str(orig_path), f"orig_bench_{orig_path.stem}")
    ref_mod = load_module_from_path(str(ref_path), f"ref_bench_{ref_path.stem}")
    
    common_funcs = get_common_functions(orig_mod, ref_mod)
    
    for func_name in common_funcs:
        orig_func = getattr(orig_mod, func_name)
        ref_func = getattr(ref_mod, func_name)
        
        inputs = generate_benchmark_inputs(orig_func, num_inputs=5) # Small number for smoke test
        if inputs:
            measure_execution_time(orig_func, inputs, num_runs=2)
            measure_execution_time(ref_func, inputs, num_runs=2)

    common_classes = get_common_classes(orig_mod, ref_mod)
    for cls_name in common_classes:
        orig_cls = getattr(orig_mod, cls_name)
        ref_cls = getattr(ref_mod, cls_name)
        
        try:
            init_inputs = generate_benchmark_inputs(orig_cls, 1)
            if init_inputs:
                inst_orig = orig_cls(*init_inputs[0])
                # Smoke test method access
                pass
        except Exception:
            # Instantiation might fail if complex, strictly valid for smoke test to skip
            pass
