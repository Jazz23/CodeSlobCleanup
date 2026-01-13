def validate_transaction(t):
    """Refactored: Flattened with guard clauses."""
    if not t or "id" not in t:
        return False
    
    if t.get("amount", 0) <= 0:
        return False
        
    if t.get("status") != "pending":
        return False
        
    return len(t["id"]) > 8
