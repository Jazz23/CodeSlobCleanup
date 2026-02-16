# /// script
# dependencies = ["numpy"]
# ///
import utils
import inventory

def main():
    print("Starting application...")
    
    # Test utils
    print("Fib 10:", utils.calculate_fibonacci(10))
    
    raw_names = ["  alice ", "BOB", "   ", "charlie"]
    clean_names = utils.format_names(raw_names)
    print("Clean names:", clean_names)
    
    nums = [10, 5, 20, 2, 8]
    print("Max:", utils.get_max_value(nums))

    # Test inventory
    inventory.add_item("Apple", 1.0, 100)
    inventory.add_item("Banana", 0.5, 150)
    inventory.add_item("Apple", 1.0, 50) # Duplicate name intention
    
    print("Total Value:", inventory.calculate_total_value())
    
    dupes = inventory.find_duplicates()
    print("Duplicates:", dupes)
    
    orders = [
        {"id": 1, "items": ["Apple", "Banana"]},
        {"id": 2, "items": ["Apple", "Orange"]} # Orange doesn't exist
    ]
    
    inventory.process_orders(orders)
    print("Finished.")

if __name__ == "__main__":
    main()
