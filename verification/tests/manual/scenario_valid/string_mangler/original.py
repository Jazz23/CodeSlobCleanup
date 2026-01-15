
def to_slug(text: str) -> str:
    # Slob: manual replacement hell
    if not text:
        return ""
        
    res = text.lower()
    # Manual list of replacements
    res = res.replace(" ", "-")
    res = res.replace("_", "-")
    res = res.replace(".", "")
    res = res.replace(",", "")
    res = res.replace("!", "")
    res = res.replace("?", "")
    res = res.replace("'", "")
    
    # Remove double dashes
    while "--" in res:
        res = res.replace("--", "-")
        
    # Strip dashes
    if res.startswith("-"):
        res = res[1:]
    if res.endswith("-"):
        res = res[:-1]
        
    return res

def parse_kv(item: str) -> dict:
    # Slob: manual string parsing "k=v;k2=v2"
    if not item:
        return {}
    
    parts = item.split(";")
    out = {}
    for p in parts:
        if "=" in p:
            # finds first =
            idx = p.find("=")
            k = p[:idx]
            v = p[idx+1:]
            
            # random stripping
            k = k.strip()
            v = v.strip()
            
            if k:
                out[k] = v
    return out
