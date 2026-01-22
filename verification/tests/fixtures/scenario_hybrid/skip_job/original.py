class UnfuzzableType:
    def __init__(self):
        raise RuntimeError("Cannot be instantiated")

def skip_me_types(a: UnfuzzableType):
    return a

def skip_me_timeout(a: int):
    import time
    time.sleep(20)
    return a
