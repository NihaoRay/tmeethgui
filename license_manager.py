import hashlib
import hmac
import uuid
import subprocess
import os
import json
from cryptography.fernet import Fernet
import time

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


def generate_key(key_file_path="secret.key"):
    """
    生成一个新的密钥并保存到文件中。
    注意：在实际项目中，密钥应该妥善保管，不要硬编码在代码中。
    """
    key = Fernet.generate_key()
    with open(key_file_path, "wb") as key_file:
        key_file.write(key)
    print(f"密钥已生成并保存至: {key_file_path}")
    return key


def encrypt_timestamp_to_file(key, output_file_path="model_tap.bin"):
    """
    获取当前时间戳，使用密钥加密后写入文件。
    """
    try:
        # 1. 获取当前时间戳（例如：1710150000.123456）
        current_timestamp = time.time()
        print(f"原始时间戳: {current_timestamp}")

        # 2. 将时间戳转换为字符串，再编码为 bytes
        timestamp_bytes = str(current_timestamp).encode('utf-8')

        # 3. 初始化 Fernet 实例并进行加密
        f = Fernet(key)
        encrypted_data = f.encrypt(timestamp_bytes)

        # 4. 将加密后的数据写入文件（使用 'wb' 二进制写入模式）
        with open(output_file_path, "wb") as file:
            file.write(encrypted_data)

        print(f"时间戳已成功加密并写入至: {output_file_path}")

    except Exception as e:
        print(f"加密或写入文件时发生错误: {e}")


def decrypt_timestamp_from_file(key, input_file_path="model_tap.bin"):
    """
    从文件中读取加密的时间戳，并使用密钥进行解密。
    （此函数用于验证加密是否成功）
    """
    try:
        # 1. 读取加密文件
        with open(input_file_path, "rb") as file:
            encrypted_data = file.read()

        # 2. 初始化 Fernet 实例并进行解密
        f = Fernet(key)
        decrypted_bytes = f.decrypt(encrypted_data)

        # 3. 将解密后的 bytes 转换回浮点数
        decrypted_timestamp = float(decrypted_bytes.decode('utf-8'))
        print(f"解密后的时间戳: {decrypted_timestamp}")
        return decrypted_timestamp

    except Exception as e:
        print(f"读取或解密文件时发生错误: {e}")

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


if __name__ == "__main__":
    # 运行前请确保已安装 cryptography 库：pip install cryptography

    # 第一步：生成或获取密钥
    # 在实际应用中，你可能已经有了一个密钥，直接读取即可
    my_key = generate_key()

    # 第二步：加密时间戳并写入文件
    encrypt_timestamp_to_file(my_key, "timestamp.enc")

    # 第三步：验证测试，读取并解密
    print("-" * 30)
    decrypt_timestamp_from_file(my_key, "timestamp.enc")