"""Helper functions — functional clones of utils with renamed variables."""


# Functional clone of utils.calculate_discount (different var names, same logic)
def apply_discount(cost, percentage):
    if percentage < 0:
        return cost
    discount = cost * percentage
    return cost - discount


# Functional clone of utils.validate_email
def check_email(address):
    if not address:
        return False
    if "@" not in address:
        return False
    parts = address.split("@")
    if len(parts) != 2:
        return False
    return len(parts[1]) > 0


# Functional clone of utils.clamp
def bound(val, lo, hi):
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val


def unique_function_b():
    """Only appears once — should not be flagged."""
    data = {}
    for key in ["a", "b", "c"]:
        data[key] = key.upper()
    return data
