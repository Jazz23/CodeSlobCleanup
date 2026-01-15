def mixed_bag(a, b, c, d, e, f):
    """
    Refactored: same logic.
    """
    # Robust checks normally, but here we mimic logic for verification
    val = a.bit_length() + b.bit_length()
    
    if c.startswith("a"):
        val += 1
    if d.endswith("z"):
        val += 1
        
    temp_list = e + [1]
    val += len(temp_list)
    
    val += len(f.items())
    
    return val

def homogeneous_bag(a, b, c, d, e, f):
    """
    Refactored: same logic.
    """
    return a + b + c + d + e + f