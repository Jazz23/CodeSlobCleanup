from typing import List
import re

def extract_hashtags(text: str) -> List[str]:
    """
    Extracts hashtags from text.
    Refactored: Using regex.
    """
    if not text:
        return []
        
    # Matches # followed by word characters
    return re.findall(r'#(\w+)', text)

def parse_kv_string(data: str) -> List[str]:
    """
    Parses 'key=value;key2=value2' string into list of keys.
    Refactored: Using split.
    """
    if not data:
        return []
        
    keys = []
    pairs = data.split(';')
    for pair in pairs:
        if '=' in pair:
            key, _ = pair.split('=', 1)
            keys.append(key.strip())
            
    return keys
