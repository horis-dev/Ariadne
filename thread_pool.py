from concurrent.futures import ThreadPoolExecutor
import threading

_thread_pool = None
_lock = threading.Lock()

def get_global_thread_pool(max_workers=5):
    global _thread_pool
    if _thread_pool is None:
        with _lock:
            if _thread_pool is None:
                _thread_pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="GlobalPool")
    return _thread_pool