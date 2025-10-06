from pymodbus.client import ModbusTcpClient
import socket
import json

# Configuration Modbus
MOXA_IP = '192.168.0.101'
MODBUS_PORT = 502
UNIT_ID = 1
DO_ADDRESS = 5  # Adresse de la sortie digitale (DO5)

def activer_compteur():
    """
    Active la sortie DO5 pour allumer le compteur.
    Envoie un statut et un message à l'interface Qt via TCP.
    Retourne un string décrivant le résultat.
    """
    client = ModbusTcpClient(MOXA_IP, port=MODBUS_PORT)

    # Tentative de connexion au module MOXA
    if not client.connect():
        message = {"status": "FAIL", "message": "Erreur: Connexion impossible au module MOXA"}
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 9000))
            s.sendall(json.dumps(message).encode('utf-8'))
        client.close()
        return "ERREUR: Connexion impossible au module MOXA"

    # Activation de la sortie DO5
    result = client.write_coil(address=DO_ADDRESS, value=True, slave=UNIT_ID)

    # Fermeture de la connexion Modbus
    client.close()

    # Gestion des erreurs Modbus
    if result.isError():
        error_msg = f"Erreur Modbus: E{result.exception_code}"
        message = {"status": "FAIL", "message": error_msg}
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 9000))
            s.sendall(json.dumps(message).encode('utf-8'))
        return error_msg

    # Si succès
    msg = "Compteur allumé"
    status = "PASS"
    message = {"status": status, "message": msg}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', 9000))
        s.sendall(json.dumps(message).encode('utf-8'))

    return msg