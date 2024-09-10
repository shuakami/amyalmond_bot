# core/ace/rate_limiting.py

import time
from collections import defaultdict, deque
from core.utils.logger import get_logger
from config import REQUEST_LIMIT_TIME_FRAME, REQUEST_LIMIT_COUNT, GLOBAL_RATE_LIMIT

_log = get_logger()


class RateLimiter:
    def __init__(self):
        # 用于存储每个用户的请求时间
        self.user_requests = defaultdict(lambda: deque(maxlen=REQUEST_LIMIT_COUNT))
        # 用于存储全局的请求时间
        self.global_requests = deque(maxlen=GLOBAL_RATE_LIMIT)

    def is_request_allowed(self, user_id):
        """
        检查用户的请求频率是否超过限制。

        参数:
            user_id (str): 用户ID

        返回:
            bool: 如果用户的请求频率在限制范围内，返回 True，否则返回 False
        """
        current_time = time.time()

        # 全局请求频率检查
        if not self.is_global_request_allowed(current_time):
            _log.warning("<ACE/RL> 🚫全局请求频率过高，已拦截")
            return False

        # 过滤掉过期的请求
        user_requests = self.user_requests[user_id]
        while user_requests and user_requests[0] < current_time - REQUEST_LIMIT_TIME_FRAME:
            user_requests.popleft()

        if len(user_requests) >= REQUEST_LIMIT_COUNT:
            _log.warning(f"<ACE/RL> 🚫用户 {user_id} 的请求频率过高，已拦截")
            return False

        # 记录用户的请求时间
        user_requests.append(current_time)

        # 更新全局请求队列
        self.global_requests.append(current_time)

        return True

    def is_global_request_allowed(self, current_time):
        """
        检查全局的请求频率是否超过限制。

        参数:
            current_time (float): 当前时间戳

        返回:
            bool: 如果全局的请求频率在限制范围内，返回 True，否则返回 False
        """
        # 过滤掉过期的全局请求
        while self.global_requests and self.global_requests[0] < current_time - 60:  # 全局限制在1分钟内
            self.global_requests.popleft()

        # 检查全局请求数是否超过限制
        return len(self.global_requests) < GLOBAL_RATE_LIMIT
