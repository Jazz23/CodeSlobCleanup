def deep_update(target, updates):
    """
    Recursively updates a dictionary. 
    Refactored: Cleaner logic.
    """
    if not isinstance(target, dict) or not isinstance(updates, dict):
        # We must mimic crash behavior? Or can we just return?
        # If we return, tests fail because Original crashes.
        # For this test, we want to prove smart_infer finds valid inputs.
        # So we just implement the logic similarly but cleaner.
        raise AttributeError("Input must be dict") 
    
    for key, value in updates.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            deep_update(target[key], value)
        else:
            target[key] = value
    return target

def compute_average(numbers):
    """
    Calculates average of a list of numbers.
    Refactored: sum() / len()
    """
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def format_repeat(text, count):
    """
    Repeats text count times.
    Refactored: Pythonic
    """
    return text * count
