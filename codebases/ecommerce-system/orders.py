def calculate_total(items):
    """Calculates the total price of items in the cart."""
    return sum(item['price'] * item['quantity'] for item in items)

def apply_discount(total, discount_code):
    """Applies a discount code to the total."""
    if discount_code == "SUMMER20":
        return total * 0.8
    elif discount_code == "WELCOME5":
        return total - 5
    return total

def process_payment(total, payment_method):
    """Simulates processing a payment."""
    print(f"Processing {payment_method} payment for ${total:.2f}")
    return True

def legacy_tax_calculator_v1(total):
    """DEPRECATED: Old tax calculation logic from 2018."""
    return total * 1.05

def send_old_fax_confirmation(order_id):
    """DEPRECATED: We no longer send faxes."""
    print(f"Sending fax for order {order_id}...")
    return False

def calculate_shipping_v1(weight):
    """DEPRECATED: Replaced by dynamic carrier API."""
    return weight * 2.5

def format_order_for_printing(order):
    """Helper for internal debugging, rarely used."""
    return f"Order: {order['id']}, Total: {order['total']}"