# core/ace/secure.py
import json
import os
import time
import random
import string
from threading import Thread


class VerificationCode:
    def __init__(self, data=None):
        if data:
            self.code = data.get("code")
            self.generated_time = data.get("generated_time")
            self.used_codes = set(data.get("used_codes", []))
            self.last_verified_time = data.get("last_verified_time", 0)
            self.last_rejected_time = data.get("last_rejected_time", 0)
        else:
            self.code = None
            self.generated_time = None
            self.used_codes = set()
            self.last_verified_time = 0
            self.last_rejected_time = 0

    def to_dict(self):
        return {
            "code": self.code,
            "generated_time": self.generated_time,
            "used_codes": list(self.used_codes),
            "last_verified_time": self.last_verified_time,
            "last_rejected_time": self.last_rejected_time,
        }

    def generate_code(self):
        # 生成7天内不重复的验证码
        while True:
            new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if new_code not in self.used_codes:
                self.code = new_code
                self.generated_time = time.time()
                self.used_codes.add(new_code)
                # 定期清理 used_codes，防止无限增长
                if len(self.used_codes) > 1000:
                    self.used_codes = set(list(self.used_codes)[-500:])  # 保留最近500个验证码
                break

    def is_valid(self):
        if self.code is None:
            return False
        return time.time() - self.generated_time < 300  # 5分钟有效期

    def is_rejected_recently(self):
        return time.time() - getattr(self, 'last_rejected_time', 0) < 3600  # 1小时内拒绝过

    def mark_rejected(self):
        self.last_rejected_time = time.time()

    def mark_verified(self):
        self.last_verified_time = time.time()

    def is_verified_recently(self):
        return time.time() - self.last_verified_time < 604800  # 7天内验证过

class SecureInterface:
    def __init__(self):
        self.secure_file = "configs/secure.json"
        self.verification_code = self._load_verification_code()

    def _load_verification_code(self):
        if os.path.exists(self.secure_file):
            try:
                with open(self.secure_file, "r") as f:
                    data = json.load(f)
                    return VerificationCode(data)
            except json.JSONDecodeError:
                # 文件为空或格式错误，返回默认的 VerificationCode 对象
                return VerificationCode()
        else:
            return VerificationCode()

    def _save_verification_code(self):
        # 获取文件所在的目录路径
        directory = os.path.dirname(self.secure_file)

        # 如果目录不存在，则创建目录
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 打开文件并写入数据
        with open(self.secure_file, "w") as f:
            json.dump(self.verification_code.to_dict(), f)

    def _show_verification_dialog(self):
        if self.verification_code.is_valid():
            code = self.verification_code.code
        else:
            self.verification_code.generate_code()
            code = self.verification_code.code

        print(f"<API_V> 验证码: {code}")
        print(f"您的关键API在被请求，触发了ACE模块拦截。您可以：")
        print("1. 输入验证码以允许本次请求")
        print("2. 拒绝本次请求")
        print("3. 强制拒绝本次及后续1小时内的所有请求")

        while True:
            user_input = input("请选择 (1/2/3): ")
            if user_input in ["1", "2", "3"]:
                break
            print("无效的选择，请重新输入")

        if user_input == "1":
            verification_code_input = input("请输入验证码: ")
            if verification_code_input == code:
                self.verification_code.mark_verified()  # 标记为已验证
                return True
            else:
                print("验证码错误")
                return False
        elif user_input == "2":
            return False
        elif user_input == "3":
            self.last_rejected_time = time.time()
            return False

    def verify_request(self):
        if time.time() - self.verification_code.last_rejected_time < 3600:
            return False  # 1小时内强制拒绝过，直接拒绝

        if self.verification_code.is_verified_recently():
            return True  # 7天内验证过，直接允许

        # 在新线程中打开对话框，避免阻塞主线程
        verification_result = False

        def verification_thread():
            nonlocal verification_result
            verification_result = self._show_verification_dialog()

        thread = Thread(target=verification_thread)
        thread.start()
        thread.join()

        if verification_result:
            self.verification_code.code = None  # 验证成功后清空验证码，7天内不再重复验证
            self._save_verification_code()  # 保存数据到文件
            return True
        else:
            self._save_verification_code()  # 保存数据到文件
            return False