import time

def process_order(order, inventory):
    # Refactored: boolean logic grouping
    if not (order.is_valid() and inventory.check_stock(order.item_id)):
        return 0.0
    return inventory.get_price(order.item_id) * order.quantity

def timeout_loop(x: int):
    time.sleep(60)
    return x

