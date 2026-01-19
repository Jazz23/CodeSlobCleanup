from typing import List, Dict, Any, Optional

def process_items(items: List[Dict[str, int]]) -> Dict[str, int]:
    """
    Aggregates scores by category.
    Slob: Manual iteration, redundant checks, explicit key handling.
    """
    result = {}
    if items is None:
        return {}
    
    for i in range(len(items)):
        item = items[i]
        if item is None:
            continue
            
        cat = item.get("category", "unknown")
        # Ensure category is a string key
        if not isinstance(cat, str):
            cat = str(cat)
            
        score = item.get("score", 0)
        if not isinstance(score, int):
            try:
                score = int(score)
            except:
                score = 0
                
        if cat in result:
            current = result[cat]
            result[cat] = current + score
        else:
            result[cat] = score
            
    return result

def find_duplicates(numbers: List[int]) -> List[int]:
    """
    Finds numbers that appear more than once.
    Slob: O(N^2) double loop.
    """
    if not numbers:
        return []
        
    dupes = []
    for i in range(len(numbers)):
        for j in range(len(numbers)):
            if i != j:
                if numbers[i] == numbers[j]:
                    # Check if we already added it
                    already_added = False
                    for k in range(len(dupes)):
                        if dupes[k] == numbers[i]:
                            already_added = True
                            break
                    if not already_added:
                        dupes.append(numbers[i])
    
    # Sort for deterministic output comparison
    dupes.sort()
    return dupes
