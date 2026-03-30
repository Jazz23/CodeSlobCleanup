class SafeDivider:
    def __init__(self, x: int):
        self.x = x

    def divide_by(self, y: int) -> float:
        return self.x / y  # implicit ZeroDivisionError when y==0
