import hashlib, subprocess

def create_seal(ast_json, ir_code):
    data = ast_json.encode() + ir_code.encode()
    return hashlib.sha256(data).hexdigest()

def inject_seal(obj_file, seal, section_name=".lettera_seal"):
    """
    Embed the seal into a custom ELF/PE section.
    Requires 'objcopy' (GNU binutils).
    """
    seal_file = obj_file + ".seal"
    with open(seal_file, "w") as f:
        f.write(seal)

    cmd = [
        "objcopy",
        f"--add-section", f"{section_name}={seal_file}",
        "--set-section-flags", f"{section_name}=noload,readonly",
        obj_file
    ]
    subprocess.check_call(cmd)
    return True
