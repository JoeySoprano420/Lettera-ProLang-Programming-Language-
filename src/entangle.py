import socket

def send_above(node_addr, code):
    s = socket.socket()
    host, port = node_addr.split(":")
    s.connect((host, int(port)))
    s.sendall(code.encode())
    s.close()

def recv_below(port=5555):
    s = socket.socket()
    s.bind(('0.0.0.0', port))
    s.listen(1)
    conn, _ = s.accept()
    data = conn.recv(4096).decode()
    conn.close()
    return data
