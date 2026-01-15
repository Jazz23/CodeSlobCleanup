
def slow_factorial(n: int) -> int:
    # Slob: Recursive with no error checking for large inputs,
    # bad variable names, print statements (that we can't easily check but indicate slob)
    # and unnecessary steps.
    if n < 0:
        raise ValueError("No negative")
    if n == 0:
        return 1
    
    res = 1
    # Unnecessary list creation
    nums = []
    for i in range(1, n + 1):
        nums.append(i)
        
    for x in nums:
        # Inefficient multiplication loop
        temp = 0
        for _ in range(x):
            temp += res
        res = temp
        
    return res

def custom_power(base: int, exp: int) -> int:
    # Slob: repetitive multiplication
    if exp < 0:
        # Just return 0 for negative exponent to be weird
        return 0
    
    res = 1
    count = 0
    while count < exp:
        res = res * base
        count = count + 1
    return res
