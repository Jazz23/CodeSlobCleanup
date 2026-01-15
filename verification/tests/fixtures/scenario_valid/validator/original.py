def validate_transaction(t):
    # Slob: "Arrow code" (deep nesting)
    if t is not None and isinstance(t, dict):
        if "id" in t:
            if t["amount"] > 0:
                if t["status"] == "pending":
                    if len(t["id"]) > 8:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False
