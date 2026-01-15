def loose_add(a, b):
    # No type hints! 
    # Hypothesis will try ints, strings, None, dicts...
    return a + b

def check_attributes(x):
    # Inspects 'x' without knowing what it is
    if hasattr(x, "keys"):
        return "Dict-like"
    if x is None:
        return "Nothing"
    return str(x)
