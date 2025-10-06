import os
import cv2
import numpy as np
import imagingcontrol4 as ic4
from datetime import datetime
from ultralytics import YOLO
import socket
import json

# === Chemin du modèle ONNX pour LCDs ===
MODEL_PATH = r"C:\Users\aya mejri\OneDrive\Bureau\stage pfe sagemcom\A\LCD\best-LCD.onnx"

# === Paramètres globaux par défaut ===
CAMERA_SERIAL = "22610286"
OUTPUT_FOLDER = r"C:\Users\aya mejri\OneDrive\Bureau\stage pfe sagemcom\A\LCD\captures"
CONFIDENCE_THRESHOLD = 0.5
TIMEOUT = 2  # en secondes

# Charger le modèle YOLOv8 une seule fois
model = YOLO(MODEL_PATH)

def send_tcp_message(ip="localhost", port=9000, image_path=None, status="PASS", message=""):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        data = json.dumps({
            "image_path": image_path,
            "status": status,
            "message": message,
            "test_completed": True
        })
        client_socket.sendall(data.encode())
        client_socket.close()
        print(f"[TCP] Message envoyé: {data}")
    except Exception as e:
        print(f"[ERREUR TCP] Impossible d'envoyer le message: {str(e)}")

def run_teststand_action(camera_serial=CAMERA_SERIAL,
                         output_folder=OUTPUT_FOLDER,
                         timeout=TIMEOUT,
                         conf_threshold=CONFIDENCE_THRESHOLD):

    serial = str(camera_serial).strip(' "\'')
    folder = os.path.normpath(str(output_folder).strip(' "\''))
    timeout_clean = max(1, min(float(timeout), 30))
    conf_clean = max(0.1, min(float(conf_threshold), 1.0))

    # === Initialisation de la bibliothèque ic4 ===
    #if not ic4.Library.is_initialized():
    #    ic4.Library.init()

    # Recherche caméra
    devices = ic4.DeviceEnum.devices()
    device = next((d for d in devices if str(d.serial) == serial), None)
    #if not device:
    #    ic4.Library.exit()
    #    return f"ERREUR: Caméra {serial} introuvable"

    grabber = ic4.Grabber()
    grabber.device_open(device)
    sink = ic4.SnapSink()
    grabber.stream_setup(sink)

    buffer = sink.snap_single(int(timeout_clean * 1000))
    if not buffer:
        grabber.stream_stop()
        grabber.device_close()
        ic4.Library.exit()
        return "ERREUR: Timeout de capture"

    # === Traitement de l'image ===
    img_np = buffer.numpy_wrap()

    if len(img_np.shape) < 3:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
    else:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    img_np = cv2.fastNlMeansDenoisingColored(img_np, None, 10, 10, 7, 21)
    lab = cv2.cvtColor(img_np, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    img_np = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # === Inférence YOLOv8 ===
    results = model.predict(source=img_np, conf=conf_clean)
    result = results[0]
    annotated_img = result.plot()

    # === Sauvegarde uniquement de l'image annotée ===
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    annotated_filename = os.path.join(folder, f"annotated_{timestamp}.png")
    if not cv2.imwrite(annotated_filename, annotated_img):
        grabber.stream_stop()
        grabber.device_close()
        ic4.Library.exit()
        return "ERREUR: Échec sauvegarde image annotée"

    # Résumé des résultats
    count = len(result.boxes)
    detected_classes = [result.names[int(box.cls)] for box in result.boxes]
    confidences = [float(box.conf) for box in result.boxes]

    print(f"\n LCD détectés : {count}")
    for cls, conf in zip(detected_classes, confidences):
        print(f"   - Classe: {cls} | Confiance: {conf:.2f}")

    # === Logique finale : choisir le meilleur composant détecté ou aucun ===
    if count == 0:
        result_message = "LCD non détecté"
        tcp_status = "FAIL"
    elif count == 1:
        result_message = f"{detected_classes[0]} détecté"
        tcp_status = "PASS"
    else:
        class_conf_pairs = list(zip(detected_classes, confidences))
        best_class, best_conf = max(class_conf_pairs, key=lambda x: x[1])

        if best_conf >= 0.5:
            result_message = f"{best_class} détecté"
            tcp_status = "PASS"
        else:
            result_message = "Aucun composant LCD clairement détecté"
            tcp_status = "FAIL"

    print(f"\n Résultat final : {result_message}")

    # === Envoi TCP ===
    send_tcp_message(
        ip="localhost",
        port=9000,
        image_path=annotated_filename,
        status=tcp_status,
        message=result_message
    )

    # Nettoyage caméra
    grabber.stream_stop()
    grabber.device_close()

    # Réinitialiser ic4 si nécessaire
    ic4.Library.exit()

    return result_message