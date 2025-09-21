import hashlib

def create_seal(ast_json, ir_code):
    data = ast_json.encode() + ir_code.encode()
    return hashlib.sha256(data).hexdigest()

def verify_seal(seal, ast_json, ir_code):
    return seal == create_seal(ast_json, ir_code)
