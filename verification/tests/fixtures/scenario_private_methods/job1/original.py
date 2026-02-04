class PrivateMethodClass:
    def public_api(self, x: int) -> int:
        return self._private_calc(x) + 10

    def _private_calc(self, x: int) -> int:
        return x * 2

def _top_level_private(x: int) -> int:
    return x + 1

def public_func(x: int) -> int:
    return _top_level_private(x) * 2
