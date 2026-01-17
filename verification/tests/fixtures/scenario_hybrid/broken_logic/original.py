def crash_func(x):
    # Unconditionally raise to force SKIP
    raise RuntimeError("Expected test crash")

def check_threshold(val: int) -> bool:
    if val > 10:
        return True
    else:
        return False
