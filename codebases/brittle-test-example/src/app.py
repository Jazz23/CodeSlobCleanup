_LOG = []

def format_user_list(users):
    """
    Slob: This function is messy, uses a global list for logging, 
    and has unnecessary string concatenations in a loop.
    """
    res = ""
    # Unnecessary global side effect that a clean refactor might remove
    global _LOG
    for u in users:
        msg = f"Processing user: {u.get('name', 'Unknown')}"
        _LOG.append(msg)
        
        # Inefficient string concatenation
        if 'name' in u:
            res = res + u['name'].upper() + ", "
        else:
            res = res + "UNKNOWN" + ", "
            
    # Messy way to remove the trailing comma
    if len(res) > 0:
        if res.endswith(", "):
            res = res[:-2]
            
    return res

def calculate_stats(numbers):
    """
    Slob: Unnecessarily complex logic for simple averaging.
    """
    if not numbers:
        return 0
    
    total = 0
    count = 0
    for n in numbers:
        # Deeply nested and redundant checks
        if n is not None:
            if isinstance(n, (int, float)):
                total += n
                count += 1
    
    if count == 0:
        return 0
    
    avg = total / count
    return avg
