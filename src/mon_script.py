import sys
import json
import socket
import random
import os
import time
import serial
import serial.tools.list_ports
from threading import Thread
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QGridLayout,
    QVBoxLayout, QHBoxLayout, QFrame, QGroupBox
)
from PySide6.QtGui import QPixmap, QFont, QIcon
from PySide6.QtCore import QThread, Qt, Signal, QObject, QTimer
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QApplication, QWidget

PRIMARY_COLOR = "#2785AB"

# === Signaux serveur TCP ===
class ServerSignals(QObject):
    message_received = Signal(dict)


# === Serveur TCP ===
class TcpServer:
    def __init__(self):
        self.led_p_delay = 5000
        self.is_led_sequence_running = False
        self.signals = ServerSignals()
        self.server_thread = None
        self.running = False

    def start_server(self, port=9000):
        self.running = True
        self.server_thread = Thread(target=self._run_server, args=(port,), daemon=True)
        self.server_thread.start()
        print(f"[QT] Serveur TCP démarré sur port {port}")

    def _run_server(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            s.settimeout(1.0)
            s.listen(5)
            while self.running:
                try:
                    conn, addr = s.accept()
                    print(f"[QT] Connexion entrante de {addr}")
                    data = conn.recv(4096).decode().strip()
                    if data:
                        print(f"[QT] Données reçues: {data}")
                        try:
                            message = json.loads(data)
                            self.signals.message_received.emit(message)
                        except json.JSONDecodeError as e:
                            print(f"Erreur décodage JSON: {e}")
                    conn.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Erreur serveur: {e}")
                finally:
                    if 'conn' in locals():
                        conn.close()

    def stop_server(self):
        self.running = False
        if self.server_thread:
            self.server_thread.join()
        print("[QT] Serveur TCP arrêté")



class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(" Compteur électrique ")
        self.setFixedSize(850, 500)
        self.setWindowIcon(QIcon(r""))
        self.setStyleSheet("font-family: 'Segoe UI';")
        self.init_ui()
        self.center_window()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Zone bleue à gauche
        left_frame = QFrame()
        left_frame.setFixedWidth(370)
        left_frame.setStyleSheet(f"""
            background-color: {PRIMARY_COLOR};
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
        """)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setAlignment(Qt.AlignCenter)
        left_layout.setContentsMargins(20, 20, 20, 20)

        logo_label = QLabel()
        pixmap = QPixmap(r"C:\Users\aya mejri\Downloads\fotor-2025063004255.png")
        logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setFixedSize(250, 250)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("""
            background-color: white;
            border-radius: 100px;
            padding: 10px;
            margin-bottom: 20px;
        """)
        left_layout.addWidget(logo_label)

        welcome = QLabel("Poste Vision")
        welcome.setFont(QFont("Segoe UI", 18, QFont.Bold))
        welcome.setStyleSheet("color: white; margin-top: 10px;")
        welcome.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(welcome)

        # Zone blanche à droite
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            background-color: white;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.setContentsMargins(60, 40, 60, 40)

        title = QLabel("Automatisation Process")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(f"color: {PRIMARY_COLOR}; margin-bottom: 30px;")
        title.setAlignment(Qt.AlignCenter)

        right_layout.addWidget(title)

        self.username_input = self.create_input("Nom d'utilisateur", "ex: Typedecompteur")
        self.password_input = self.create_input("Mot de passe", "••••••••", password=True)

        login_button = QPushButton("Se connecter")
        login_button.setFixedHeight(45)
        login_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: white;
                font-size: 16px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1b6e91;
            }}
        """)
        login_button.clicked.connect(self.check_credentials)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red; font-size: 13px; margin-top: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)

        right_layout.addWidget(self.username_input["label"])
        right_layout.addWidget(self.username_input["edit"])
        right_layout.addWidget(self.password_input["label"])
        right_layout.addWidget(self.password_input["edit"])
        right_layout.addSpacing(10)
        right_layout.addWidget(login_button)
        right_layout.addWidget(self.status_label)

        # Final assembly
        main_layout.addWidget(left_frame)
        main_layout.addWidget(right_frame)

    def create_input(self, label_text, placeholder, password=False):
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 6px;
                background-color: #f1f3f5;
                margin-bottom: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #2785AB;
                background-color: white;
            }
            """)
        if password:
            edit.setEchoMode(QLineEdit.Password)
        return {"label": label, "edit": edit}

    def check_credentials(self):
        username = self.username_input["edit"].text()
        password = self.password_input["edit"].text()
        if username == "" and password == "":
            self.accept_login()
        else:
            self.status_label.setText("Identifiants incorrects.")

    def accept_login(self):
        self.close()
        # Ouvre la fenêtre principale
        self.main_window = MainWindow()
        self.main_window.show()



