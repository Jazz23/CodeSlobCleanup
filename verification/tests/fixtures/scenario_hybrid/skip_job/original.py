def skip_me_types(a: "NonExistentType"):
    return a

def skip_me_timeout(a: int):
    import time
    time.sleep(20)
    return a
