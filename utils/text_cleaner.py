import re

def normalize_text(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()
