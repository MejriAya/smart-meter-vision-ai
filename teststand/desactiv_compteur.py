from pymodbus.client import ModbusTcpClient

# Configuration Modbus
MOXA_IP = '192.168.0.101'
PORT = 502
UNIT_ID = 1
DO_ADDRESS = 5  # Adresse de la sortie digitale (DO5)

def desactiver_compteur():
    # Initialisation client Modbus
    client = ModbusTcpClient(host=MOXA_IP, port=PORT)
    
    # Tentative de connexion
    if not client.connect():
        return "ERREUR: Connexion impossible au module MOXA"
    
    # Commande de désactivation
    result = client.write_coil(address=DO_ADDRESS, value=False, slave=UNIT_ID)
    
    # Retour du résultat
    if result.isError():
        return "ERREUR: Échec de la désactivation de la sortie DO5"
    else:
        return "SUCCÈS: Sortie DO5 désactivée"