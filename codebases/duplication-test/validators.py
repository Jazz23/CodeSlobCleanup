"""Validators — more clones of the clamp and discount patterns."""


# Functional clone of utils.clamp / helpers.bound
def restrict(number, minimum, maximum):
    if number < minimum:
        return minimum
    if number > maximum:
        return maximum
    return number


# Functional clone of utils.calculate_discount / helpers.apply_discount
def compute_discount(base_price, discount_rate):
    if discount_rate < 0:
        return base_price
    discount = base_price * discount_rate
    return base_price - discount


def unique_function_c():
    """Only appears once — should not be flagged."""
    total = 0
    for n in range(1, 6):
        total += n ** 2
    return total
