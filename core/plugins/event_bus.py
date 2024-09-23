"""
AmyAlmond Plugins - core/plugins/event_bus.py
事件总线模块
"""
from collections import defaultdict
from typing import Callable
from core.utils.logger import get_logger

_log = get_logger()

class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        _log.info("EventBus initialized.")

    def subscribe(self, event_type: str, handler: Callable, plugin_name: str, priority: int = 0):
        """
        订阅事件，并按优先级排序。
        """
        self.subscribers[event_type].append((handler, plugin_name, priority))
        self.subscribers[event_type].sort(key=lambda x: x[2], reverse=True)  # 按优先级排序
        _log.info(f"Subscribed {plugin_name} to {event_type} event with priority {priority}.")

    async def publish(self, event_type: str, *args, **kwargs):
        if event_type in self.subscribers:
            _log.info(f"Publishing event {event_type} to {len(self.subscribers[event_type])} subscribers.")
            handlers = [handler for handler, _, _ in self.subscribers[event_type]]
            last_result = None
            for handler in handlers:
                result = await handler(*args, **kwargs)
                if result is not None:
                    if isinstance(result, dict):
                        kwargs.update(result)
                    elif isinstance(result, str):
                        kwargs['reply_message'] = result
                    elif isinstance(result, bool) and event_type == "before_llm_message":
                        if not result:
                            return kwargs.get('reply_message', last_result)
                    last_result = result
            return kwargs.get('reply_message', last_result)
        _log.warning(f"No subscribers for event {event_type}.")
        return args[0] if args else None
