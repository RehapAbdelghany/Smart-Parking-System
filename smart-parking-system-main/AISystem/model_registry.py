"""
model_registry.py
-----------------
Loads CLIP and OSNet exactly once per process and shares them across
every VehicleTracker instance.  Thread-safe via a module-level lock.
"""

import threading
import torch
from transformers import CLIPModel, CLIPProcessor
import torchreid


class _ModelRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # Double-checked locking so the heavy model loads happen only once
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def initialize(self, device: str = None):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:   # re-check inside lock
                return

            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

            print(f"[ModelRegistry] Loading CLIP on {self.device}…")
            self.clip_model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32"
            ).to(self.device)
            self.clip_processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
            self.clip_model.eval()

            print(f"[ModelRegistry] Loading OSNet on {self.device}…")
            self.reid_model = torchreid.models.build_model(
                name="osnet_x1_0", num_classes=1000, pretrained=True
            )
            self.reid_model.eval().to(self.device)

            self._initialized = True
            print("[ModelRegistry] All models ready.")


# Public singleton accessor
ModelRegistry = _ModelRegistry()