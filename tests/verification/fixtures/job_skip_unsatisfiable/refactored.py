class Opaque:
    pass


def process(obj):
    if not isinstance(obj, Opaque):
        raise TypeError("Must be Opaque")
    return True
