def import_address(node):
    for child in node.children:
        if child.kind == "ADDRESS":
            return child.value
    return None
