class Calculator:
    def __init__(self, x: int):
        self.x = x

    def double(self) -> int:
        return self.x * 3  # wrong: should be * 2
