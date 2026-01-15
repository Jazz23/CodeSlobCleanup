def process_user_data(data):
    # This is a "Slob" function: too many responsibilities, poor naming, and redundant logic
    results = []
    for item in data:
        if item is not None:
            # Cleanup
            name = item.get("name", "Unknown").strip().upper()
            age = item.get("age", 0)
            if age < 0: age = 0
            
            # Math
            score = item.get("score", 0)
            bonus = 0
            if score > 90:
                bonus = 10
            elif score > 80:
                bonus = 5
            
            final_score = score + bonus
            
            # Formatting
            entry = f"User: {name}, Age: {age}, Score: {final_score}"
            print(f"Processing {name}...") # Slob: logging inside logic
            results.append(entry)
    
    return results
