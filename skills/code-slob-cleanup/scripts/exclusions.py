import os
import json
import fnmatch
from pathlib import Path

def load_config(root_dir):
    config_path = Path(root_dir) / "code-slob-cleanup.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

def get_inline_exclusions(file_path):
    exclusions = {
        "ignore_file": False,
        "ignored_functions": set(), # Set of line numbers that are ignored
        "ignored_blocks": [], # List of (start, end)
        "ignored_lines": set() # Set of line numbers
    }
    
    if not os.path.exists(file_path):
        return exclusions
        
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except Exception:
        return exclusions
        
    if lines and "# cs-cleanup: ignore-file" in lines[0]:
        exclusions["ignore_file"] = True
        return exclusions
        
    current_block_start = None
    
    for i, line in enumerate(lines):
        lineno = i + 1
        
        if "# cs-cleanup: ignore-function" in line:
            # Mark the next line as ignored (likely the function definition or decorator)
            exclusions["ignored_functions"].add(lineno + 1)
            
        if "# cs-cleanup: ignore-start" in line:
            current_block_start = lineno
            
        if "# cs-cleanup: ignore-end" in line:
            if current_block_start is not None:
                exclusions["ignored_blocks"].append((current_block_start, lineno))
                current_block_start = None
                
        if "# cs-cleanup: ignore" in line and "# cs-cleanup: ignore-" not in line:
             exclusions["ignored_lines"].add(lineno)
             
    return exclusions

def is_excluded(file_path, func_name, func_start, func_end, config, root_dir, inline_excl):
    if inline_excl.get("ignore_file"):
        return True

    # Check ignore-function (immediately preceding line)
    if func_start in inline_excl["ignored_functions"]:
        return True
        
    # Check ignored blocks
    for b_start, b_end in inline_excl["ignored_blocks"]:
        if b_start <= func_start <= b_end:
            return True
            
    # Check ignored lines within function
    for l_no in inline_excl["ignored_lines"]:
        if func_start <= l_no <= func_end:
            return True

    rel_path = os.path.relpath(file_path, root_dir)
    
    # Check excludePaths
    exclude_paths = config.get("excludePaths", [])
    for pattern in exclude_paths:
        # Simple glob match for file or folder
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, pattern.rstrip('/') + '/*'):
            return True
            
    # Check excludeFunctions
    exclude_funcs = config.get("excludeFunctions", [])
    for pattern in exclude_funcs:
        if ":" in pattern:
            path_pat, func_pat = pattern.split(":", 1)
            if fnmatch.fnmatch(rel_path, path_pat) and fnmatch.fnmatch(func_name, func_pat):
                return True
        else:
            if fnmatch.fnmatch(func_name, pattern):
                return True
                
    return False
