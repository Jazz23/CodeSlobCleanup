import time

def process_order(order, inventory):
    # Slob: Implicit interface usage (Duck Typing)
    if order.is_valid() and inventory.check_stock(order.item_id):
        price = inventory.get_price(order.item_id)
        return price * order.quantity
    return 0.0

def timeout_loop(x: int):
    # This should trigger the 30s timeout
    time.sleep(60)
    return x

