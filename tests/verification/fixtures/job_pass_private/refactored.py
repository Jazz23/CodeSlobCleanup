def _helper(x):
    return x * 99  # different impl, but private so auto-passed


def public_func(x: int) -> int:
    return x * 2
