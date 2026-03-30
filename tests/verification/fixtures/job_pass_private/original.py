def _helper(x):
    return x * 2


def public_func(x: int) -> int:
    return _helper(x)
