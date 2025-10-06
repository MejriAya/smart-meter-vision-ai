import serial
import serial.tools.list_ports
import socket
import json
import time

def led_q_on():
    """
    Fonction unique pour :
    - Vérifier la présence du port COM3
    - Envoyer une commande série
    - Envoyer le résultat à l'interface Qt via TCP (sans gestion d'erreur sur le socket)
    """

    # Configuration du port série
    COM_PORT = "COM3"
    BAUD_RATE = 19200
    COMMAND = b"MS 1 1 4F7B\r"

    # Étape 1 : Vérification du port COM3
    available_ports = [port.device for port in serial.tools.list_ports.comports()]
    if COM_PORT not in available_ports:
        message = {"status": "FAIL", "message": f"{COM_PORT} introuvable"}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 9000))
        s.sendall(json.dumps(message).encode('utf-8'))
        s.close()
        return f"Erreur : Le port {COM_PORT} n'est pas connecté ou introuvable."

    # Étape 2 : Connexion au port COM3
    conn = serial.Serial(
        port=COM_PORT,
        baudrate=BAUD_RATE,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=2
    )
    conn.write(COMMAND)
    time.sleep(0.5)
    response = conn.read_all().decode().strip()
    conn.close()

    # Étape 3 : Analyse de la réponse
    if "OK" in response or not response:
        status = "PASS"
        msg = " LED Q ON réussie"
    else:
        status = "FAIL"
        msg = f"Réponse inattendue: {response}"

    # Étape 4 : Envoi TCP vers l'interface Qt
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 9000))
    s.sendall(json.dumps({"status": status, "message": msg}).encode())
    s.close()

    return f"{status} > {msg}"