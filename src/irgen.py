def generate_ir(ast):
    fmt = "@fmt = constant [13 x i8] c\"Hello, World\\0A\\00\"\n"
    ir = [
        "; Lettera LLVM IR",
        "declare i32 @printf(i8*, ...)",
        fmt,
        "define i32 @main() {",
        "  call i32 (i8*, ...) @printf(i8* getelementptr ([13 x i8], [13 x i8]* @fmt, i32 0, i32 0))",
        "  ret i32 0",
        "}"
    ]
    return "\n".join(ir)
