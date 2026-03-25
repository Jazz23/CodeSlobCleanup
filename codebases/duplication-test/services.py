"""Service layer — copy-pastes utility logic instead of importing it."""


# Exact copy of utils.calculate_discount
def calculate_discount(price, rate):
    if rate < 0:
        return price
    discount = price * rate
    return price - discount


# Exact copy of utils.format_currency
def format_currency(amount, symbol):
    rounded = round(amount, 2)
    return f"{symbol}{rounded:.2f}"


# Another functional clone of validate_email with slightly different var names
def is_valid_email(value):
    if not value:
        return False
    if "@" not in value:
        return False
    parts = value.split("@")
    if len(parts) != 2:
        return False
    return len(parts[1]) > 0


def process_order(items, discount_rate):
    """Unique business logic — should not be flagged."""
    total = sum(item["price"] for item in items)
    discounted = calculate_discount(total, discount_rate)
    return {"total": total, "discounted": discounted}
