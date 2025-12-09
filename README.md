-----

````markdown
# 🛡️ LAN-FILE-TUNNEL (Silent Count)
> **The Ultimate Local Network Hub:** High-Speed File Transfer, Remote Administration & Universal Clipboard.

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-SocketIO-lightgrey?style=for-the-badge&logo=flask)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android%20%7C%20iOS-green?style=for-the-badge)

**LAN-FILE-TUNNEL** is a robust, self-hosted web application that transforms your PC into a local server. Transfer files at Wi-Fi speeds, sync your clipboard across devices, and control your host PC remotely—all without an internet connection.

---

## ⚡ Key Features

### 🚀 High-Performance Transfer
* **Zero Internet Required:** Uses your local Wi-Fi bandwidth for maximum speed.
* **Batch & Folder Uploads:** Drag and drop entire folders or multiple files at once.
* **One-Click ZIP Download:** Download specific files or zip the entire server storage instantly.
* **Resume Capability:** Handles large file transfers with stability.

### 🛡️ "Cyber" Command Center
* **Matrix Traffic Monitor:** A live, scrolling terminal log showing real-time server activity, IP connections, and requests.
* **Remote PC Control:**
    * 🔒 **Lock Workstation:** Secure your PC instantly from your phone (Windows only).
    * 🛑 **Remote Shutdown:** Turn off the host machine remotely.
    * 📡 **Device Ping:** Send audio/vibration signals to find connected devices.
* **Security:** PIN-based authentication ensures only you can execute remote commands.

### 📲 Universal Clipboard & Media
* **Real-Time Sync:** Copy text on your PC and paste it on your phone instantly (and vice-versa).
* **In-Browser Streaming:** Watch videos (`.mp4`, `.mkv`) or listen to music (`.mp3`) directly in the browser without downloading.

### 📊 Admin Dashboard
* **Live Analytics:** Visual graphs for upload/download speeds and traffic consumption.
* **User Management:** View active sessions, identify device types, and block specific IP addresses.
* **Server Config:** Adjust speed limits and max file size caps on the fly.

---

## 📸 Screenshots

| **Admin Dashboard** | **Mobile Client** |
|:---:|:---:|
| ![Dashboard](Fileshare/screenshots/Screenshot%20(2).png) | ![Mobile](Fileshare/screenshots/Screenshot_20251209_203649.jpg) |
| *Real-time traffic graphs & settings* | *Dark mode UI & QR Connect* |

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.x installed on the host machine.
* A Wi-Fi network (Host and Client must be on the same network).

### 1. Installation
Clone the repository and install the dependencies:

```bash
git clone [https://github.com/YourUsername/LAN-FILE-TUNNEL.git](https://github.com/YourUsername/LAN-FILE-TUNNEL.git)
cd LAN-FILE-TUNNEL
pip install flask flask-socketio eventlet user-agents qrcode pillow
````

### 2\. Running the Server

**Option A: The Easy Way (Windows)**
Double-click `run_app.bat`. This script will:

1.  Close existing browser instances (optional, for a clean start).
2.  Launch the server.
3.  Automatically open the Admin Dashboard.

**Option B: Manual Start (Terminal)**

```bash
python app.py
```

### 3\. Connecting Devices

1.  Open the Admin Dashboard on your PC.
2.  Scan the **QR Code** on the sidebar with your phone.
3.  Or manually enter the IP address shown (e.g., `http://192.168.1.X:5000`).

-----

## ⚙️ Configuration

You can modify `app.py` or use the **Admin Dashboard** GUI to change these settings:

  * **`UPLOAD_FOLDER`**: Directory where files are saved (Default: `uploads`).
  * **`MAX_CONTENT_LENGTH`**: Maximum file size limit (Default: 16GB).
  * **`REMOTE_PIN`**: The security PIN for remote shutdown/lock (Generated randomly on startup, viewable in Admin sidebar).

-----

## 🤝 Connect & Support

This project is maintained by **Gajjar Kashyap**.

  * 📸 **Instagram:** [**@gajjar\_090**](https://www.instagram.com/gajjar_090?igsh=MW1oODN0aGUxdmtvaQ==)
  * 🐙 **GitHub:** [Fork & Contribute](https://www.google.com/search?q=%23)

> *Feel free to DM on Instagram for feature requests or support\!*

-----

## ⚠️ Disclaimer

This tool uses HTTP for maximum local speed. It is intended for **Private Home Wi-Fi** use. Do not use on public networks (airports, cafes) as data is not encrypted.

```
```
