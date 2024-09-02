# core/ace/rate_limiting.py

import time
from collections import defaultdict
from core.utils.logger import get_logger

_log = get_logger()

class RateLimiter:
    def __init__(self):
        self.user_requests = defaultdict(list)
        self.REQUEST_LIMIT_TIME_FRAME = 10  # 每10秒
        self.REQUEST_LIMIT_COUNT = 8  # 最多8次请求

    def is_request_allowed(self, user_id):
        """
        检查用户的请求频率是否超过限制。

        参数:
            user_id (str): 用户ID

        返回:
            bool: 如果请求频率在限制范围内，返回 True，否则返回 False
        """
        current_time = time.time()
        self.user_requests[user_id] = [
            t for t in self.user_requests[user_id] if t > current_time - self.REQUEST_LIMIT_TIME_FRAME
        ]

        if len(self.user_requests[user_id]) >= self.REQUEST_LIMIT_COUNT:
            _log.warning(f"<ACE/RL> 🚫用户 {user_id} 的请求频率过高")
            return False

        # 记录新的请求时间
        self.user_requests[user_id].append(current_time)
        return True
