def deep_update(target, updates):
    """
    Recursively updates a dictionary. 
    Expects (dict, dict). Crashes on anything else.
    """
    # Slob: No type checks, implicit assumption of .items()
    for key, value in updates.items():
        if isinstance(value, dict) and value: # Check if non-empty dict
            # Recursion - assumes target[key] exists and is dict if we are to recurse?
            # Actually, slob code often crashes if target[key] isn't a dict.
            if key in target and isinstance(target[key], dict):
                deep_update(target[key], value)
            else:
                target[key] = value
        else:
            target[key] = value
    return target

def compute_average(numbers):
    """
    Calculates average of a list of numbers.
    Expects list. Crashes on int/str/None.
    """
    # Slob: manual summation
    total = 0
    count = 0
    for x in numbers:
        total += x
        count += 1
    if count == 0:
        return 0
    return total / count

def format_repeat(text, count):
    """
    Repeats text count times.
    Expects (str, int).
    """
    # Slob: loop string concatenation
    result = ""
    # If count is not int, range() crashes
    for _ in range(count):
        # If text is not str, += might work (if int) or crash
        result += text
    return result
