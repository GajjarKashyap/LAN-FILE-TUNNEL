# 🔧 Technical Issue: Binary File Corruption (ZIP/PDF)

### **Problem Description**

When transferring binary files (specifically `.zip`, `.pdf`, or `.exe`) over the LAN, the transfer completes successfully, but the resulting file is **corrupted** and cannot be opened.

  * **Symptoms:** ZIP files show "Unexpected end of archive," PDFs show blank pages or errors.
  * **Affected Files:** Binary formats (ZIP, PDF, EXE).
  * **Unaffected Files:** Text files (`.txt`, `.py`) and streamable media (`.mp4`) often appear to work because they are less sensitive to missing bytes.

### **Root Cause Analysis**

The corruption is caused by a **WSGI Server Conflict** in the Python environment.

1.  **The Conflict:**

      * **In `app.py`:** You explicitly forced the server to use **Threading** mode:
        ```python
        socketio = SocketIO(app, async_mode='threading', ...)
        ```
      * **In `run_app.bat`:** You installed the **Eventlet** library:
        ```batch
        pip install ... eventlet ...
        ```

2.  **Why this breaks transfers:**

      * When `flask_socketio` detects that `eventlet` is installed, it attempts to use Eventlet's asynchronous workers to handle network traffic, even if `async_mode='threading'` is requested.
      * Eventlet requires "monkey patching" (modifying Python's standard library to be async-compatible) to work correctly with file I/O.
      * Since your code uses standard Python file writing methods (`file.save()`, `open()`) **without** monkey patching, the async server interrupts the file stream prematurely.
      * **Result:** The file saves to the disk, but the last few kilobytes (bytes) of data are lost/truncated, causing corruption.

-----

### **✅ The Solution**

To fix this, we must ensure the environment matches the code's logic. We will remove the conflicting library and rely purely on Python's native threading.

#### **Step 1: Uninstall the Conflicting Library**

Open your terminal (or Command Prompt) and run:

```bash
pip uninstall eventlet
```

*(Type `y` and press Enter if prompted)*

#### **Step 2: Update the Launcher Script**

Edit your `run_app.bat` file to stop installing `eventlet` automatically.

**Change this line:**

```batch
pip install flask flask-socketio eventlet user-agents qrcode pillow
```

**To this:**

```batch
pip install flask flask-socketio user-agents qrcode pillow
```

#### **Step 3: Verify Application Code**

Ensure `app.py` remains configured for threading (no changes needed if it looks like this):

```python
# app.py
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
```

### **Why this fixes it**

By removing `eventlet`, Flask-SocketIO is forced to use the standard **Werkzeug** development server (which uses standard Python threads). This server is fully compatible with standard file I/O operations on Windows, ensuring every byte of the file is written to the disk before the connection closes.
