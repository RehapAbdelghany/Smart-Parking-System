import queue
from config import CAMERA_URLS

# One unique queue for every camera ID
queues = {i: queue.Queue(maxsize=1) for i in range(len(CAMERA_URLS))}
# Shared storage for the UI
processed_results = {}