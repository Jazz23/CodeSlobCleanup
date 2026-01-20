def _clean_user_info(item):
    name = item.get("name", "Unknown").strip().upper()
    age = max(item.get("age", 0), 0)
    return name, age

def _calculate_bonus(score):
    if score > 90: return 10
    if score > 80: return 5
    return 0

def process_user_data(data):
    """Refactored: Cleaned, decomposed, and removed side effects."""
    results = []
    for item in (i for i in data if i is not None):
        name, age = _clean_user_info(item)
        score = item.get("score", 0)
        final_score = score + _calculate_bonus(score)
        results.append(f"User: {name}, Age: {age}, Score: {final_score}")
    return results
