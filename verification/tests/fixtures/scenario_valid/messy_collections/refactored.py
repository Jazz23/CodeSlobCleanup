from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter

def process_items(items: List[Dict[str, int]]) -> Dict[str, int]:
    """
    Aggregates scores by category.
    Refactored: Using defaultdict and cleaner logic.
    """
    if not items:
        return {}
        
    result = defaultdict(int)
    
    for item in items:
        if item is None:
            continue
            
        cat = str(item.get("category", "unknown"))
        
        try:
            score = int(item.get("score", 0))
        except (ValueError, TypeError):
            score = 0
            
        result[cat] += score
        
    return dict(result)

def find_duplicates(numbers: List[int]) -> List[int]:
    """
    Finds numbers that appear more than once.
    Refactored: O(N) using Counter.
    """
    if not numbers:
        return []
        
    counts = Counter(numbers)
    dupes = [num for num, count in counts.items() if count > 1]
    dupes.sort()
    return dupes
