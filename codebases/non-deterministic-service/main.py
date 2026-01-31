import random
import time

def process_data_list(items):
    """
    Sloppy function that processes a list.
    Slob: Verbose, redundant checks, manual indexing.
    """
    if items is None:
        return []
    
    result = []
    i = 0
    while i < len(items):
        item = items[i]
        if item is not None:
            # Redundant logic
            val = item * 2
            result.append(val)
        i += 1
    return result

def generate_session_token(user_id):
    """
    Sloppy non-deterministic function.
    Slob: Manual string building, uses random.
    Should be SKIPPED during verification.
    """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    token = ""
    # Verbose random string generation
    for _ in range(10):
        idx = random.randint(0, len(chars) - 1)
        token = token + chars[idx]
    
    final_token = f"{user_id}-{token}"
    return final_token

def calculate_heavy_score(n):
    """
    Sloppy and potentially slow function.
    Slob: Inefficient recursion.
    Might TIMEOUT if n is large, leading to a SKIP.
    """
    if n <= 0: return 0
    if n == 1: return 1
    return calculate_heavy_score(n - 1) + calculate_heavy_score(n - 2)

if __name__ == "__main__":
    print(process_data_list([1, 2, 3]))
    print(generate_session_token("user123"))
