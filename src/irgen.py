from llvmlite import ir

# Symbol table for variables
class SymbolTable:
    def __init__(self, builder):
        self.vars = {}
        self.builder = builder

    def declare(self, name, value):
        ptr = self.builder.alloca(value.type, name=name)
        self.builder.store(value, ptr)
        self.vars[name] = ptr

    def load(self, name):
        return self.builder.load(self.vars[name], name=name)

def generate_ir(ast):
    module = ir.Module(name="lettera_module")

    # printf declaration
    voidptr_ty = ir.IntType(8).as_pointer()
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")

    # main function
    func_ty = ir.FunctionType(ir.IntType(32), [])
    main_fn = ir.Function(module, func_ty, name="main")
    block = main_fn.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    symbols = SymbolTable(builder)

    # Traverse AST: handle Equations
    for node in ast.children:
        if node.kind == "Block":
            eq = node.children[0]  # Equation
            above = node.children[1]
            below = node.children[2]

            lhs, rhs = eq.value
            # Support numbers (base-12 → int) and strings
            if rhs.isdigit() or all(c in "0123456789ab" for c in rhs):
                val = int(rhs, 12)  # base-12 conversion
                llvm_val = ir.Constant(ir.IntType(32), val)
            else:
                # treat as string literal
                rhs_val = rhs.strip('"') + "\0"
                str_ty = ir.ArrayType(ir.IntType(8), len(rhs_val))
                global_str = ir.GlobalVariable(module, str_ty, name=f"{lhs}_str")
                global_str.global_constant = True
                global_str.initializer = ir.Constant(str_ty, bytearray(rhs_val.encode()))
                llvm_val = global_str

            symbols.declare(lhs, llvm_val if isinstance(llvm_val, ir.Constant) else llvm_val)

            # Handle Above + Below Print statements
            for section in [above, below]:
                if section.value[0].lower() == "print":
                    msg = section.value[1].strip('"')
                    if msg in symbols.vars:
                        ptr = symbols.load(msg)
                        builder.call(printf, [ptr])
                    else:
                        # print raw literal
                        fmt_str = msg + "\n\0"
                        arr_ty = ir.ArrayType(ir.IntType(8), len(fmt_str))
                        global_fmt = ir.GlobalVariable(module, arr_ty, name=f"str_{lhs}")
                        global_fmt.global_constant = True
                        global_fmt.initializer = ir.Constant(arr_ty, bytearray(fmt_str.encode()))
                        fmt_ptr = builder.gep(global_fmt, [ir.IntType(32)(0), ir.IntType(32)(0)])
                        builder.call(printf, [fmt_ptr])

    # Return 0
    builder.ret(ir.IntType(32)(0))
    return str(module)

def handle_djcmd(cmd, args, builder, module, printf):
    if cmd == "BPM":
        bpm_val = int(args[0], 12) if args[0].isdigit() else int(args[0])
        return ir.Constant(ir.IntType(32), bpm_val)

    if cmd == "Key":
        key_str = args[0].strip('"') + "\0"
        arr_ty = ir.ArrayType(ir.IntType(8), len(key_str))
        gv = ir.GlobalVariable(module, arr_ty, name="key_str")
        gv.global_constant = True
        gv.initializer = ir.Constant(arr_ty, bytearray(key_str.encode()))
        return gv

    if cmd == "Energy":
        return ir.Constant(ir.IntType(32), int(args[0]))

    if cmd == "Crossfade":
        dur, typ = args
        msg = f"Crossfade {dur} {typ}\n\0"
        arr_ty = ir.ArrayType(ir.IntType(8), len(msg))
        gv = ir.GlobalVariable(module, arr_ty, name="crossfade_msg")
        gv.global_constant = True
        gv.initializer = ir.Constant(arr_ty, bytearray(msg.encode()))
        return gv

    if cmd == "Filter":
        typ, sweep = args
        msg = f"Filter {typ} sweep {sweep}\n\0"
        arr_ty = ir.ArrayType(ir.IntType(8), len(msg))
        gv = ir.GlobalVariable(module, arr_ty, name="filter_msg")
        gv.global_constant = True
        gv.initializer = ir.Constant(arr_ty, bytearray(msg.encode()))
        return gv

    return None

from llvmlite import ir

