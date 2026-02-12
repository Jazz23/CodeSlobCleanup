import processor

def main():
    print("Running Clean Tests...")
    
    items = [
        {"name": "Item 1", "price": 10.0, "quantity": 2, "active": True},
        {"name": "Item 2", "price": 5.0, "quantity": 10, "active": True},
        {"name": "Item 3", "price": 20.0, "quantity": 1, "active": False}
    ]
    
    total = processor.process_data(items)
    print("Total Processed Value:", total)
    
    active_items = processor.get_active_items(items)
    print("Active Items Count:", len(active_items))
    
    print("Clean Tests Finished.")

if __name__ == "__main__":
    main()
