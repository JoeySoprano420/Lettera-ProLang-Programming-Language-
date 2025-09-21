import sys
import json
from lexer import tokenize
from parser import Parser
from ail import entangle_correction
from sealed import create_seal
from llvmlite import ir, binding as llvm

def serialize_ast(node):
    """Recursively serialize AST nodes to handle nested structures."""
    if isinstance(node, list):
        return [serialize_ast(n) for n in node]
    elif hasattr(node, '__dict__'):
        return {k: serialize_ast(v) for k, v in node.__dict__.items()}
    else:
        return node

def generate_ir(ast):
    module = ir.Module(name="lettera_module")

    # Declare printf
    voidptr_ty = ir.IntType(8).as_pointer()
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")

    # Define main function
    func_ty = ir.FunctionType(ir.IntType(32), [])
    main_fn = ir.Function(module, func_ty, name="main")
    block = main_fn.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)

    # Extract message from AST
    msg = "Hello, World"
    for node in ast.children:
        if node.kind == "Block":
            above_nodes = [c for c in node.children if c.kind == "Above"]
            if above_nodes:
                msg = above_nodes[0].value[1].strip('"')
            break

    # Create global string
    fmt_str = msg + "\n\0"
    global_fmt = ir.GlobalVariable(module,
                                   ir.ArrayType(ir.IntType(8), len(fmt_str)),
                                   name="fmt")
    global_fmt.linkage = "internal"
    global_fmt.global_constant = True
    global_fmt.initializer = ir.Constant(
        ir.ArrayType(ir.IntType(8), len(fmt_str)),
        bytearray(fmt_str.encode("utf8"))
    )

    # Get pointer to string
    fmt_ptr = builder.gep(global_fmt, [ir.IntType(32)(0), ir.IntType(32)(0)])

    # Call printf
    builder.call(printf, [fmt_ptr])
    builder.ret(ir.IntType(32)(0))

    return str(module)

