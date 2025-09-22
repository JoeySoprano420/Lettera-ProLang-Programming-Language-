DJ_KEYWORDS = {"BPM", "Key", "Energy", "Crossfade", "Filter"}

# inside parse_block:
rhs_tokens = []
while self.peek()[0] not in ("ABOVE", "BELOW"):
    tok = self.eat()[1]
    if tok in DJ_KEYWORDS:
        rhs_tokens.append(("DJCMD", tok))
    else:
        rhs_tokens.append(("TOK", tok))
