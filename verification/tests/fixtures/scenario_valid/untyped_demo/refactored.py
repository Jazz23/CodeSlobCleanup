def loose_add(a, b):
    # Identical logic, still untyped
    return a + b

def check_attributes(x):
    # Refactored logic, but behaviorally equivalent
    if hasattr(x, "keys"):
        return "Dict-like"
    if x is None:
        return "Nothing"
    return str(x)
