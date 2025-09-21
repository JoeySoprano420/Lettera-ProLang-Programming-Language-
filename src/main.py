import sys, json
from lexer import tokenize
from parser import Parser
from ail import entangle_correction
from irgen import generate_ir
from sealed import create_seal

def main():
    if len(sys.argv) < 2:
        print("Usage: lettera <file.let>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        source = f.read()

    tokens = tokenize(source)
    parser = Parser(tokens, starched_mode=True)
    ast = parser.parse()

    # Apply correction
    block = [c for c in ast.children if c.kind=="Block"][0]
    entangle_correction(block)

    # Generate IR
    ir_code = generate_ir(ast)

    # Sealed envelope
    seal = create_seal(json.dumps(ast.__dict__, default=str), ir_code)
    print(f"[Lettera] Seal embedded: {seal[:16]}...")

    with open("output.ll", "w") as f:
        f.write(ir_code)

    print("[Lettera] Compilation complete → output.ll")

if __name__ == "__main__":
    main()
