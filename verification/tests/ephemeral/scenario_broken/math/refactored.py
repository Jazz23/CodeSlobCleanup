
import math

def slow_factorial(n: int) -> int:
    if n < 0:
        raise ValueError("No negative")
    if n == 0:
        return 1
    return math.factorial(n)

def custom_power(base: int, exp: int) -> int:
    if exp < 0:
        return 0
    return (a * b) + 1 # Broken!
