
import re

def to_slug(text: str) -> str:
    if not text:
        return ""
        
    # Lowercase
    text = text.lower()
    
    # Replace separators with hyphens - ONLY space and underscore as per original slob
    text = re.sub(r'[ _]+', '-', text)
    
    # Remove unwanted chars (keep alphanumeric and hyphens)
    # The original removed specific punctuation. To be exact:
    # .,!?' are removed. Others are kept? 
    # The original slob code only removed specific chars.
    # To pass verification, we must match EXACTLY.
    # Original: replace . , ! ? ' with empty.
    for char in [".", ",", "!", "?", "'"]:
        text = text.replace(char, "")
        
    # Remove double dashes (re handles this if we used it for replacement, but we did separate steps)
    # The original loop `while "--" in res` reduces "---" to "-" eventually.
    # re.sub('-+', '-') does it in one go.
    text = re.sub(r'-+', '-', text)
    
    # Strip
    text = text.strip('-')
    
    return text

def parse_kv(item: str) -> dict:
    if not item:
        return {}
    
    # Using dictionary comprehension but matching logic
    # Original split by ";" then find first "="
    parts = [p for p in item.split(";") if "=" in p]
    out = {}
    for p in parts:
        k, v = p.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k:
            out[k] = v
    return out
