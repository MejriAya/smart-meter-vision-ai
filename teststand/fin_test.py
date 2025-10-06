import socket
import json

def fin_test():
    message = {
        "status": "PASS",
        "test_completed": True
    }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", 9000))
        s.sendall(json.dumps(message).encode())

    # Retour simple pour TestStand
    return "PASS"





