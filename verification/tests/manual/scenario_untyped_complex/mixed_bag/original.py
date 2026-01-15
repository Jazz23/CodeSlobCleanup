def mixed_bag(a, b, c, d, e, f):
    """
    Requires strict types:
    a: int (uses bit_length)
    b: int (uses bit_length)
    c: str (uses startswith)
    d: str (uses endswith)
    e: list (uses e.pop() if not empty, or e.copy())
    f: dict (uses items)
    """
    # Strict checks via usage
    val = a.bit_length() + b.bit_length()
    
    if c.startswith("a"):
        val += 1
    if d.endswith("z"):
        val += 1
        
    # List specific: copy() works on list, not tuple (in older python? No, tuple has no copy).
    # actually tuple doesn't have copy method in standard python?
    # Let's use something very list specific.
    # e.insert(0, 1) ? Modifies.
    # e + [1] works for list, not tuple.
    temp_list = e + [1]
    val += len(temp_list)
    
    # Dict specific
    val += len(f.items())
    
    return val

def homogeneous_bag(a, b, c, d, e, f):
    """
    Works if all are ints or all are strings (concatenation).
    """
    return a + b + c + d + e + f