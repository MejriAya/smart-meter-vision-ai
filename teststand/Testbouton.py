import os
import cv2
import numpy as np
import onnxruntime as ort
from datetime import datetime
import socket
import json

# === Paramètres ===
MODEL_PATH = r"C:\Users\aya mejri\OneDrive\Bureau\stage pfe sagemcom\A\boutons\best-buttons.onnx"
IMAGE_PATH = r"C:\Users\aya mejri\CameraCaptures\BACKLIGHT_ON\BACKLIGHT_ON_2025-06-09_14-11-38_0003.png"
OUTPUT_FOLDER = r"C:\Users\aya mejri\OneDrive\Bureau\stage pfe sagemcom\A\boutons\captures_test"
TCP_IP = "localhost"
TCP_PORT = 9000

# === Envoi TCP ===
def send_tcp_message(ip="localhost", port=9000, image_path=None, count=0):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))
    message = json.dumps({
        "image_path": image_path,
        "status": "PASS" if count > 0 else "FAIL",
        "message": f" Bouton  détecté " if count > 0 else "Aucun bouton détecté",
        "test_completed": False
    })
    client_socket.sendall(message.encode())
    client_socket.close()

# === Traitement Image & Inférence ===
def process_image(image_path):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Lecture image existante
    img_np = cv2.imread(image_path)
    if img_np is None:
        return "ERREUR: Image non chargée"

    # Amélioration de la qualité
    img_np = cv2.fastNlMeansDenoisingColored(img_np, None, 10, 10, 7, 21)
    lab = cv2.cvtColor(img_np, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
    img_np = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    # Inférence
    img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (640, 640))
    img_input = img_resized.transpose(2, 0, 1).astype(np.float32)[None] / 255.0

    ort_session = ort.InferenceSession(MODEL_PATH)
    input_name = ort_session.get_inputs()[0].name
    outputs = ort_session.run(None, {input_name: img_input})

    # Post-processing YOLOv8
    output_array = outputs[0][0].transpose(1, 0)
    class_scores = np.zeros((output_array.shape[0], 1), dtype=output_array.dtype)
    output_array = np.hstack([output_array, class_scores])

    mask = output_array[:, 4] > 0.5
    valid_dets = output_array[mask]

    boxes = []
    scores = []
    H, W = img_rgb.shape[:2]

    for det in valid_dets:
        x_center, y_center, width, height, score, cls_id = det
        x1 = int((x_center - width / 2) * W / 640)
        y1 = int((y_center - height / 2) * H / 640)
        x2 = int((x_center + width / 2) * W / 640)
        y2 = int((y_center + height / 2) * H / 640)
        boxes.append([x1, y1, x2, y2])
        scores.append(score)

    # Suppression des doublons (NMS)
    final_boxes = []
    if len(boxes) > 0:
        boxes = np.array(boxes)
        pick = []
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(scores)

        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])
            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
            overlap = (w * h) / area[idxs[:last]]
            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > 0.5)[0])))

        final_boxes = [boxes[i] for i in pick]

    count = len(final_boxes)

    # Annoter l'image
    for box in final_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(img_np, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img_np, "Bouton", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    base_filename = os.path.basename(image_path)
    annotated_filename = os.path.join(OUTPUT_FOLDER, base_filename.replace(".png", "_annotated.png"))
    cv2.imwrite(annotated_filename, img_np)

    # Envoi TCP
    send_tcp_message(ip=TCP_IP, port=TCP_PORT, image_path=annotated_filename, count=count)

    return "Bouton détecté" if count > 0 else "Aucun bouton détecté"