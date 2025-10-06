# AI-Powered Vision Test System for Smart Meters

🎓 Final Year Engineering Project – Embedded Electronics  
👩‍💻 Author: **Aya Mejri**

## 📌 Project Overview

This project replaces the legacy **Vision Builder-based** test system with an **AI-driven vision testing solution** using **YOLOv8**, **Qt**, and **NI TestStand**.

Key achievements:
- ✅ **FPY increased from 89% to 96%**
- ✅ **False rejects reduced by >80%**
- ✅ **Inference time < 150 ms/image**
- ✅ Full integration with **industrial hardware** (DFK camera, Moxa ioLogik, optical CEI 62056-21)

## 🚀 Features

- **Multi-component detection**: LCD states, LED indicators (P/Q ON/OFF), button presence
- **Real-time Qt GUI** for test supervision and manual control
- **TCP/IP communication** between TestStand, Python, and Qt
- **Industrial protocols**: Modbus TCP, CEI 62056-21, JSON/TCP
- **Trained YOLOv8 models** (specialized per component)

## ⚙️ Tech Stack

| Layer | Technology |
|------|------------|
| **AI** | YOLOv8 (Ultralytics), Roboflow |
| **Backend** | Python 3.9+, OpenCV, PySerial, PyModbus |
| **GUI** | Qt / PySide6 |
| **Test Engine** | NI TestStand |
| **Hardware** | The Imaging Source DFK 23G031, Moxa ioLogik E1214 |
| **Protocols** | TCP/IP, Modbus, CEI 62056-21, JSON |

## 📂 Repository Structure

> 📖 Full documentation in `/docs/rapport_pfe.pdf`.

## 🏆 Results

- **96% FPY** achieved (vs. 89% with Vision Builder)
- **< 150 ms/image** inference time
- **Manual re-tests reduced by 80%**
- Validated on **real industrial prototype** 

## 👩‍💻 Author

**Aya Mejri**  
Embedded Electronics Engineer | AI & Industrial Automation  
📧 [mejri_aya.engineeremb@yahoo.com]  
🔗 [LinkedIn](https://linkedin.com/in/ayamejri)