# === Fenêtre principale avec affichage d'images ===
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TEST PAR VISION")
        self.setWindowIcon(QIcon(""))   # dans __init__()
        self.test_running = False
        self.tcp_server = TcpServer()
        self.teststand_process = None
        self.process_check_timer = QTimer(self)
        self.is_led_sequence_running = False
        self.pending_presence_data = None
        self.pending_result_data = None
        self.current_image_path = None
        self.image_history = []
        self.current_image_index = -1
        self.result_history = []
        # Nouvelle variable pour sauvegarder la dernière commande exécutée
        self.last_executed_component = None
        self.tcp_message_received = False  # Flag ajouté ici

        # Mapping des commandes vers les noms courts utilisables
        self.WHITELISTED_COMPONENTS = {
            "LEDPON": "P_ON",
            "LEDPOFF": "P_OFF",
            "LEDQON": "Q_ON",
            "LEDQOFF": "Q_OFF",
            "BacklightON": "LCD_BLACKLIGHT_ON",
            "BacklightOFF": "LCD_BLACKLIGHT_OFF",
            "LCDBlack": "LCD_BLACK",
            "LCDClear": "LCD_CLEAR",
            "LCDRestart": "LCD_RESTART"
        }

        self.setup_ui()
        self.setup_styles()
        self.init_ui()
        self.setup_communication()
        self.setMinimumSize(1000, 700)
        self.adjustSize()

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

    def setup_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #f0f2f5; font-family: 'Segoe UI'; }
            QPushButton {
                background-color: #4a6fa5; color: white; border: none;
                border-radius: 5px; padding: 8px 12px; font-size: 13px;
                min-height: 35px; margin: 3px;
            }
            QPushButton:hover { background-color: #3a5a80; }
            QPushButton:pressed { background-color: #2a4a70; }
            QPushButton#stop_button {
                background-color: #e74c3c; border: 2px solid #b71c1c;
            }
            QPushButton#stop_button:pressed {
                background-color: #c0392b; border: 2px solid #7f1c1c;
            }
            QPushButton#start_button {
                background-color: #27ae60; border: 2px solid #277e46; color: white;
            }
            QPushButton#start_button:hover { background-color: #1e8449; }
            QPushButton#start_button:pressed {
                background-color: #164d2a; border: 2px solid #0f341f;
            }
            QLabel { font-size: 13px; }
            QGroupBox {
                background-color: white; border-radius: 8px; border: 1px solid #d1d5db;
                margin-top: 15px; font-weight: bold; color: #3a7bf7;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            .status-label {
                font-size: 13px; padding: 8px; border-radius: 5px;
                font-weight: bold; min-width: 80px; text-align: center;
            }
            .status-pass { background-color: #e8f5e9; color: #27ae60; border: 1px solid #a5d6a7; }
            .status-fail { background-color: #ffebee; color: #e74c3c; border: 1px solid #ef9a9a; }
            .status-wait { background-color: #fff3e0; color: #f39c12; border: 1px solid #ffe0b2; }
            .image-container { border: 2px solid #e0e0e0; border-radius: 6px; background-color: #f9f9f9; }
            QPushButton.command-button-active { background-color: #3a5a80; border: 2px solid #2a4a70; }
            QFrame.command-frame-active {
                border: 2px solid #4a6fa5; border-radius: 5px; background-color: #e7eff9;
            }
            QFrame#header_frame {
                background-color: white; border-radius: 8px; border: 1px solid #d0d0d0; padding: 5px;
            }
            QLabel#camera_label {
                background-color: #2c3e50; color: white; font-size: 18px;
                font-weight: bold; border-radius: 8px;
            }
            QPushButton.nav-button {
                background-color: #3498db;
                min-width: 40px;
                min-height: 30px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton.nav-button:hover { background-color: #2980b9; }
            QPushButton.nav-button:disabled { background-color: #95a5a6; }
        """)

    def init_ui(self):
        self.create_header()
        self.create_main_content()
        self.test_steps = {
            "Cnx_Moxa": {"label": self.presence_label, "on_fail": [self.result_label]},
            "Verification_Presence": {"label": self.presence_label},
            "Capture_Image": {"label": self.result_label}
        }

    def setup_communication(self):
        self.tcp_server.start_server()
        self.tcp_server.signals.message_received.connect(self.handle_server_message)
        self.process_check_timer.timeout.connect(self.check_process_status)

    def create_header(self):
        header_frame = QFrame()
        header_frame.setObjectName("header_frame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Partie Logo (70%)
        self.logo_label = QLabel()
        try:
            pixmap = QPixmap(r"C:\Users\aya mejri\Downloads\.png").scaledToHeight(130, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        except:
            self.logo_label.setText("LOGO")
        self.logo_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.logo_label, stretch=70)

        # Titre + Horloge (30%)
        title_container = QVBoxLayout()
        title_container.setSpacing(0)
        self.title_label = QLabel("TEST PAR VISION")
        self.title_label.setFont(QFont("Arial Black", 18, QFont.Black))
        self.title_label.setStyleSheet("color: #4a6fa5; margin-bottom: 2px;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.clock_label = QLabel()
        self.clock_label.setFont(QFont("Arial", 10))
        self.clock_label.setStyleSheet("color: #6c7a89; margin-top: -5px;")
        self.clock_label.setAlignment(Qt.AlignCenter)
        title_container.addWidget(self.title_label)
        title_container.addWidget(self.clock_label)
        header_layout.addLayout(title_container, stretch=30)

        # Configuration du timer pour l'horloge
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()
        self.main_layout.addWidget(header_frame)

    def update_clock(self):
        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%d/%m/%Y")
        self.clock_label.setText(f"{current_time} - {current_date}")

    def create_main_content(self):
        content_frame = QFrame()
        content_layout = QHBoxLayout(content_frame)
        control_frame = QFrame()
        control_layout = QGridLayout(control_frame)
        self.create_test_control(control_layout)
        self.create_presence_section(control_layout)
        self.create_commands_section(control_layout)
        self.create_results_section(control_layout)
        content_layout.addWidget(control_frame, 40)
        self.create_camera_section(content_layout)
        self.main_layout.addWidget(content_frame)

    def create_test_control(self, layout):
        group = QGroupBox("CONTROLE TEST")
        vbox = QVBoxLayout()
        img_label = QLabel()
        try:
            pixmap = QPixmap(r"C:\Users\aya mejri\Downloads\images.png").scaled(150, 150, Qt.KeepAspectRatio)
            img_label.setPixmap(pixmap)
        except:
            img_label.setText("📷")
        img_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(img_label)
        hbox = QHBoxLayout()
        self.start_btn = QPushButton("DÉMARRER TEST")
        self.start_btn.setObjectName("start_button")
        self.stop_btn = QPushButton("ARRÊTER TEST")
        self.stop_btn.setObjectName("stop_button")
        self.start_btn.clicked.connect(self.start_test)
        self.stop_btn.clicked.connect(self.stop_test)
        hbox.addWidget(self.start_btn)
        hbox.addWidget(self.stop_btn)
        vbox.addLayout(hbox)
        group.setLayout(vbox)
        layout.addWidget(group, 0, 0)

    def create_presence_section(self, layout):
        group = QGroupBox("DÉTECTION PRÉSENCE")
        vbox = QVBoxLayout()
        img_label = QLabel()
        try:
            pixmap = QPixmap(r"C:\Users\aya mejri\Downloads\Capteur-de-mouvement-sans-fil-industriel-ALTA-300x300.jpg").scaled(150, 150)
            img_label.setPixmap(pixmap)
        except:
            img_label.setText("📷")
        img_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(img_label)
        self.presence_btn = QPushButton("VÉRIFIER PRÉSENCE")
        self.presence_btn.setStyleSheet("background-color: #4a6fa5;")
        self.presence_btn.clicked.connect(self.check_presence)
        vbox.addWidget(self.presence_btn)
        self.presence_label = QLabel("WAIT ...")
        self.presence_label.setProperty("class", "status-wait")
        vbox.addWidget(self.presence_label)
        group.setLayout(vbox)
        layout.addWidget(group, 0, 1)

    def create_commands_section(self, layout):
        group = QGroupBox("COMMANDES")
        vbox = QVBoxLayout()
        img_label = QLabel()
        try:
            pixmap = QPixmap(r"C:\Users\aya mejri\Downloads\images (1).jpg").scaled(150, 150)
            img_label.setPixmap(pixmap)
        except:
            img_label.setText("📷")
        img_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(img_label)
        group1 = [
            ("LED P ON", self.led_p_on, "LEDPON"),
            ("LED P OFF", self.led_p_off, "LEDPOFF"),
            ("LED Q ON", self.led_q_on, "LEDQON"),
            ("LED Q OFF", self.led_q_off, "LEDQOFF"),
        ]
        group2 = [
            ("Backlight ON", self.backlight_on, "BacklightON"),
            ("Backlight OFF", self.backlight_off, "BacklightOFF"),
        ]
        group3 = [
            ("LCD Black", self.lcd_black_screen, "LCDBlack"),
            ("LCD Clear", self.lcd_clear_screen, "LCDClear"),
            ("LCD Restart", self.lcd_restart, "LCDRestart"),
        ]
        vbox.addLayout(self.create_command_group(group1))
        vbox.addLayout(self.create_command_group(group2))
        vbox.addLayout(self.create_command_group(group3))
        group.setLayout(vbox)
        layout.addWidget(group, 1, 0)

    def create_command_group(self, commands):
        hbox = QHBoxLayout()
        for btn_text, func, btn_name in commands:
            btn = QPushButton(btn_text)
            btn.setObjectName(btn_name)
            btn.setFont(QFont("Segoe UI", 9))
            btn.setStyleSheet("""
                background-color: #4a6fa5;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 4px;
                min-width: 60px;
                max-width: 80px;
                min-height: 25px;
                font-size: 9px;
            """)
            btn.clicked.connect(func)
            btn.setFixedHeight(40)
            btn.setFixedWidth(85)
            hbox.addWidget(btn)
        return hbox

    def create_results_section(self, layout):
        group = QGroupBox("RÉSULTATS")
        vbox = QVBoxLayout()
        img_label = QLabel()
        try:
            pixmap = QPixmap(r"C:\Users\aya mejri\Downloads\cm13001.jpg").scaled(150, 150)
            img_label.setPixmap(pixmap)
        except:
            img_label.setText("📷")
        img_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(img_label)
        self.result_btn = QPushButton("ANALYSER")
        self.result_btn.setStyleSheet("background-color: #4a6fa5;")
        self.result_btn.clicked.connect(self.analyze_results)
        vbox.addWidget(self.result_btn)
        self.result_label = QLabel("WAIT ...")
        self.result_label.setProperty("class", "status-wait")
        vbox.addWidget(self.result_label)
        group.setLayout(vbox)
        layout.addWidget(group, 1, 1)

    def create_camera_section(self, layout):
        group = QGroupBox("AFFICHAGE IMAGE")
        vbox = QVBoxLayout()
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setObjectName("prev_button")
        self.prev_btn.setToolTip("Image précédente")
        self.prev_btn.setStyleSheet("QPushButton.nav-button")
        self.prev_btn.clicked.connect(self.show_prev_image)
        self.prev_btn.setEnabled(False)
        self.next_btn = QPushButton("▶")
        self.next_btn.setObjectName("next_button")
        self.next_btn.setToolTip("Image suivante")
        self.next_btn.setStyleSheet("QPushButton.nav-button")
        self.next_btn.clicked.connect(self.show_next_image)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        vbox.addLayout(nav_layout)
        self.camera_label = QLabel("En attente d'images...")
        self.camera_label.setObjectName("camera_label")
        self.camera_label.setMinimumSize(600, 500)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            background-color: #2c3e50;
            color: #ecf0f1;
            font-size: 16px;
            font-weight: bold;
            border: 2px solid #34495e;
            padding: 10px;
        """)
        vbox.addWidget(self.camera_label)
        self.image_info = QLabel("Aucune image chargée")
        self.image_info.setAlignment(Qt.AlignCenter)
        self.image_info.setStyleSheet("color: #95a5a6; font-size: 12px;")
        vbox.addWidget(self.image_info)
        group.setLayout(vbox)
        layout.addWidget(group)

    def show_prev_image(self):
        if self.image_history and self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_image(self.image_history[self.current_image_index])
            self.update_nav_buttons()

    def show_next_image(self):
        if self.image_history and self.current_image_index < len(self.image_history) - 1:
            self.current_image_index += 1
            self.display_image(self.image_history[self.current_image_index])
            self.update_nav_buttons()

    def update_nav_buttons(self):
        self.prev_btn.setEnabled(self.current_image_index > 0)
        self.next_btn.setEnabled(self.current_image_index < len(self.image_history) - 1)

    def disable_led_buttons(self):
        for btn_name in ["LEDPON", "LEDPOFF", "LEDQON", "LEDQOFF"]:
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                btn.setEnabled(False)

    def enable_led_buttons(self):
        for btn_name in ["LEDPON", "LEDPOFF", "LEDQON", "LEDQOFF"]:
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                btn.setEnabled(True)

    def led_p_on(self):
        if self.is_led_sequence_running:
            return
        self.is_led_sequence_running = True
        self.disable_led_buttons()
        self.run_serial_command("LEDPON", b"MS 0 1 39CF\r")

    def led_p_off(self):
        if self.is_led_sequence_running:
            return
        self.is_led_sequence_running = True
        self.disable_led_buttons()
        self.run_serial_command("LEDPOFF", b"MS 0 0 0AFE\r")

    def led_q_on(self):
        if self.is_led_sequence_running:
            return
        self.is_led_sequence_running = True
        self.disable_led_buttons()
        self.run_serial_command("LEDQON", b"MS 1 1 4F7B\r")

    def led_q_off(self):
        if self.is_led_sequence_running:
            return
        self.is_led_sequence_running = True
        self.disable_led_buttons()
        self.run_serial_command("LEDQOFF", b"MS 1 0 7C4A\r")

    def backlight_on(self):
        self.run_serial_command("BacklightON", b"MT 3 1 6A52\r")

    def backlight_off(self):
        self.run_serial_command("BacklightOFF", b"MT 3 0 5963\r")

    def lcd_black_screen(self):
        self.run_serial_command("LCDBlack", b"MV 1 F6B0\r")

    def lcd_clear_screen(self):
        self.run_serial_command("LCDClear", b"MV 2 A3E3\r")

    def lcd_restart(self):
        self.run_serial_command("LCDRestart", b"MV 0 C581\r")
        self.is_led_sequence_running = False
        self.enable_led_buttons()

    def run_serial_command(self, cmd_name, command_bytes):
        QTimer.singleShot(50, lambda: self._execute_serial_command(cmd_name, command_bytes))

    def _execute_serial_command(self, cmd_name, command_bytes):
        try:
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            if "COM3" not in available_ports:
                raise serial.SerialException("Port COM3 introuvable")
            with serial.Serial(port="COM3", baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=2) as conn:
                conn.write(command_bytes)
                time.sleep(0.5)
                response = conn.read_all().decode().strip()
                status = "PASS" if "OK" in response or not response else "FAIL"
                QTimer.singleShot(500, lambda: self._update_ui_after_command(cmd_name, status, response))
        except serial.SerialException as e:
            print(f"[ERREUR] {cmd_name} : {str(e)}")
            QTimer.singleShot(500, lambda: self._update_ui_after_command(cmd_name, "FAIL", str(e)))
        except Exception as e:
            print(f"[ERREUR] {cmd_name} : {str(e)}")
            QTimer.singleShot(500, lambda: self._update_ui_after_command(cmd_name, "FAIL", str(e)))

    def _update_ui_after_command(self, cmd_name, status, msg=""):
        self.update_button_style(cmd_name, status)

        if "COM3" in msg or "port" in msg.lower():
            self.set_all_buttons_style("FAIL")
            self.result_label.setText(f"ERREUR : {msg}")
            self.result_label.setProperty("class", "status-fail")
        else:
            if cmd_name in ["LEDPON", "LEDPOFF", "LEDQON", "LEDQOFF"]:
                self.presence_label.setText(f"{cmd_name} {'✓' if status == 'PASS' else '✗'} {msg}")
                self.presence_label.setProperty("class", f"status-{status.lower()}")
            else:
                self.result_label.setText(f"{cmd_name} {'✓' if status == 'PASS' else '✗'} {msg}")
                self.result_label.setProperty("class", f"status-{status.lower()}")

        self.presence_label.style().unpolish(self.presence_label)
        self.presence_label.style().polish(self.presence_label)
        self.result_label.style().unpolish(self.result_label)
        self.result_label.style().polish(self.result_label)
        self.send_tcp_status(cmd_name, status, msg)

    def set_all_buttons_style(self, status):
        command_buttons = ["LEDPON", "LEDPOFF", "LEDQON", "LEDQOFF",
                          "BacklightON", "BacklightOFF",
                          "LCDBlack", "LCDClear", "LCDRestart"]
        for btn_name in command_buttons:
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                if status == "FAIL":
                    btn.setStyleSheet("background-color: #e74c3c; color: white;")
                else:
                    btn.setStyleSheet("background-color: #4a6fa5; color: white;")

    def update_button_style(self, cmd_name, status):
        btn_name = cmd_name.replace(' ', '')
        btn = self.findChild(QPushButton, btn_name)
        if btn:
            if status == "PASS":
                btn.setStyleSheet("background-color: #27ae60; color: white;")
            elif status == "FAIL":
                btn.setStyleSheet("background-color: #e74c3c; color: white;")
            else:
                btn.setStyleSheet("background-color: #f39c12; color: black;")
            short_name = self.get_shortname_from_cmd_name(cmd_name)
            if short_name:
                self.last_executed_component = {"component": short_name, "status": status}

    def get_shortname_from_cmd_name(self, cmd_name):
        return self.WHITELISTED_COMPONENTS.get(cmd_name, None)

    def send_tcp_status(self, command_name, status, error=""):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 9000))
            message = json.dumps({
                "command": command_name,
                "status": status,
                "message": error or "Réussite"
            })
            client_socket.sendall(message.encode())
            client_socket.close()
        except Exception as e:
            print(f"[ERREUR] Impossible d'envoyer via TCP : {e}")

    def handle_server_message(self, message):
        print(f"[TCP] Message reçu : {message}")
        image_path = message.get("image_path", "")
        status = message.get("status", "").upper()
        msg = message.get("message", "")

        if image_path and os.path.exists(image_path):
            self.display_image(image_path)
            if image_path not in self.image_history:
                self.image_history.append(image_path)
            self.current_image_index = self.image_history.index(image_path)
            self.update_nav_buttons()

            # Active le flag d'affichage spécial
            self.tcp_message_received = True

        if status in ["PASS", "FAIL"]:
            self.result_history.append(status)
            QTimer.singleShot(1000, lambda: self._update_labels_after_delay(status, msg))

        if message.get("test_completed", False):
            self.test_completed()

    def display_result_label_with_status(self):
        """
        Affiche dans result_label si le dernier composant exécuté a été détecté ou non.
        """
        if not self.last_executed_component:
            return

        component = self.last_executed_component["component"]
        status = self.last_executed_component["status"]

        display_names = {
            "P_ON": "LED P ON",
            "P_OFF": "LED P OFF",
            "Q_ON": "LED Q ON",
            "Q_OFF": "LED Q OFF",
            "LCD_BLACKLIGHT_ON": "Backlight ON",
            "LCD_BLACKLIGHT_OFF": "Backlight OFF",
            "LCD_BLACK": "LCD Black",
            "LCD_CLEAR": "LCD Clear",
            "LCD_RESTART": "LCD Restart"
        }

        readable_name = display_names.get(component, component)

        if status == "PASS":
            msg = f"{readable_name} ✓ détecté"
            self.result_label.setProperty("class", "status-pass")
        elif status == "FAIL":
            msg = f"{readable_name} ✗ non détecté"
            self.result_label.setProperty("class", "status-fail")
        else:
            msg = f"{readable_name} ⚠️ en attente"
            self.result_label.setProperty("class", "status-wait")

        self.result_label.setText(msg)
        self.result_label.style().unpolish(self.result_label)
        self.result_label.style().polish(self.result_label)
        self.result_label.update()

    def display_image(self, path):
        try:
            path = os.path.normpath(path)
            if not os.path.exists(path):
                self.camera_label.setText("Fichier introuvable")
                self.camera_label.setStyleSheet("color: #e74c3c;")
                self.image_info.setText(f"Erreur: {os.path.basename(path)}")
                return

            pixmap = QPixmap(path)
            if not pixmap.isNull():
                label_width = self.camera_label.width()
                label_height = self.camera_label.height()
                scaled_pixmap = pixmap.scaled(label_width, label_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.camera_label.setPixmap(scaled_pixmap)
                self.camera_label.setAlignment(Qt.AlignCenter)

                file_name = os.path.basename(path)
                file_size = f"{os.path.getsize(path)/1024:.1f} KB"
                timestamp = time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(path)))
                self.image_info.setText(f"{file_name} | {file_size} | {timestamp}")
                print(f"[IMAGE] Affichage de {file_name}")
            else:
                self.camera_label.setText("Image non chargée")
                self.camera_label.setStyleSheet("color: #f39c12;")
                self.image_info.setText("Format d'image non supporté")
        except Exception as e:
            print(f"[ERREUR] Affichage image: {e}")
            self.camera_label.setText(f"Erreur: {os.path.basename(path)}")
            self.camera_label.setStyleSheet("color: #e74c3c;")
            self.image_info.setText("Exception lors du chargement")

    def _update_labels_after_delay(self, status, msg):
        step = "Cnx_Moxa"
        formatted_msg = f"{step} {'✓' if status == 'PASS' else '✗'}\n{msg}"

        # Choisir le bon label
        if self.tcp_message_received:
            label = self.result_label
            self.tcp_message_received = False  # Réinitialiser le flag
        else:
            label = self.presence_label

        label.setText(formatted_msg)
        label.setProperty("class", f"status-{status.lower()}")
        label.style().unpolish(label)
        label.style().polish(label)
        label.update()

        command_buttons = {
            "LED P ON": "LEDPON",
            "LED P OFF": "LEDPOFF",
            "LED Q ON": "LEDQON",
            "LED Q OFF": "LEDQOFF",
            "Backlight ON": "BacklightON",
            "Backlight OFF": "BacklightOFF",
            "LCD Black": "LCDBlack",
            "LCD Clear": "LCDClear",
            "LCD Restart": "LCDRestart"
        }

        for cmd_name, btn_obj_name in command_buttons.items():
            btn = self.findChild(QPushButton, btn_obj_name)
            if btn:
                if cmd_name in msg:
                    btn.setStyleSheet("background-color: #27ae60;" if status == "PASS" else "background-color: #e74c3c;")
                elif status == "FAIL":
                    btn.setStyleSheet("background-color: #e74c3c; color: white;")

        if status == "FAIL" and not self.tcp_message_received:
            self.result_label.setText(formatted_msg)
            self.result_label.setProperty("class", f"status-{status.lower()}")
            self.result_label.style().unpolish(self.result_label)
            self.result_label.style().polish(self.result_label)
            self.result_label.update()
            if label == self.result_label and status == "FAIL":
                print("[AUTO] Échec détecté → Arrêt automatique du test.")
                QTimer.singleShot(2000, self.test_completed)
            
        # Dans _update_labels_after_delay(), après avoir choisi le label :
        if status == "FAIL" and self.tcp_message_received:
            self.result_label.setText(formatted_msg)
            self.result_label.setProperty("class", f"status-{status.lower()}")
            self.result_label.style().unpolish(self.result_label)
            self.result_label.style().polish(self.result_label)
            self.result_label.update()
            print("[AUTO] Échec détecté → Arrêt automatique du test.")
            QTimer.singleShot(2000, self.test_completed)
            # Dans _update_labels_after_delay(), après avoir choisi le label :

    def start_test(self):
        self.result_history.clear()
        self.test_running = True
        self.reset_interface()
        self.start_btn.setEnabled(False)
        success = self.run_teststand_visibly_and_run_sequence()
        if not success:
            self.test_failed()
        else:
            self.process_check_timer.start(1000)

    def run_teststand_visibly_and_run_sequence(self):
        seq_path = r"C:\Users\aya mejri\TestScripts2\Sequence File 1.seq"
        if not os.path.exists(seq_path):
            print(f"[ERREUR] Fichier .seq introuvable : {seq_path}")
            self.update_label(self.result_label, "Erreur", "FAIL", "Fichier TestStand non trouvé")
            return False
        try:
            os.startfile(seq_path)
            print(f"[OK] Fichier .seq ouvert : {seq_path}")
            time.sleep(5)
            return True
        except Exception as e:
            print(f"[ERREUR] Impossible d'ouvrir TestStand : {e}")
            self.update_label(self.result_label, "Erreur", "FAIL", f"Ouverture TestStand échouée : {e}")
            return False

    def check_process_status(self):
        pass

    def test_completed(self):
        self.test_running = False
        self.start_btn.setEnabled(True)

        if "FAIL" in self.result_history:
            self.result_label.setText("PRODUIT NON OK ❌")
            self.result_label.setProperty("class", "status-fail")
        else:
            self.result_label.setText("PRODUIT OK ✅")
            self.result_label.setProperty("class", "status-pass")

        self.result_label.style().unpolish(self.result_label)
        self.result_label.style().polish(self.result_label)
        self.result_label.update()
        
        QTimer.singleShot(2000, self.stop_test)
 
    def test_failed(self):
        self.test_running = False
        self.start_btn.setEnabled(True)

    def stop_test(self):
        print("[ARRÊT] Test arrêté manuellement par l'utilisateur")
        if self.process_check_timer.isActive():
            self.process_check_timer.stop()
        self.test_running = False
        self.start_btn.setEnabled(True)
        self.result_label.setText("TEST ARRÊTÉ MANUELLEMENT")
        self.result_label.setProperty("class", "status-fail")
        self.result_label.style().unpolish(self.result_label)
        self.result_label.style().polish(self.result_label)
        self.result_label.update()
        self.reset_interface()
        self.stop_btn.setStyleSheet("background-color: #c62828; border: 2px solid #8e0000;")
        QTimer.singleShot(300, self.restore_button_style)

    def restore_button_style(self):
        self.stop_btn.setStyleSheet("background-color: #e74c3c; border: none;")
        self.stop_btn.setStyleSheet("background-color: #e74c3c; border: none;")

    def reset_interface(self):
        for label in [self.presence_label, self.result_label]:
            label.setText("WAIT ...")
            label.setProperty("class", "status-wait")
        for btn_name in ["LEDPON", "LEDPOFF", "LEDQON", "LEDQOFF",
                         "BacklightON", "BacklightOFF",
                         "LCDBlack", "LCDClear", "LCDRestart"]:
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                btn.setStyleSheet("background-color: #4a6fa5; color: white;")
                btn.setEnabled(True)
        self.camera_label.clear()
        self.camera_label.setText("En attente d'images...")
        self.image_info.setText("Aucune image chargée")
        self.current_image_path = None
        self.image_history = []
        self.current_image_index = -1
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.is_led_sequence_running = False
        self.update_styles()

    def check_presence(self):
        if not self.test_running:
            return
        status = "PASS" if random.choice([False]) else "FAIL"
        self.update_label(self.presence_label, "Présence", status, "")

    def analyze_results(self):
        if not self.test_running:
            return
        status = "PASS" if random.choice([False]) else "FAIL"
        self.update_label(self.result_label, "Résultat", status, "")

    def update_label(self, label, step, status, msg):
        text = f"{step} {'✓' if status == 'PASS' else '✗'}\n{msg}"
        label.setText(text)
        label.setProperty("class", f"status-{status.lower()}")
        label.style().unpolish(label)
        label.style().polish(label)
        label.update()

    def update_styles(self):
        for widget in [self.presence_label, self.result_label]:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_image_path:
            self.display_image(self.current_image_path)

    def closeEvent(self, event):
        self.tcp_server.stop_server()
        self.stop_test()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())

