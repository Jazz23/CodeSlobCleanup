def parse(x: int) -> str:
    if x < 0:
        raise TypeError("negative")  # wrong exception type
    return str(x)
