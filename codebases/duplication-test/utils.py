"""Utility functions for the application."""


def calculate_discount(price, rate):
    if rate < 0:
        return price
    discount = price * rate
    return price - discount


def validate_email(email):
    if not email:
        return False
    if "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    return len(parts[1]) > 0


def clamp(value, min_val, max_val):
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


def format_currency(amount, symbol):
    rounded = round(amount, 2)
    return f"{symbol}{rounded:.2f}"


def unique_function_a():
    """Only appears once — should not be flagged."""
    result = []
    for i in range(10):
        result.append(i * 2)
    return result