def main():
    if len(sys.argv) < 2:
        print("Usage: lettera <file.let> [output.ll]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.ll"

    try:
        with open(input_file, "r") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    try:
        tokens = tokenize(source)
        parser = Parser(tokens, starched_mode=True)
        ast = parser.parse()
    except Exception as e:
        print(f"Parsing error: {e}")
        sys.exit(1)

    # Apply correction
    block_nodes = [c for c in ast.children if c.kind == "Block"]
    if block_nodes:
        entangle_correction(block_nodes[0])

    # Generate IR
    ir_code = generate_ir(ast)

    # Create seal
    serialized_ast = json.dumps(serialize_ast(ast), indent=2)
    seal = create_seal(serialized_ast, ir_code)
    print(f"[Lettera] Seal embedded: {seal[:16]}...")

    # Write IR to file
    try:
        with open(output_file, "w") as f:
            f.write(ir_code)
        print(f"[Lettera] Compilation complete → {output_file}")
    except IOError as e:
        print(f"Error writing IR file: {e}")
        sys.exit(1)

    # Compile to bitcode
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    try:
        mod = llvm.parse_assembly(ir_code)
        with open("output.bc", "wb") as f:
            f.write(mod.as_bitcode())
        print("[Lettera] Compilation complete → output.bc")
        print("Use: llc output.bc -o output.s && clang output.s -o output.exe")
    except Exception as e:
        print(f"LLVM compilation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

import sys
import json
from lexer import tokenize
from parser import Parser
from ail import entangle_correction
from sealed import create_seal
from llvmlite import ir, binding as llvm

def serialize_ast(node):
    if isinstance(node, list):
        return [serialize_ast(n) for n in node]
    elif hasattr(node, '__dict__'):
        return {k: serialize_ast(v) for k, v in node.__dict__.items()}
    else:
        return node

def generate_ir(ast):
    module = ir.Module(name="lettera_module")

    voidptr_ty = ir.IntType(8).as_pointer()
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")

    func_ty = ir.FunctionType(ir.IntType(32), [])
    main_fn = ir.Function(module, func_ty, name="main")
    block = main_fn.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)

    msg = "Hello, World"
    for node in ast.children:
        if node.kind == "Block":
            above_nodes = [c for c in node.children if c.kind == "Above"]
            if above_nodes:
                msg = above_nodes[0].value[1].strip('"')
            break

    fmt_str = msg + "\n\0"
    global_fmt = ir.GlobalVariable(module,
                                   ir.ArrayType(ir.IntType(8), len(fmt_str)),
                                   name="fmt")
    global_fmt.linkage = "internal"
    global_fmt.global_constant = True
    global_fmt.initializer = ir.Constant(
        ir.ArrayType(ir.IntType(8), len(fmt_str)),
        bytearray(fmt_str.encode("utf8"))
    )

    fmt_ptr = builder.gep(global_fmt, [ir.IntType(32)(0), ir.IntType(32)(0)])
    builder.call(printf, [fmt_ptr])
    builder.ret(ir.IntType(32)(0))

    return str(module)

def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print("Usage: lettera <file.let> [output.ll] [--emit-ast] [--opt-level=N]")
        sys.exit(1)

    input_file = args[0]
    output_file = next((a for a in args if a.endswith(".ll")), "output.ll")
    emit_ast = "--emit-ast" in args
    opt_level = next((a.split("=")[1] for a in args if a.startswith("--opt-level=")), "0")

    try:
        with open(input_file, "r") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    try:
        tokens = tokenize(source)
        parser = Parser(tokens, starched_mode=True)
        ast = parser.parse()
    except Exception as e:
        print(f"Parsing error: {e}")
        sys.exit(1)

    block_nodes = [c for c in ast.children if c.kind == "Block"]
    if block_nodes:
        entangle_correction(block_nodes[0])

    if emit_ast:
        serialized_ast = json.dumps(serialize_ast(ast), indent=2)
        with open("ast.json", "w") as f:
            f.write(serialized_ast)
        print("[Lettera] AST emitted → ast.json")
        sys.exit(0)

    ir_code = generate_ir(ast)
    seal = create_seal(json.dumps(serialize_ast(ast)), ir_code)
    print(f"[Lettera] Seal embedded: {seal[:16]}...")

    try:
        with open(output_file, "w") as f:
            f.write(ir_code)
        print(f"[Lettera] Compilation complete → {output_file}")
    except IOError as e:
        print(f"Error writing IR file: {e}")
        sys.exit(1)

    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    try:
        mod = llvm.parse_assembly(ir_code)
        mod.verify()

        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine(opt=int(opt_level))
        with open("output.bc", "wb") as f:
            f.write(mod.as_bitcode())
        print(f"[Lettera] Bitcode emitted → output.bc (opt-level={opt_level})")
        print("Use: llc output.bc -o output.s && clang output.s -o output.exe")
    except Exception as e:
        print(f"LLVM compilation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

import sys
import json
from lexer import tokenize
from parser import Parser
from ail import entangle_correction
from sealed import create_seal
from llvmlite import ir, binding as llvm

def serialize_ast(node):
    if isinstance(node, list):
        return [serialize_ast(n) for n in node]
    elif hasattr(node, '__dict__'):
        return {k: serialize_ast(v) for k, v in node.__dict__.items()}
    else:
        return node

def generate_ir(ast):
    module = ir.Module(name="lettera_module")

    voidptr_ty = ir.IntType(8).as_pointer()
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")

    func_ty = ir.FunctionType(ir.IntType(32), [])
    main_fn = ir.Function(module, func_ty, name="main")
    block = main_fn.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)

    msg = "Hello, World"
    for node in ast.children:
        if node.kind == "Block":
            above_nodes = [c for c in node.children if c.kind == "Above"]
            if above_nodes:
                msg = above_nodes[0].value[1].strip('"')
            break

    fmt_str = msg + "\n\0"
    global_fmt = ir.GlobalVariable(module,
                                   ir.ArrayType(ir.IntType(8), len(fmt_str)),
                                   name="fmt")
    global_fmt.linkage = "internal"
    global_fmt.global_constant = True
    global_fmt.initializer = ir.Constant(
        ir.ArrayType(ir.IntType(8), len(fmt_str)),
        bytearray(fmt_str.encode("utf8"))
    )

    fmt_ptr = builder.gep(global_fmt, [ir.IntType(32)(0), ir.IntType(32)(0)])
    builder.call(printf, [fmt_ptr])
    builder.ret(ir.IntType(32)(0))

    return str(module)

def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print("Usage: lettera <file.let> [output.ll] [--emit-ast] [--opt-level=N]")
        sys.exit(1)

    input_file = args[0]
    output_file = next((a for a in args if a.endswith(".ll")), "output.ll")
    emit_ast = "--emit-ast" in args
    opt_level = next((a.split("=")[1] for a in args if a.startswith("--opt-level=")), "0")

    try:
        with open(input_file, "r") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    try:
        tokens = tokenize(source)
        parser = Parser(tokens, starched_mode=True)
        ast = parser.parse()
    except Exception as e:
        print(f"Parsing error: {e}")
        sys.exit(1)

    block_nodes = [c for c in ast.children if c.kind == "Block"]
    if block_nodes:
        entangle_correction(block_nodes[0])

    serialized_ast = json.dumps(serialize_ast(ast), indent=2)

    if emit_ast:
        with open("ast.json", "w") as f:
            f.write(serialized_ast)
        print("[Lettera] AST emitted → ast.json")
        sys.exit(0)

    ir_code = generate_ir(ast)
    seal = create_seal(serialized_ast, ir_code)
    print(f"[Lettera] Seal embedded: {seal[:16]}...")

    try:
        with open(output_file, "w") as f:
            f.write(ir_code)
        print(f"[Lettera] Compilation complete → {output_file}")
    except IOError as e:
        print(f"Error writing IR file: {e}")
        sys.exit(1)

    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    try:
        mod = llvm.parse_assembly(ir_code)
        mod.verify()

        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine(opt=int(opt_level))
        with open("output.bc", "wb") as f:
            f.write(mod.as_bitcode())
        print(f"[Lettera] Bitcode emitted → output.bc (opt-level={opt_level})")
        print("Use: llc output.bc -o output.s && clang output.s -o output.exe")
    except Exception as e:
        print(f"LLVM compilation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
