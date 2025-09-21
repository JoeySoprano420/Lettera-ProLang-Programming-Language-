from llvmlite import ir

def generate_ir(ast):
    # Create an LLVM module
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

    # Walk AST to find Above/Below values
    msg = None
    for node in ast.children:
        if node.kind == "Block":
            above = [c for c in node.children if c.kind == "Above"][0]
            msg = above.value[1].strip('"')
            break

    if msg is None:
        msg = "Hello, World"

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

    # Return 0
    builder.ret(ir.IntType(32)(0))

    return str(module)
