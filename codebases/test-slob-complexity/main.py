import nested_logic

def main():
    print("Running Complexity Tests...")
    
    # Test deeply_nested_function
    data = [
        {
            "active": True,
            "items": [
                {"id": "A1", "priority": 10, "tags": ["urgent-task"], "status": "pending"},
                {"id": "A2", "priority": 2, "retry": True},
                {"id": "A3", "priority": 10, "type": "internal"}
            ]
        },
        {
            "active": False
        }
    ]
    results = nested_logic.deeply_nested_function(data)
    print("Nested Function Result:", results)
    
    # Test redundant_checks
    val = nested_logic.redundant_checks(1, 1, 1)
    print("Redundant Checks Result:", val)
    
    print("Complexity Tests Finished.")

if __name__ == "__main__":
    main()
