from orders import calculate_total, apply_discount, process_payment

def test_order_flow():
    cart = [
        {'name': 'Laptop', 'price': 1000, 'quantity': 1},
        {'name': 'Mouse', 'price': 25, 'quantity': 2}
    ]
    
    total = calculate_total(cart)
    assert total == 1050
    
    discounted = apply_discount(total, "SUMMER20")
    assert discounted == 840
    
    success = process_payment(discounted, "credit_card")
    assert success is True

if __name__ == "__main__":
    test_order_flow()
    print("Golden test passed!")
