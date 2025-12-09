from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, send_file
from flask_socketio import SocketIO, emit
import os
import socket
import qrcode
import io
import base64
import json
import time
import shutil
import zipfile
import sys
from datetime import datetime
from werkzeug.utils import secure_filename
from user_agents import parse
import random
import string
import sqlite3
import sqlite3
from flask import g
import webbrowser
import threading

# --- CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lan_share_secret'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024 # 16 GB Limit

# Use 'threading' to prevent Python 3.12 crashes, but keep all features
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

METADATA_FILE = 'metadata.json'
DATABASE = 'platform.db'
connected_clients = {}

# --- SECURITY ---
REMOTE_PIN = ''.join(random.choices(string.digits, k=4))
print(f"\n[!] REMOTE CONTROL PIN: {REMOTE_PIN}\n")

# --- DATABASE HANDLERS ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        # Traffic Log: Speed analytics
        db.execute('''CREATE TABLE IF NOT EXISTS traffic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount_mb REAL,
            direction TEXT
        )''')
        # Access Log: User actions
        db.execute('''CREATE TABLE IF NOT EXISTS access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip TEXT,
            device TEXT,
            action TEXT,
            details TEXT
        )''')
        # Blocked IPs
        db.execute('''CREATE TABLE IF NOT EXISTS blocked_ips (
            ip TEXT PRIMARY KEY,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        # Server Config: Global settings
        db.execute('''CREATE TABLE IF NOT EXISTS server_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
        # Set defaults if not exist
        db.execute("INSERT OR IGNORE INTO server_config (key, value) VALUES ('MAX_CONTENT_LENGTH', ?)", (str(app.config['MAX_CONTENT_LENGTH']),))
        db.execute("INSERT OR IGNORE INTO server_config (key, value) VALUES ('SPEED_LIMIT_MBPS', '0')") # 0 = Unlimited
        db.commit()

# --- MIDDLEWARE ---
@app.before_request
def check_blocklist():
    if request.endpoint == 'static': return
    try:
        db = get_db()
        blocked = db.execute("SELECT 1 FROM blocked_ips WHERE ip = ?", (request.remote_addr,)).fetchone()
        if blocked:
            return jsonify({'status': 'error', 'message': 'Access Denied: Your IP is blocked.'}), 403
            
        # Log Action
        if request.endpoint and 'api' in request.endpoint or 'upload' in request.endpoint or 'download' in request.endpoint:
             device, icon = get_device_info(request.user_agent.string)
             db.execute("INSERT INTO access_log (ip, device, action, details) VALUES (?, ?, ?, ?)",
                        (request.remote_addr, f"{icon} {device}", request.endpoint, str(request.view_args or request.form or '')))
             db.commit()
    except Exception as e:
        print(f"DB Error: {e}")

# --- HELPER FUNCTIONS ---

def load_metadata():
    try:
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_metadata(data):
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f)

def get_unique_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return new_filename

