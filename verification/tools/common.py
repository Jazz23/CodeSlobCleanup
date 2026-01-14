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

import importlib.util
import inspect
import sys
import hypothesis.strategies as st
from typing import List, Callable, Any, Tuple
import itertools

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
    if param.annotation == int:
        return st.integers(min_value=-50, max_value=50)
        
    if param.annotation != inspect.Parameter.empty:
        try:
            return st.from_type(param.annotation)
        except Exception:
            pass # Fallback if resolution fails
    
    # Fallback strategies for untyped arguments
    return st.one_of(
        st.integers(min_value=-50, max_value=50),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none(),
        st.booleans(),
        st.recursive(
            st.dictionaries(st.text(), st.one_of(st.text(), st.integers(min_value=-50, max_value=50), st.booleans())),
            lambda children: st.lists(children) | st.dictionaries(st.text(), children),
            max_leaves=10
        )
    )

def _get_candidate_values() -> List[Any]:
    """Returns a list of representative values for various types."""
    return [
        1,              # int
        1.5,            # float
        "test",         # str
        True,           # bool
        None,           # NoneType
        [1, 2],         # list
        {"a": 1},       # dict
    ]

def _type_to_strategy(val: Any) -> st.SearchStrategy:
    """Maps a value's type to a Hypothesis strategy."""
    if isinstance(val, bool):
        return st.booleans()
    if isinstance(val, int):
        return st.integers(min_value=-100, max_value=100)
    if isinstance(val, float):
        return st.floats(allow_nan=False, allow_infinity=False)
    if isinstance(val, str):
        return st.text()
    if val is None:
        return st.none()
    if isinstance(val, list):
        return st.lists(st.integers() | st.text(), max_size=5) # simplified list strategy
    if isinstance(val, dict):
        return st.dictionaries(st.text(), st.integers() | st.text(), max_size=5) # simplified dict
    return st.just(val)

import random

def smart_infer_arg_strategies(func: Callable) -> st.SearchStrategy:
    """
    Intelligently deduces a strategy for function arguments by probing the function
    with various combinations of types. Returns a strategy generating valid argument tuples.
    """
    sig = inspect.signature(func)
    params = [p for p in sig.parameters.values() if p.name != 'self']
    
    # If fully typed, just use standard inference
    if all(p.annotation != inspect.Parameter.empty for p in params):
        return st.tuples(*[infer_strategy(p) for p in params])
        
    num_args = len(params)
    if num_args == 0:
        return st.tuples()
        
    candidates = _get_candidate_values()
    
    # Limit combinations for performance (max 3 args for exhaustive, else random/homogeneous)
    working_signatures = []
    
    if num_args <= 3:
        # Try all combinations
        combinations = itertools.product(candidates, repeat=num_args)
        for args in combinations:
            try:
                func(*args)
                working_signatures.append(tuple(args))
            except Exception:
                pass
    else:
        # 1. Try homogeneous (all ints, all strs)
        for val in candidates:
            args = (val,) * num_args
            try:
                func(*args)
                working_signatures.append(args)
            except Exception:
                pass
        
        # 2. Random Probing if we haven't found many (or any) signatures
        # Try 5000 random combinations to catch mixed types (e.g. int, int, str, dict...)
        # 7 candidates ^ 6 args = 117k combos. 5k = ~4% coverage. 
        # But many combos might crash early, so it's fast.
        for _ in range(5000):
            args = tuple(random.choice(candidates) for _ in range(num_args))
            try:
                func(*args)
                working_signatures.append(args)
            except Exception:
                pass
                
    if not working_signatures:
        # Fallback: nothing simple worked, return the blind "try everything" strategy
        print(f"    [INFO] Smart inference failed to find simple valid inputs for {func.__name__}. Falling back to blind fuzzing.")
        return st.tuples(*[infer_strategy(p) for p in params])
        
    # Group working signatures by type to form strategies
    # e.g. if (1, 2) works, we add (st.ints, st.ints)
    # if ("a", "b") works, we add (st.text, st.text)
    strategy_options = []
    seen_types = set()
    
    for args in working_signatures:
        arg_types = tuple(type(a) for a in args)
        if arg_types in seen_types:
            continue
        seen_types.add(arg_types)
        
        strategies = [_type_to_strategy(a) for a in args]
        strategy_options.append(st.tuples(*strategies))
        
    if not strategy_options:
        return st.tuples(*[infer_strategy(p) for p in params])
        
    print(f"    [INFO] Smart inference deduced {len(strategy_options)} valid signatures for {func.__name__}.")
    return st.one_of(*strategy_options)
