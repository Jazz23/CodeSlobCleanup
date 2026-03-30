def safe_divide(x: int, y: int) -> float:
    if y == 0:
        raise ValueError("Division by zero")
    return x / y
