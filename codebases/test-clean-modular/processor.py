from math_utils import add, multiply

def process_data(items):
    """
    Clean, modular processing logic.
    """
    total = 0
    for item in items:
        price = item.get("price", 0)
        qty = item.get("quantity", 0)
        line_total = multiply(price, qty)
        total = add(total, line_total)
    return total

def get_active_items(items):
    return [i for i in items if i.get("active")]
