import hashlib
import hmac
import uuid
import subprocess
import os
import json

# ===== 这个密钥只有你自己知道，不要泄露 =====
SECRET_KEY = b"your_super_secret_key_here_change_me"


def get_machine_code():
    """获取机器唯一标识（CPU + MAC + 磁盘序列号）"""
    raw = ""

    # MAC 地址
    mac = uuid.getnode()
    raw += str(mac)

    # CPU ID（Windows）
    try:
        result = subprocess.check_output(
            'wmic cpu get processorid', shell=True, stderr=subprocess.DEVNULL
        ).decode().strip()
        cpu_id = result.split('\n')[-1].strip()
        raw += cpu_id
    except Exception:
        raw += "unknown_cpu"

    # 磁盘序列号（C 盘）
    try:
        result = subprocess.check_output(
            'wmic diskdrive get serialnumber', shell=True, stderr=subprocess.DEVNULL
        ).decode().strip()
        disk_serial = result.split('\n')[-1].strip()
        raw += disk_serial
    except Exception:
        raw += "unknown_disk"

    # 生成短一点的机器码（16位，方便用户复制）
    full_hash = hashlib.sha256(raw.encode()).hexdigest().upper()
    machine_code = '-'.join([full_hash[i:i+4] for i in range(0, 16, 4)])
    return machine_code


def generate_license(machine_code):
    """
    根据机器码生成授权码（开发者专用）
    """
    signature = hmac.new(SECRET_KEY, machine_code.encode(), hashlib.sha256).hexdigest().upper()
    license_key = '-'.join([signature[i:i+4] for i in range(0, 20, 4)])
    return license_key


def verify_license(machine_code, license_key):
    """
    验证授权码是否合法
    """
    expected = generate_license(machine_code)
    return license_key.strip().upper() == expected.strip().upper()


def get_license_path():
    """授权文件保存路径"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(app_dir, "license.json")


def save_license(license_key):
    """保存授权码到本地文件"""
    data = {"license_key": license_key.strip().upper()}
    with open(get_license_path(), "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_license():
    """读取本地保存的授权码"""
    path = get_license_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("license_key", None)
    except Exception:
        return None


def check_license():
    """
    检查当前机器是否已授权
    返回: (是否授权, 机器码)
    """
    machine_code = get_machine_code()
    saved_key = load_license()
    if saved_key and verify_license(machine_code, saved_key):
        return True, machine_code
    return False, machine_code