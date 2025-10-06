from pymodbus.client import ModbusTcpClient
import socket
import json

def Cnx_Moxa():
    # Connexion Modbus
    client = ModbusTcpClient('192.168.0.101', port=502)
    is_connected = client.connect()
    
    # Envoi statut à Qt
    gui_socket = socket.socket()
    gui_socket.connect(('localhost', 9000))
    gui_socket.sendall(json.dumps({
        "status": "PASS" if is_connected else "FAIL",
        "message": "" 
    }).encode())
    gui_socket.close()

       
    return is_connected