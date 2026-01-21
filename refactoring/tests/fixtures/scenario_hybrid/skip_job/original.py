class UnfuzzableType:
    def __init__(self):
        raise RuntimeError("Cannot be instantiated")

def skip_me_types(a: UnfuzzableType):
    return a
