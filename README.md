# 🚀 ALPR Neural · Automated License Plate Recognition

A futuristic, high-performance license plate recognition system built with Python, Flask, and Dual-YOLO Architectures. This system features a real-time web dashboard with a "Neural" aesthetic, automated detection history, and a VIP authorization management system.

## 🏆 Project Milestone: WE DID IT!
The system is now fully operational, integrating:
- **Real-time Camera Feed** (DroidCam / Local)
- **Dual-YOLO Inference** (Plate Detection + Character Recognition)
- **Arduino Access Control** (LED Indicators & Serial Communication)
- **Persistent Database** (SQLite VIP & Scan History)
- **Cyberpunk Dashboard** (Live Monitoring & Management)

---

![Neural Dashboard](https://img.shields.io/badge/UI-Cyberpunk-00f5c8?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-Python%20|%20Flask%20|%20YOLOv8-7b5cff?style=for-the-badge)
![Hardware](https://img.shields.io/badge/Hardware-Arduino%20Integrated-ff5c5c?style=for-the-badge)

## ✨ Key Features

- **Dual-Model Processing**: Uses two separate YOLOv8 models for maximum accuracy:
  - `best.pt`: Optimized for license plate localization.
  - `best_ocr.pt`: Specialized in Arabic/English character recognition.
- **Live Video Stream**: Ultra-low latency MJPEG feed directly in your browser.
- **Neural Inference Engine**: High-accuracy plate detection with real-time probability scoring.
- **Hardware Integration**: Real-time Arduino feedback with LED indicators for authorized (Green) and unauthorized (Red) access.
- **VIP Management**: Dynamic dashboard to authorize or revoke matricules instantly.
- **Smart Analytics**: Automated history tracking and system performance stats.

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Flask
- **Vision**: OpenCV, Ultralytics YOLOv8
- **Hardware Control**: PySerial, Arduino (C++)
- **Database**: SQLite3
- **Frontend**: Vanilla JS, Space Grotesk Typography, Cyber-Neural CSS

## 🏁 Quick Start

### 1. Installation
Ensure you have Python 3.10+ installed. Install the required dependencies:

```bash
pip install flask opencv-python ultralytics imutils torch torchvision torchaudio pyserial
```

### 2. Configuration
The system is optimized for **DroidCam** or local cameras. Adjust the source in `camera.py`:

```python
# camera.py
url_camera = "http://100.72.66.91:4747/video" # Change to 0 for local webcam
self.cap = cv2.VideoCapture(url_camera)
```

### 3. Hardware Setup (Optional)
To use the LED access control system:
1. **Wiring**: 
   - **Pin 8**: Connect to a "Scanning" LED.
   - **Pin 12**: Connect to an "Authorized" LED (Green).
2. **Upload**: Flash the `.ino` sketch from `arduino_code/` to your board.
3. **Connect**: The system will automatically detect your Arduino on COM ports.

### 4. Launching the System
Start the main engine:

```bash
python backend.py
```

Access the dashboard at: **[http://localhost:5000](http://localhost:5000)**

## 📂 Project Structure

- `backend.py`: Core Flask server and API management.
- `camera.py`: The ALPR engine using dual YOLOv8 models.
- `database.py`: SQLite persistence layer.
- `arduino_controller.py`: Serial bridge for hardware signaling.
- `templates/`: Modern, responsive dashboard UI.
- `best.pt` & `best_ocr.pt`: Trained neural network weights.

## ⚠️ Performance Note
The system automatically detects if a **CUDA-capable GPU** is available. 
- **GPU Mode**: ~20-30 FPS (Recommended)
- **CPU Mode**: ~2-5 FPS (Functional but slower)

---
*Developed with ❤️ for the future of Intelligent Parking Systems.*
