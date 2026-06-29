"""
CAPL-equivalent Python decorators.

@on_start          → on start {}
@on_stop           → on stop {}
@on_message(0x180) → on message 0x180 {}
@every(100)        → on timer t1 { setTimer(t1, 100); }
"""

import threading
from typing import Callable

_start_hooks: list[Callable] = []
_stop_hooks: list[Callable] = []
_message_hooks: dict[int, list[Callable]] = {}
_timers: list[threading.Timer] = []


def on_start(fn: Callable) -> Callable:
    _start_hooks.append(fn)
    return fn


def on_stop(fn: Callable) -> Callable:
    _stop_hooks.append(fn)
    return fn


def on_message(can_id: int):
    def decorator(fn: Callable) -> Callable:
        _message_hooks.setdefault(can_id, []).append(fn)
        return fn
    return decorator


def every(interval_ms: int):
    """Calls the decorated function every interval_ms milliseconds."""
    def decorator(fn: Callable) -> Callable:
        def _run():
            fn()
            t = threading.Timer(interval_ms / 1000.0, _run)
            _timers.append(t)
            t.daemon = True
            t.start()
        fn._interval_ms = interval_ms
        fn._starter = _run
        return fn
    return decorator


def fire_start():
    for fn in _start_hooks:
        fn()


def fire_stop():
    for t in _timers:
        t.cancel()
    _timers.clear()
    for fn in _stop_hooks:
        fn()


def fire_message(can_id: int, msg):
    for fn in _message_hooks.get(can_id, []):
        fn(msg)


def start_timers():
    """Call after fire_start() to activate @every decorated functions."""
    import importlib, sys
    for mod in list(sys.modules.values()):
        for attr in vars(mod).values() if hasattr(mod, '__dict__') else []:
            if callable(attr) and hasattr(attr, '_starter'):
                attr._starter()
