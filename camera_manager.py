import threading
import cv2
import time
import numpy as np
from multiprocessing import shared_memory
from config import CAMERA_URLS, FRAME_WIDTH, FRAME_HEIGHT


# --- Shared Memory Configuration ---
# Match dimensions to your config
SHAPE = (FRAME_HEIGHT, FRAME_WIDTH, 3)
DTYPE = np.uint8

# CRITICAL FIX FOR WINDOWS: 
# np.prod returns a numpy.int64, but Windows CreateFileMapping requires a Python int.
SHAPE = (FRAME_HEIGHT, FRAME_WIDTH, 3)
SIZE = int(np.prod(SHAPE) * np.dtype(np.uint8).itemsize)

class CameraManager:
    def __init__(self):
        self.frames = {}
        self.shm_blocks = {}   # To store the SharedMemory objects
        self.shm_arrays = {}   # To store the numpy wrappers (RAM access)
        self.locks = {i: threading.Lock() for i in range(len(CAMERA_URLS))}
        self.running = True

    def _setup_shared_memory(self, cam_id):
        """Creates or attaches to a named RAM block for each camera."""
        shm_name = f"parking_cam_{cam_id}"
        try:
            # Create a new shared memory block
            shm = shared_memory.SharedMemory(name=shm_name, create=True, size=SIZE)
            print(f"[SHM] Created new block: {shm_name}")
        except FileExistsError:
            # If the block was not cleaned up properly last time, attach to it
            shm = shared_memory.SharedMemory(name=shm_name)
            print(f"[SHM] Attached to existing block: {shm_name}")
        
        self.shm_blocks[cam_id] = shm
        # Map the memory block to a numpy array for easy pixel manipulation
        self.shm_arrays[cam_id] = np.ndarray(SHAPE, dtype=DTYPE, buffer=shm.buf)

    def start_all(self):
        """Initializes memory and starts background RTSP reader threads."""
        for cam_id, source in enumerate(CAMERA_URLS):
            self._setup_shared_memory(cam_id)
            t = threading.Thread(target=self._reader, args=(cam_id, source), daemon=True)
            t.start()
        print(f"[SYSTEM] Camera Manager: {len(CAMERA_URLS)} Shared Memory blocks active.")

    def _reader(self, cam_id, source):
        """Continuously pulls frames from RTSP and writes them into shared RAM."""
        cap = cv2.VideoCapture(source)
        # Prevent frame buffering (lag)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        while self.running:
            if not cap.grab():
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(source)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                continue

            ret, frame = cap.retrieve()
            if ret:
                frame_resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                
                # Update the Shared Memory buffer
                # [:] is mandatory: it copies the data INTO the existing RAM block
                self.shm_arrays[cam_id][:] = frame_resized
            
            # Tiny sleep to yield CPU to other threads
            time.sleep(0.005)

    def cleanup(self):
        """Releases memory blocks. Call this on system shutdown."""
        print("[SYSTEM] Cleaning up Shared Memory...")
        self.running = False
        for shm in self.shm_blocks.values():
            try:
                shm.close()
                shm.unlink() # Physically deletes the block from RAM
            except:
                pass

# --- GLOBAL EXPORTS ---

_cm_instance = None

def get_camera_manager():
    """Singleton: Returns/Starts the Master Camera Manager."""
    global _cm_instance
    if _cm_instance is None:
        _cm_instance = CameraManager()
        _cm_instance.start_all()
    return _cm_instance

def get_shared_frame(cam_id):
    """
    Helper for other modules/processes to read from the memory.
    Note: In a different Process, it is better to attach to the SHM directly
    as shown in your Yolo_Detection update.
    """
    try:
        shm = shared_memory.SharedMemory(name=f"parking_cam_{cam_id}")
        return np.ndarray(SHAPE, dtype=DTYPE, buffer=shm.buf)
    except FileNotFoundError:
        return None