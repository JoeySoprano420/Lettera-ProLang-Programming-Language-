import sys
from lexer import tokenize
from parser import parse
from ail import entangle_correction
from irgen import generate_ir
from sealed import create_seal

def main():
    with open(sys.argv[1]) as f:
        source = f.read()

    tokens = tokenize(source)
    ast = parse(tokens)
    corrected_ast = entangle_correction(ast)
    ir_code = generate_ir(corrected_ast)

    # Seal creation
    seal = create_seal(str(ast), ir_code)
    print(f"[Lettera] Seal embedded: {seal[:16]}...")

    with open("output.ll", "w") as f:
        f.write(ir_code)

    print("[Lettera] Compilation complete → output.ll")

if __name__ == "__main__":
    main()
