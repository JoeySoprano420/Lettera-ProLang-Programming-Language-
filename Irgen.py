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
