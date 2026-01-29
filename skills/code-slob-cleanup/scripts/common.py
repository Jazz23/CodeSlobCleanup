# /// script
# dependencies = [
#     "hypothesis",
# ]
# ///

import sys
import os
import subprocess

# Configure pycache to be created in the root of the active git repository
# This runs on import to ensure all scripts importing this module share the config.
try:
    # Try to find git root
    _git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL, text=True).strip()
    _pycache_dir = os.path.join(_git_root, "__pycache__")
    os.makedirs(_pycache_dir, exist_ok=True)
    sys.pycache_prefix = _pycache_dir
    os.environ["PYTHONPYCACHEPREFIX"] = _pycache_dir
except Exception:
    # Fallback to local directory if git fails
    try:
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        _target_root = os.path.abspath(os.path.join(_script_dir, ".."))
        _pycache_dir = os.path.join(_target_root, "__pycache__")
        os.makedirs(_pycache_dir, exist_ok=True)
        sys.pycache_prefix = _pycache_dir
        os.environ["PYTHONPYCACHEPREFIX"] = _pycache_dir
    except Exception:
        pass

import importlib.util
import inspect
import hypothesis.strategies as st
from typing import List, Callable, Any, Tuple, Dict, Union
import itertools
import random
import json
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
    """Returns a list of function names present in both modules, defined in the modules."""
    funcs1 = {n for n, f in inspect.getmembers(mod1, inspect.isfunction) if getattr(f, '__module__', None) == mod1.__name__}
    funcs2 = {n for n, f in inspect.getmembers(mod2, inspect.isfunction) if getattr(f, '__module__', None) == mod2.__name__}
    return list(funcs1.intersection(funcs2))

def get_common_classes(mod1, mod2) -> List[str]:
    """Returns a list of class names present in both modules, defined in the modules."""
    cls1 = {n for n, c in inspect.getmembers(mod1, inspect.isclass) if getattr(c, '__module__', None) == mod1.__name__}
    cls2 = {n for n, c in inspect.getmembers(mod2, inspect.isclass) if getattr(c, '__module__', None) == mod2.__name__}
    return list(cls1.intersection(cls2))

def _json_type_to_strategy(type_str: str) -> st.SearchStrategy:
    """Maps a type string from JSON to a Hypothesis strategy."""
    type_str = type_str.lower().strip()
    
    # Parse int(min, max)
    if type_str.startswith("int(") and type_str.endswith(")"):
        try:
            content = type_str[4:-1]
            parts = content.split(',')
            if len(parts) == 2:
                min_val = int(parts[0].strip())
                max_val = int(parts[1].strip())
                return st.integers(min_value=min_val, max_value=max_val)
        except ValueError:
            pass # Fallback

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
        0,              # zero
        -1,             # negative int
        1.5,            # float
        "test",         # str
        "",             # empty str
        True,           # bool
        None,           # NoneType
        [1, 2],         # simple list
        [],             # empty list
        {"a": 1},       # simple dict
        {},             # empty dict
        [{"name": "test", "age": 25, "score": 90}], # list of dicts (common in data processing)
        {"key": ["val1", "val2"]},                 # dict with list
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

from hypothesis.errors import Unsatisfiable

def smart_infer_arg_strategies(func: Callable, config: Dict[str, Any] = None) -> st.SearchStrategy:
    """
    Intelligently deduces a strategy for function arguments.
    Priority 1: Type hints (if all parameters are typed)
    Priority 2: Passed config dictionary (checks qualname first, then name)
    Priority 3: Probe/Heuristic
    """
    if config is None:
        config = {}
        
    sig = inspect.signature(func)
    params = [p for p in sig.parameters.values() if p.name != 'self']
    
    # 1. Check Type Hints
    if params and all(p.annotation != inspect.Parameter.empty for p in params):
        return st.tuples(*[infer_strategy(p) for p in params])

    name = func.__name__
    qualname = func.__qualname__
    
    # 2. Check Config
    # Prefer strict match (QualName) over simple Name
    target_key = None
    if qualname in config:
        target_key = qualname
    elif name in config:
        target_key = name
        
    if target_key:
        print(f"    [INFO] Found config entry for {target_key}")
        type_list = config[target_key]
        strategies = [_json_type_to_strategy(t) for t in type_list]
        return st.tuples(*strategies)

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
        # For many args, product is too slow. 
        # Try: all same
        for val in candidates:
            args = (val,) * num_args
            try:
                func(*args)
                working_signatures.append(args)
            except Exception:
                pass
        
        # Try: one of each type in sequence
        if num_args <= len(candidates):
            args = tuple(candidates[:num_args])
            try:
                func(*args)
                working_signatures.append(args)
            except Exception:
                pass

        # Try: more random trials
        for _ in range(20000):
            args = tuple(random.choice(candidates) for _ in range(num_args))
            try:
                func(*args)
                working_signatures.append(args)
                if len(working_signatures) > 100:
                    break
            except Exception:
                pass
                
    if not working_signatures:
        print(f"    [INFO] Smart inference failed to find simple valid inputs for {func.__name__}.")
        # Instead of falling back to blind fuzzing which often results in fake [PASS] 
        # for functions that always crash on standard types, we raise Unsatisfiable 
        # if there are NO type hints and NO config.
        raise Unsatisfiable(f"Could not find valid inputs for untyped function {func.__name__}")
        
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
