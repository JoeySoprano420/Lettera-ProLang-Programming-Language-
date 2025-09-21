import re

TOKENS = [
    ("MODULE", r"Module:"),
    ("ENTRY", r"Entry:"),
    ("BLOCK", r"Block:"),
    ("END", r"End:"),
    ("FUNC", r"Func"),
    ("EQUATION", r"Equation:"),
    ("ABOVE", r"Above:"),
    ("BELOW", r"Below:"),
    ("TARGET", r"Target:"),
    ("VERSION", r"Version:"),
    ("SUBJECT", r"Subject:"),
    ("ADDRESS", r"Address:"),
    ("RETURN", r"Return"),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("STRING", r"\".*?\""),
    ("NUMBER", r"[0-9ab]+"),   # base-12
    ("SYMBOL", r"[:;=()]"),
    ("NEWLINE", r"\n"),
    ("SPACE", r"[ \t]+"),
]

def tokenize(src: str):
    tokens = []
    i = 0
    while i < len(src):
        match = None
        for typ, regex in TOKENS:
            pattern = re.compile(regex)
            match = pattern.match(src, i)
            if match:
                text = match.group(0)
                if typ not in ("SPACE", "NEWLINE"):  # skip whitespace
                    tokens.append((typ, text))
                i = match.end(0)
                break
        if not match:
            raise SyntaxError(f"Unexpected char at {i}: {src[i]}")
    return tokens
