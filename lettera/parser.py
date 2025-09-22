from .ast import ASTNode

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def eat(self, kind=None):
        token = self.peek()
        if kind and token[0] != kind:
            raise RuntimeError(f"Expected {kind}, got {token}")
        self.pos += 1
        return token

    def parse(self):
        nodes = []
        while self.peek()[0]:
            if self.peek()[0] == "MODULE":
                nodes.append(self.parse_module())
            elif self.peek()[0] == "ENTRY":
                nodes.append(self.parse_entry())
            elif self.peek()[0] == "BLOCK":
                nodes.append(self.parse_block())
            elif self.peek()[0] == "END":
                nodes.append(self.parse_end())
            else:
                self.eat()  # skip unrecognized for now
        return ASTNode("Program", children=nodes)

    def parse_module(self):
        self.eat("MODULE")
        return ASTNode("Module")

    def parse_entry(self):
        self.eat("ENTRY")
        self.eat("FUNC")
        name = self.eat("IDENT")[1]
        return ASTNode("EntryFunc", value=name)

    def parse_block(self):
        self.eat("BLOCK")
        children = []
        while self.peek()[0] not in ("END", None):
            if self.peek()[0] == "EQUATION":
                self.eat("EQUATION")
                ident = self.eat("IDENT")[1]
                self.eat("IDENT")  # '='
                val = self.eat("IDENT")[1]
                children.append(ASTNode("Equation", value=(ident, val)))
            elif self.peek()[0] == "ABOVE":
                self.eat("ABOVE")
                msg = self.eat("STRING")[1]
                children.append(ASTNode("AbovePrint", value=msg))
            elif self.peek()[0] == "BELOW":
                self.eat("BELOW")
                msg = self.eat("STRING")[1]
                children.append(ASTNode("BelowPrint", value=msg))
            else:
                self.eat()
        return ASTNode("Block", children=children)

    def parse_end(self):
        self.eat("END")
        self.eat("RETURN")
        val = self.eat("NUMBER")[1]
        return ASTNode("Return", value=int(val))
