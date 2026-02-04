class PrivateMethodClass:
    def public_api(self, x: int) -> int:
        return self._private_calc(x) + 10

    def _private_calc(self, x: int) -> int:
        # This is different, but if auto-passed, it shouldn't cause a failure for this specific method's verification
        return x * 3

def _top_level_private(x: int) -> int:
    # If this is also auto-passed, it won't fail
    return x + 2

def public_func(x: int) -> int:
    # This WILL fail because it uses _top_level_private which changed, 
    # unless we fix the logic in public_func to match original behavior.
    # Actually, let's keep it failing to see what happens.
    return (x + 1) * 2
