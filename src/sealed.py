import hashlib
import subprocess
import os
import tempfile
import platform
import shutil

def create_seal(ast_json, ir_code):
    """
    Create a SHA-256 seal from the serialized AST and LLVM IR code.
    """
    data = ast_json.encode() + ir_code.encode()
    return hashlib.sha256(data).hexdigest()

def find_objcopy():
    """
    Try to locate a working objcopy tool: prefer llvm-objcopy, fallback to GNU objcopy.
    """
    if shutil.which("llvm-objcopy"):
        return "llvm-objcopy"
    elif shutil.which("objcopy"):
        return "objcopy"
    else:
        return None

def inject_seal(obj_file, seal, section_name=".lettera_seal"):
    """
    Embed the seal into a custom section of the object file using objcopy.

    Supported platforms:
    - ✅ Linux (Ubuntu, Kali): ELF format
    - ✅ Windows (MinGW or WSL): PE format
    - ⚠️ macOS: Mach-O format is not supported for custom sections

    Automatically selects between llvm-objcopy and GNU objcopy.
    """
    current_os = platform.system()
    if current_os == "Darwin":
        print("Seal injection is not supported on macOS (Mach-O binaries).")
        return False

    objcopy_tool = find_objcopy()
    if not objcopy_tool:
        print("No objcopy tool found. Please install llvm-objcopy or GNU objcopy.")
        return False

    try:
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".seal") as temp:
            temp.write(seal)
            seal_file = temp.name

        cmd = [
            objcopy_tool,
            f"--add-section={section_name}={seal_file}",
            f"--set-section-flags={section_name}=noload,readonly",
            obj_file
        ]

        subprocess.check_call(cmd)
        print(f"[Lettera] Seal injected into {obj_file} using {objcopy_tool} → section {section_name}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[Lettera] Seal injection failed: {e}")
        return False

    finally:
        if 'seal_file' in locals() and os.path.exists(seal_file):
            os.remove(seal_file)