def log_activity(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    socketio.emit('server_log', {'msg': f"[{timestamp}] {msg}"})

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to public DNS to find local IP (no data sent)
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_device_info(user_agent_string):
    try:
        ua = parse(user_agent_string)
        if ua.is_mobile or ua.is_tablet:
            return 'Mobile', '📱'
        return 'PC', '💻'
    except:
        return 'Unknown', '🔌'

# --- ROUTES ---

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    metadata = load_metadata()
    
    file_list = []
    for f in files:
        meta = metadata.get(f, {})
        file_list.append({
            'name': f,
            'source': meta.get('source', 'Unknown'),
            'icon': meta.get('icon', '❓'),
            'time': meta.get('time', ''),
            'ip': meta.get('ip', '')
        })

    # Storage Stats
    try:
        total, used, free = shutil.disk_usage(app.config['UPLOAD_FOLDER'])
        storage_stats = {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'percent': round((used / total) * 100, 1)
        }
    except:
        storage_stats = {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'percent': 0}

    # Generate QR Code (HTTP)
    local_ip = get_local_ip()
    port = 5000
    address = f"http://{local_ip}:{port}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(address)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="PNG")
    qr_b64 = base64.b64encode(output_buffer.getvalue()).decode()
    
    device_type, _ = get_device_info(request.user_agent.string)
    is_admin = (device_type == 'PC')

    return render_template('index.html', 
                           files=file_list, 
                           qr_code=qr_b64, 
                           server_address=address,
                           storage=storage_stats,
                           is_admin=is_admin)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Helper to process a single file object
    def process_file(file):
        if file.filename == '': return False
        filename = secure_filename(file.filename)
        filename = get_unique_filename(filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        device_type, icon = get_device_info(request.user_agent.string)
        metadata = load_metadata()
        metadata[filename] = {
            'source': device_type,
            'icon': icon,
            'ip': request.remote_addr,
            'time': datetime.now().strftime("%I:%M %p")
        }
        save_metadata(metadata)
        log_activity(f"UPLOAD: {filename} from {request.remote_addr} ({device_type})")
        return filename

    # Handle multiple files (key 'files') or single file (key 'file')
    files = request.files.getlist('files')
    single_file = request.files.get('file')
    
    uploaded_names = []

    if files:
        for f in files:
            name = process_file(f)
            if name: uploaded_names.append(name)
    elif single_file:
         name = process_file(single_file)
         if name: uploaded_names.append(name)
    
    if uploaded_names:
        socketio.emit('new_file', {'name': 'Batch Upload' if len(uploaded_names) > 1 else uploaded_names[0]})  
        return 'OK'
    
    return redirect(request.url)

@app.route('/upload_folder', methods=['POST'])
def upload_folder():
    files = request.files.getlist('files')
    count = 0
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            filename = get_unique_filename(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            count += 1
            
    log_activity(f"FOLDER UPLOAD: Received {count} files from {request.remote_addr}")
    socketio.emit('new_file', {'name': 'Folder Batch'}) 
    return 'OK'

@app.route('/download/<filename>')
def download_file(filename):
    log_activity(f"DOWNLOAD: {filename} by {request.remote_addr}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/download_all')
def download_all():
    log_activity(f"ZIP DOWNLOAD: {request.remote_addr} requested full backup")
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        for f in files:
            zf.write(os.path.join(app.config['UPLOAD_FOLDER'], f), arcname=f)
    memory_file.seek(0)
    return send_file(memory_file, download_name='all_files.zip', as_attachment=True)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        metadata = load_metadata()
        if filename in metadata:
            del metadata[filename]
            save_metadata(metadata)
        socketio.emit('file_deleted', {'name': filename})
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/disconnect_all', methods=['POST'])
def disconnect_all_users():
    socketio.emit('force_disconnect')
    return jsonify({'status': 'success'})

@app.route('/api/auth/verify', methods=['POST'])
def verify_pin():
    data = request.json
    if data.get('pin') == REMOTE_PIN:
        with app.test_request_context():
             # In a real app we'd use a secure session, but here we can just return success
             # and let the frontend store a token, or just rely on the PIN being sent with requests.
             # Actually, let's use a simplified session check based on IP for this LAN tool.
             pass
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid PIN'}), 401

@app.route('/api/pin', methods=['GET'])
def get_pin():
    # Only allow Admin (PC) to see the PIN via API
    device_type, _ = get_device_info(request.user_agent.string)
    if device_type == 'PC':
        return jsonify({'pin': REMOTE_PIN})
    return jsonify({'status': 'error'}), 403

@app.route('/remote/lock', methods=['POST'])
def remote_lock():
    # Auth Check
    device_type, _ = get_device_info(request.user_agent.string)
    data = request.get_json(silent=True) or {}
    client_pin = data.get('pin')
    
    if device_type != 'PC' and client_pin != REMOTE_PIN:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        log_activity("ADMIN: Executing Remote Lock")
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Not Windows'}), 400

@app.route('/remote/shutdown', methods=['POST'])
def remote_shutdown():
    # Auth Check
    device_type, _ = get_device_info(request.user_agent.string)
    data = request.get_json(silent=True) or {}
    client_pin = data.get('pin')
    
    if device_type != 'PC' and client_pin != REMOTE_PIN:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    cmd = "shutdown /s /t 60" if sys.platform == 'win32' else "shutdown -h +1"
    log_activity("ADMIN: Executing Remote Shutdown")
    os.system(cmd)
    return jsonify({'status': 'success'})

@app.route('/api/control/kill_server', methods=['POST'])
def kill_server():
    # Only allow Admin (PC) or Authenticated Mobile
    device_type, _ = get_device_info(request.user_agent.string)
    data = request.get_json(silent=True) or {}
    client_pin = data.get('pin')
    
    # Simple check: local admin or PIN auth
    if device_type == 'PC' or client_pin == REMOTE_PIN:
        print("[!] KILL COMMAND RECEIVED. SHUTTING DOWN...")
        os._exit(0) # Force kill
    return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

@app.route('/api/control/restart_server', methods=['POST'])
def restart_server():
    device_type, _ = get_device_info(request.user_agent.string)
    if device_type == 'PC':
        print("[!] RESTART COMMAND RECEIVED...")
        socketio.emit('server_log', {'msg': '[SYSTEM] Server Restarting...'})
        # Allow time for emission
        def restart():
            time.sleep(1)
            sys.exit(5) # Exit code 5 triggers restart in batch file
        
        import threading
        threading.Thread(target=restart).start()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

# --- ADMIN ROUTES ---
@app.route('/admin')
def admin_panel():
    # Basic protection: Only PC or Localhost can view Admin Panel
    # For better security, we'd use a login session
    device_type, _ = get_device_info(request.user_agent.string)
    if device_type != 'PC':
         return "<h1>403 Forbidden</h1><p>Admin panel is accessible only from the Host PC.</p>", 403
    return render_template('admin.html')

@app.route('/api/admin/stats')
def admin_stats():
    db = get_db()
    # Mocking real-time stats for now based on what we have
    total_traffic_q = db.execute("SELECT SUM(amount_mb) as total FROM traffic_log").fetchone()
    total_traffic = round(total_traffic_q['total'] or 0, 2)
    
    # Active Users (Active in last 5 mins)
    # Using access_log to find unique IPs recently
    active_users = len(connected_clients) # Using socket clients as proxy for active
    
    # Storage
    total, used, free = shutil.disk_usage(app.config['UPLOAD_FOLDER'])
    
    # Active Sessions List
    sessions = []
    # Mix socket clients + recent DB access
    for sid, info in connected_clients.items():
        sessions.append({
            'ip': info['ip'],
            'device': info['device'],
            'last_action': 'Online'
        })
    
    # Calculate Real Speed (MB/s in last 5 seconds)
    try:
        # Check traffic in last 10 seconds to get an average
        speed_q = db.execute("""
            SELECT SUM(amount_mb) as total 
            FROM traffic_log 
            WHERE timestamp > datetime('now', '-5 seconds')
        """).fetchone()
        recent_mb = speed_q['total'] or 0
        current_speed = round(recent_mb / 5, 2) # MB per second
    except:
        current_speed = 0

    return jsonify({
        'total_traffic': f"{total_traffic} MB",
        'active_users': active_users,
        'storage_used': f"{round(used / (1024**3), 2)} GB",
        'current_speed': current_speed,
        'sessions': sessions
    })

@app.route('/api/admin/block', methods=['POST'])
def block_ip():
    ip = request.json.get('ip')
    if ip:
        db = get_db()
        db.execute("INSERT OR IGNORE INTO blocked_ips (ip, reason) VALUES (?, 'Admin Block')", (ip,))
        db.commit()
        # Disconnect if connected via socket
        for sid, info in list(connected_clients.items()):
            if info['ip'] == ip:
                socketio.emit('disconnect_user', room=sid) 
        return jsonify({'status': 'success'})
    return jsonify({'error': 'No IP'}), 400

@app.route('/api/admin/config', methods=['POST'])
def save_config():
    data = request.json
    db = get_db()
    if 'max_size_gb' in data:
        bytes_val = int(data['max_size_gb']) * 1024 * 1024 * 1024
        app.config['MAX_CONTENT_LENGTH'] = bytes_val
        db.execute("INSERT OR REPLACE INTO server_config (key, value) VALUES ('MAX_CONTENT_LENGTH', ?)", (str(bytes_val),))
    if 'speed_limit' in data:
        db.execute("INSERT OR REPLACE INTO server_config (key, value) VALUES ('SPEED_LIMIT_MBPS', ?)", (str(data['speed_limit']),))
    db.commit()
    return jsonify({'status': 'success'})

# --- SOCKET EVENTS ---
@socketio.on('connect')
def handle_connect():
    device_type, icon = get_device_info(request.user_agent.string)
    connected_clients[request.sid] = {'ip': request.remote_addr, 'device': device_type}
    log_activity(f"CONNECT: {request.remote_addr}")
    emit('update_users', list(connected_clients.values()), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_clients:
        del connected_clients[request.sid]
        emit('update_users', list(connected_clients.values()), broadcast=True)

@socketio.on('clipboard_change')
def handle_clipboard(data):
    # Syncs text between devices
    emit('clipboard_update', data, broadcast=True, include_self=False)

@socketio.on('ping_device')
def handle_ping():
    emit('ping_trigger', broadcast=True)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        init_db()

    # HTTP Mode (No SSL)
    # HTTP Mode (No SSL)
    print(f"[*] Server Starting on http://0.0.0.0:5000")
    
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://localhost:5000')
        
    threading.Thread(target=open_browser).start()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
