import importlib.util
import inspect
import sys
import hypothesis.strategies as st
from typing import List, Callable, Any, Tuple, Dict, Union
import itertools
import random
import json
import os
from pathlib import Path

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

def load_verification_config() -> Dict[str, List[str]]:
    """Loads verification_config.json if it exists."""
    # Check current dir and verification dir
    paths = ["verification_config.json", "verification/verification_config.json"]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    print(f"    [INFO] Loading config from {p}")
                    return json.load(f)
            except Exception as e:
                print(f"    [WARN] Failed to load config {p}: {e}")
    return {}

def _json_type_to_strategy(type_str: str) -> st.SearchStrategy:
    """Maps a type string from JSON to a Hypothesis strategy."""
    type_str = type_str.lower().strip()
    if type_str == "int":
        return st.integers(min_value=-100, max_value=100)
    if type_str == "float":
        return st.floats(allow_nan=False, allow_infinity=False)
    if type_str == "str" or type_str == "string":
        return st.text()
    if type_str == "bool":
        return st.booleans()
    if type_str == "list":
        return st.lists(st.integers() | st.text(), max_size=5)
    if type_str == "dict":
        return st.dictionaries(st.text(), st.integers() | st.text(), max_size=5)
    if type_str == "none":
        return st.none()
    
    # Fallback/Default
    return st.integers() | st.text()

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
        return st.lists(st.integers() | st.text(), max_size=5)
    if isinstance(val, dict):
        return st.dictionaries(st.text(), st.integers() | st.text(), max_size=5)
    return st.just(val)

def smart_infer_arg_strategies(func: Callable) -> st.SearchStrategy:
    """
    Intelligently deduces a strategy for function arguments.
    Priority 1: verification_config.json
    Priority 2: Type hints
    Priority 3: Probe/Heuristic
    """
    config = load_verification_config()
    func_name = func.__name__
    
    # 1. Check Config
    if func_name in config:
        print(f"    [INFO] Found JSON config for {func_name}")
        type_list = config[func_name]
        strategies = [_json_type_to_strategy(t) for t in type_list]
        return st.tuples(*strategies)

    sig = inspect.signature(func)
    params = [p for p in sig.parameters.values() if p.name != 'self']
    
    # 2. Check Type Hints
    if all(p.annotation != inspect.Parameter.empty for p in params):
        return st.tuples(*[infer_strategy(p) for p in params])
        
    num_args = len(params)
    if num_args == 0:
        return st.tuples()
        
    candidates = _get_candidate_values()
    
    # 3. Probe
    working_signatures = []
    
    if num_args <= 3:
        combinations = itertools.product(candidates, repeat=num_args)
        for args in combinations:
            try:
                func(*args)
                working_signatures.append(tuple(args))
            except Exception:
                pass
    else:
        for val in candidates:
            args = (val,) * num_args
            try:
                func(*args)
                working_signatures.append(args)
            except Exception:
                pass
        
        for _ in range(5000):
            args = tuple(random.choice(candidates) for _ in range(num_args))
            try:
                func(*args)
                working_signatures.append(args)
            except Exception:
                pass
                
    if not working_signatures:
        print(f"    [INFO] Smart inference failed to find simple valid inputs for {func.__name__}. Falling back to blind fuzzing.")
        return st.tuples(*[infer_strategy(p) for p in params])
        
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