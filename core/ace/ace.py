# core/ace/ace.py

from core.ace.input_validation import InputValidator
from core.ace.rate_limiting import RateLimiter

class ACE:
    def __init__(self):
        # 初始化InputValidator和RateLimiter
        self.input_validator = InputValidator()
        self.rate_limiter = RateLimiter()

    def validate_user_input(self, content):
        """
        验证用户输入，防止SQL注入、XSS等攻击。

        参数:
            content (str): 用户输入的内容

        返回:
            bool: 如果输入合法，返回 True，否则返回 False
        """
        return self.input_validator.validate(content)

    def check_request_frequency(self, user_id):
        """
        检查用户的请求频率是否超过限制。

        参数:
            user_id (str): 用户ID

        返回:
            bool: 如果请求频率在限制范围内，返回 True，否则返回 False
        """
        return self.rate_limiter.is_request_allowed(user_id)
