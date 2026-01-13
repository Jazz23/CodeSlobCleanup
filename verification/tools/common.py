import importlib.util
import inspect
import sys
import hypothesis.strategies as st
from typing import List

def load_module_from_path(file_path: str, module_name: str):
    """Dynamically loads a python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def get_common_functions(mod1, mod2) -> List[str]:
    """Returns a list of function names present in both modules."""
    funcs1 = {n for n, _ in inspect.getmembers(mod1, inspect.isfunction)}
    funcs2 = {n for n, _ in inspect.getmembers(mod2, inspect.isfunction)}
    return list(funcs1.intersection(funcs2))

def get_common_classes(mod1, mod2) -> List[str]:
    """Returns a list of class names present in both modules."""
    cls1 = {n for n, _ in inspect.getmembers(mod1, inspect.isclass)}
    cls2 = {n for n, _ in inspect.getmembers(mod2, inspect.isclass)}
    return list(cls1.intersection(cls2))

def infer_strategy(param: inspect.Parameter) -> st.SearchStrategy:
    """Infers a Hypothesis strategy based on type hint or default."""
    if param.annotation != inspect.Parameter.empty:
        try:
            return st.from_type(param.annotation)
        except Exception:
            pass # Fallback if resolution fails
    
    # Fallback strategies for untyped arguments
    return st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none(),
        st.booleans(),
        st.recursive(
            st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())),
            lambda children: st.lists(children) | st.dictionaries(st.text(), children),
            max_leaves=10
        )
    )
