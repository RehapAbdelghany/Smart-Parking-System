import queue

# One unique queue for every AISystem ID
queues = {i: queue.Queue(maxsize=1) for i in range(6)}
# Shared storage for the UI
processed_results = {}