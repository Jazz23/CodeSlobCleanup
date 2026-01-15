from typing import List

def extract_hashtags(text: str) -> List[str]:
    """
    Extracts hashtags from text.
    Slob: Manual character iteration.
    """
    if not text:
        return []
        
    tags = []
    current_tag = ""
    in_tag = False
    
    for char in text:
        if char == "#":
            if in_tag:
                # Previous tag ended
                if len(current_tag) > 0:
                    tags.append(current_tag)
                current_tag = ""
            in_tag = True
        elif in_tag:
            if char.isalnum() or char == "_":
                current_tag += char
            else:
                if len(current_tag) > 0:
                    tags.append(current_tag)
                current_tag = ""
                in_tag = False
                
    if in_tag and len(current_tag) > 0:
        tags.append(current_tag)
        
    return tags

def parse_kv_string(data: str) -> List[str]:
    """
    Parses 'key=value;key2=value2' string into list of keys.
    Slob: using find and string slicing loops.
    """
    if not data:
        return []
        
    keys = []
    remainder = data
    
    while True:
        eq_idx = -1
        # Manual find
        for i in range(len(remainder)):
            if remainder[i] == "=":
                eq_idx = i
                break
        
        if eq_idx == -1:
            break
            
        key = remainder[:eq_idx].strip()
        keys.append(key)
        
        semi_idx = -1
        for i in range(eq_idx + 1, len(remainder)):
            if remainder[i] == ";":
                semi_idx = i
                break
                
        if semi_idx == -1:
            break
            
        remainder = remainder[semi_idx+1:]
        
    return keys
