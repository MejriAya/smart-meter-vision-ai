import os
import cv2
import numpy as np
import onnxruntime as ort
import imagingcontrol4 as ic4
from datetime import datetime
import socket
import json

# Chemin du modèle ONNX
MODEL_PATH = r"C:\Users\aya mejri\OneDrive\Bureau\stage pfe sagemcom\A\boutons\best-buttons.onnx"

# Variables globales
ic4_initialized = False
ort_session = None

def send_tcp_message(ip="localhost", port=9000, image_path=None, count=0):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))
    message = json.dumps({
        "image_path": image_path,
        "status": "PASS",
        "message": f" Bouton détecté ",
        "test_completed": True
    })
    client_socket.sendall(message.encode())
    client_socket.close()

def run_teststand_action(camera_serial="22610286",
                         output_folder=r"C:\Users\aya mejri\OneDrive\Bureau\stage pfe sagemcom\A\boutons\captures",
                         timeout=2):
    global ic4_initialized, ort_session

    serial = str(camera_serial).strip(' "\'')
    folder = os.path.normpath(str(output_folder).strip(' "\''))
    timeout_clean = max(1, min(float(timeout), 30))

    if not ic4_initialized:
        ic4.Library.init()
        ic4_initialized = True

    devices = ic4.DeviceEnum.devices()
    device = next((d for d in devices if str(d.serial) == serial), None)
    if not device:
        return f"ERREUR: Caméra {serial} introuvable"

    grabber = ic4.Grabber()
    grabber.device_open(device)
    sink = ic4.SnapSink()
    grabber.stream_setup(sink)

    buffer = sink.snap_single(int(timeout_clean * 1000))
    if not buffer:
        grabber.stream_stop()
        grabber.device_close()
        return "ERREUR: Timeout de capture"

    img_np = buffer.numpy_wrap()

    if len(img_np.shape) < 3:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
    else:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Amélioration qualité
    img_np = cv2.fastNlMeansDenoisingColored(img_np, None, 10, 10, 7, 21)
    lab = cv2.cvtColor(img_np, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    img_np = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
    cv2.imwrite(filename, img_np)

    # Préparation pour inférence
    img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (640, 640))
    img_input = img_resized.transpose(2, 0, 1).astype(np.float32)[None] / 255.0

    if ort_session is None:
        ort_session = ort.InferenceSession(MODEL_PATH)

    input_name = ort_session.get_inputs()[0].name
    outputs = ort_session.run(None, {input_name: img_input})

    # Post-traitement YOLOv8
    output_array = outputs[0][0].transpose(1, 0)  # shape: (8400, 5)
    class_scores = np.zeros((output_array.shape[0], 1), dtype=output_array.dtype)
    output_array = np.hstack([output_array, class_scores])  # shape: (8400, 6)

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

    final_boxes = []
    if len(boxes) > 0:
        boxes = np.array(boxes)
        pick = []

        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]

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

    # Dessiner les boîtes sur l'image
    for box in final_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(img_np, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img_np, "Bouton", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    annotated_filename = filename.replace(".png", "_annotated.png")
    cv2.imwrite(annotated_filename, img_np)

    # Envoi TCP
    send_tcp_message(image_path=annotated_filename, count=count)

    # === Message personnalisé selon la détection ===
    if count > 0:
        result_message = "Bouton détecté"
    else:
        result_message = "Bouton non détecté"

    # Nettoyage
    grabber.stream_stop()
    grabber.device_close()

    return result_message