import re
from core.utils.logger import get_logger

_log = get_logger()


class InputValidator:
    def __init__(self):
        self.whitelist_patterns = [
            # 放宽对部分内容的限制，比如允许合法的HTML标签（如 <b>，<i> 等）
            r"<(b|i|u|strong|em|code)>.*?</\1>",
            # 允许URL（不带JavaScript）
            r"https?://[^\s]+",
        ]

        self.suspicious_patterns = [
            # SQL注入模式检测
            r"(?:')|(?:--)|(/\*(?:.|[\n\r])*?\*/)|(\b(select|update|delete|insert|truncate|alter|drop)\b)",
            # XSS攻击检测，强化对特定JavaScript行为的检测
            r"(<script.*?>.*?</script.*?>)|(<.*?javascript:.*?>)|(<.*?\\s+on\\w+\\s*=\\s*['\"].*?['\"].*?>)",
            # 执行类代码检测
            r"\b(exec|execute|system|shell|eval|os\.)\b",
            # 特定字符的组合检测
            r"[<>\"'/;]&&[^<>\"'/;]*",  # 要求特定字符旁无合法字符时才拦截
        ]

    def validate(self, content):
        """
        验证用户输入，防止SQL注入、XSS等攻击。

        参数:
            content (str): 用户输入的内容

        返回:
            bool: 如果输入合法，返回 True，否则返回 False
        """
        if self._matches_whitelist(content):
            return True

        if self._matches_suspicious_patterns(content):
            _log.warning(f"<ACE/IV> 🚫检测到可疑的用户输入: {content}")
            return False

        return True

    def _matches_whitelist(self, content):
        """
        检查输入内容是否符合白名单规则。

        参数:
            content (str): 用户输入的内容

        返回:
            bool: 如果符合白名单规则，返回 True，否则返回 False
        """
        for pattern in self.whitelist_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                return True
        return False

    def _matches_suspicious_patterns(self, content):
        """
        检查输入内容是否符合可疑模式。

        参数:
            content (str): 用户输入的内容

        返回:
            bool: 如果符合可疑模式，返回 True，否则返回 False
        """
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                _log.debug(f"<ACE/IV> 🚫匹配到的模式: {pattern}")
                return True
        return False
