def safe_divide(x: int, y: int) -> float:
    if y == 0:
        return 0.0  # should have raised
    return x / y
