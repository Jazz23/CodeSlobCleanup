def parse(x: int) -> str:
    if x < 0:
        raise ValueError("negative")
    return str(x)
