def deeply_nested_function(data):
    """
    Deliberately complex function with high cyclomatic complexity (CC).
    """
    result = []
    if data:
        for category in data:
            if category.get("active"):
                for item in category.get("items", []):
                    if item.get("priority") > 5:
                        if "tags" in item:
                            for tag in item["tags"]:
                                if tag.startswith("urgent"):
                                    if item.get("status") == "pending":
                                        result.append(item["id"])
                                    elif item.get("status") == "failed":
                                        print(f"Alert: {item['id']} failed")
                                    else:
                                        result.append(f"LOG: {item['id']}")
                        else:
                            if item.get("type") == "internal":
                                result.append(item["id"])
                    else:
                        if item.get("retry"):
                            result.append(item["id"])
            else:
                print("Category inactive")
    return result

def redundant_checks(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            if z > 0:
                return x + z
            else:
                return x
    else:
        if y > 0:
            if z > 0:
                return y + z
            else:
                return y
        else:
            if z > 0:
                return z
            else:
                return 0
