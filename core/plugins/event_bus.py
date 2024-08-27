"""
AmyAlmond Plugins - core/plugins/event_bus.py
事件总线模块
"""
from collections import defaultdict
from typing import Callable, List

class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        """
        订阅事件，将处理函数绑定到事件类型。

        Args:
            event_type (str): 事件类型。
            handler (Callable): 处理该事件的函数。
        """
        self.subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        """
        取消订阅事件。

        Args:
            event_type (str): 事件类型。
            handler (Callable): 处理该事件的函数。
        """
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)

    async def publish(self, event_type: str, *args, **kwargs):
        if event_type in self.subscribers:
            last_result = None
            for handler in self.subscribers[event_type]:
                result = await handler(*args, **kwargs)
                if result is not None:
                    last_result = result
            return last_result
        return args[0] if args else None