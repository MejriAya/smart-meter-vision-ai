from pymodbus.client import ModbusTcpClient
import socket
import json

# Configuration
MOXA_IP = '192.168.0.101'
MODBUS_PORT = 502
UNIT_ID = 1
DI_ADDRESS = 0

def check_presence():
    """
    Vérifie la détection de présence via Modbus.
    Retourne un string (message) et envoie le statut à l'interface Qt.
    """
    client = ModbusTcpClient(MOXA_IP, port=MODBUS_PORT)

    # Connexion au serveur MOXA
    if not client.connect():
        message = {"status": "FAIL", "message": "Erreur: Capteur Présence"}
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 9000))
            s.sendall(json.dumps(message).encode('utf-8'))
        client.close()
        return "Erreur: Connexion MOXA"

    # Lecture des entrées discrètes
    result = client.read_discrete_inputs(DI_ADDRESS, count=1, slave=UNIT_ID)

    # Fermeture connexion
    client.close()

    # Gestion des erreurs Modbus
    if result.isError():
        error_msg = f"Erreur Modbus: E{result.exception_code}"
        message = {"status": "FAIL", "message": error_msg}
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 9000))
            s.sendall(json.dumps(message).encode('utf-8'))
        return error_msg

    # Détection de présence
    presence = result.bits[0]
    if presence:
        msg = "Compteur Présent "
        status = "PASS"
    else:
        msg = "Aucune présence"
        status = "FAIL"

    # Envoi du statut à l'interface Qt
    message = {"status": status, "message": msg}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', 9000))
        s.sendall(json.dumps(message).encode('utf-8'))

    return msg