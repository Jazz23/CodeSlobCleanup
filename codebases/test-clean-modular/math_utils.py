def add(a: float, b: float) -> float:
    return a + b

def multiply(a: float, b: float) -> float:
    return a * b

def safe_divide(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b

def square(a: float) -> float:
    return a * a
