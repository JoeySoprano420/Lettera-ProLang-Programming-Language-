class Node:
    def __init__(self, kind, value=None, children=None):
        self.kind = kind
        self.value = value
        self.children = children or []

    def __repr__(self):
        return f"Node({self.kind}, {self.value}, {self.children})"
