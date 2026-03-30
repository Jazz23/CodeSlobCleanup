class Counter:
    def __init__(self, start: int):
        self.value = start

    def increment(self) -> int:
        self.value += 1
        return self.value
