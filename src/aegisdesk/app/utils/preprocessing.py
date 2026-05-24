import re

EMOJI_MAP = {
    "🙏": "please",
    "😅": "sorry",
    "😂": "funny",
    "👍": "acknowledged",
    "🔥": "important",
    "🤷": "confused",
    "🥺": "urgent"
}

def clean_text(txt: str) -> str:
    if not txt:
        return ""

    res = txt
    
    for k, v in EMOJI_MAP.items():
        res = res.replace(k, f" {v} ")
        
    res = res.lower()
    res = re.sub(r'([!?.])\1+', r'\1', res)
    res = re.sub(r'\s+', ' ', res).strip()
    
    return res