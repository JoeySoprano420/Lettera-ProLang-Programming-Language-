def entangle_correction(block_node):
    """Correct Above/Below mismatches via canonicalization."""
    eq, above, below = block_node.children
    if above.value[1] != below.value[1]:
        # canonicalize to Below
        corrected = below.value[1]
        above.value = (above.value[0], corrected)
    return block_node
