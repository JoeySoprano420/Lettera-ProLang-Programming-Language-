from ast import Node

class Parser:
    def __init__(self, tokens, starched_mode=True):
        self.tokens = tokens
        self.i = 0
        self.starched = starched_mode

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else (None, None)

    def eat(self, typ=None):
        tok = self.peek()
        if typ and tok[0] != typ:
            raise SyntaxError(f"Expected {typ}, got {tok}")
        self.i += 1
        return tok

    def parse(self):
        module = self.parse_module()
        entry = self.parse_entry()
        block = self.parse_block()
        end = self.parse_end()
        return Node("Program", children=[module, entry, block, end])

    def parse_module(self):
        self.eat("MODULE")
        return Node("Module", children=self.collect_metadata())

    def collect_metadata(self):
        nodes = []
        while self.peek()[0] in ("TARGET","VERSION","SUBJECT","ADDRESS"):
            key, val = self.eat()
            if self.starched and not self.peek()[1].endswith(";"):
                raise SyntaxError("Missing semicolon in Starched Paper Mode")
            nodes.append(Node(key, val))
            self.eat("SYMBOL")  # consume ;
        return nodes

    def parse_entry(self):
        self.eat("ENTRY")
        self.eat("FUNC")
        name = self.eat("IDENT")[1]
        self.eat("SYMBOL")  # (
        self.eat("SYMBOL")  # )
        self.eat("SYMBOL")  # :
        if self.starched: self.eat("SYMBOL")  # ;
        return Node("Entry", value=name)

    def parse_block(self):
        self.eat("BLOCK")
        self.eat("EQUATION")
        eq_left = self.eat("IDENT")[1]
        self.eat("SYMBOL")
        eq_right = self.eat("IDENT")[1]
        eq = Node("Equation", value=(eq_left, eq_right))

        self.eat("ABOVE")
        above_stmt = self.eat("IDENT")[1], self.eat("STRING")[1]

        self.eat("BELOW")
        below_stmt = self.eat("IDENT")[1], self.eat("STRING")[1]

        return Node("Block", children=[eq,
                Node("Above", value=above_stmt),
                Node("Below", value=below_stmt)])

    def parse_end(self):
        self.eat("END")
        self.eat("RETURN")
        code = self.eat("NUMBER")[1]
        if self.starched: self.eat("SYMBOL")
        return Node("End", value=code)

DJ_KEYWORDS = {"BPM", "Key", "Energy", "Crossfade", "Filter"}

# inside parse_block:
rhs_tokens = []
while self.peek()[0] not in ("ABOVE", "BELOW"):
    tok = self.eat()[1]
    if tok in DJ_KEYWORDS:
        rhs_tokens.append(("DJCMD", tok))
    else:
        rhs_tokens.append(("TOK", tok))