def declare_dj_runtime(module):
    i32 = ir.IntType(32)
    i8ptr = ir.IntType(8).as_pointer()

    funcs = {
        "dj_bpm": ir.FunctionType(ir.VoidType(), [i32]),
        "dj_key": ir.FunctionType(ir.VoidType(), [i8ptr]),
        "dj_energy": ir.FunctionType(ir.VoidType(), [i32]),
        "dj_genre": ir.FunctionType(ir.VoidType(), [i8ptr]),
        "dj_crossfade": ir.FunctionType(ir.VoidType(), [i32, i8ptr]),
        "dj_filter": ir.FunctionType(ir.VoidType(), [i8ptr, i8ptr]),
        "dj_loop": ir.FunctionType(ir.VoidType(), [i32, i32]),
        "dj_drop": ir.FunctionType(ir.VoidType(), [i8ptr, i32]),
        "dj_playlist": ir.FunctionType(ir.VoidType(), [i8ptr]),
        "dj_order": ir.FunctionType(ir.VoidType(), [i8ptr, i8ptr, i8ptr]),
        "dj_record": ir.FunctionType(ir.VoidType(), [i8ptr]),
        "dj_seal": ir.FunctionType(ir.VoidType(), [i8ptr]),
        "dj_log": ir.FunctionType(ir.VoidType(), [i8ptr]),
    }
    return {name: ir.Function(module, ftype, name=name) for name, ftype in funcs.items()}

def str_constant(module, builder, name, s):
    s += "\0"
    arr_ty = ir.ArrayType(ir.IntType(8), len(s))
    gv = ir.GlobalVariable(module, arr_ty, name=name)
    gv.global_constant = True
    gv.initializer = ir.Constant(arr_ty, bytearray(s.encode()))
    return builder.gep(gv, [ir.IntType(32)(0), ir.IntType(32)(0)])

def handle_dj_command(cmd, args, builder, module, dj_funcs):
    if cmd == "BPM":
        builder.call(dj_funcs["dj_bpm"], [ir.Constant(ir.IntType(32), int(args[0]))])
    elif cmd == "Key":
        ptr = str_constant(module, builder, "keystr", args[0].strip('"'))
        builder.call(dj_funcs["dj_key"], [ptr])
    elif cmd == "Energy":
        builder.call(dj_funcs["dj_energy"], [ir.Constant(ir.IntType(32), int(args[0]))])
    elif cmd == "Genre":
        ptr = str_constant(module, builder, "genrestr", args[0].strip('"'))
        builder.call(dj_funcs["dj_genre"], [ptr])
    elif cmd == "Crossfade":
        duration = int(args[0].replace("s", ""))
        ptr = str_constant(module, builder, "cftype", args[1].strip('"'))
        builder.call(dj_funcs["dj_crossfade"], [ir.Constant(ir.IntType(32), duration), ptr])
    elif cmd == "Filter":
        tptr = str_constant(module, builder, "ftype", args[0].strip('"'))
        sptr = str_constant(module, builder, "fsweep", args[1].strip('"'))
        builder.call(dj_funcs["dj_filter"], [tptr, sptr])
    elif cmd == "Loop":
        length, count = map(int, args)
        builder.call(dj_funcs["dj_loop"], [ir.Constant(ir.IntType(32), length),
                                           ir.Constant(ir.IntType(32), count)])
    elif cmd == "Drop":
        ptr = str_constant(module, builder, "dropeffect", args[0].strip('"'))
        builder.call(dj_funcs["dj_drop"], [ptr, ir.Constant(ir.IntType(32), int(args[1]))])
    elif cmd == "Playlist":
        ptr = str_constant(module, builder, "plname", args[0].strip('"'))
        builder.call(dj_funcs["dj_playlist"], [ptr])
    elif cmd == "Order":
        a, b, method = args
        aptr = str_constant(module, builder, "ordera", a.strip('"'))
        bptr = str_constant(module, builder, "orderb", b.strip('"'))
        mptr = str_constant(module, builder, "orderm", method.strip('"'))
        builder.call(dj_funcs["dj_order"], [aptr, bptr, mptr])
    elif cmd == "RecordSet":
        ptr = str_constant(module, builder, "recfile", args[0].strip('"'))
        builder.call(dj_funcs["dj_record"], [ptr])
    elif cmd == "SealSet":
        ptr = str_constant(module, builder, "sealhash", args[0].strip('"'))
        builder.call(dj_funcs["dj_seal"], [ptr])
    elif cmd == "Log":
        ptr = str_constant(module, builder, "logevt", args[0].strip('"'))
        builder.call(dj_funcs["dj_log"], [ptr])

def handle_dj_audio(cmd, args, builder, module, dj_funcs):
    if cmd == "Play":
        ptr = str_constant(module, builder, "playfile", args[0].strip('"'))
        builder.call(dj_funcs["dj_play"], [ptr])
    elif cmd == "Crossfade":
        a = str_constant(module, builder, "filea", args[0].strip('"'))
        b = str_constant(module, builder, "fileb", args[1].strip('"'))
        duration = ir.Constant(ir.IntType(32), int(args[2].replace("s","")))
        builder.call(dj_funcs["dj_crossfade"], [a, b, duration])

