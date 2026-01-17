def crash_func(x):
    raise RuntimeError("Expected test crash")

def check_threshold(val: int) -> bool:
    return val >= 10
