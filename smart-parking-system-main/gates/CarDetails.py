
import os
import cv2
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from torchvision import transforms
from ultralytics import YOLO
import torchvision.models as models



class CarDetails:
    def __init__(self, image):
        self.image = image
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = models.resnet50(pretrained=True)
        self.model.eval()  # Add this for better performance
        self.model = self.model.to(self.device)
        self.yolo = YOLO("yolov8n-seg.pt")

    def crop_car_with_mask(self, image):
        results = self.yolo(image)[0]

        # Check if masks exist and boxes exist
        if results.masks is None or results.boxes is None:
            return image

        for mask, cls in zip(results.masks.data, results.boxes.cls):
            if int(cls) == 2:  # car
                mask = mask.cpu().numpy()
                mask = (mask > 0.5).astype(np.uint8)
                # resize mask to image size
                mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
                # apply mask
                segmented = image.copy()
                segmented[mask == 0] = 0
                return segmented

        return image

    def detect_car_color(self,img_bgr):
        if img_bgr is None or img_bgr.size == 0:
            return "Unknown"

        h, w = img_bgr.shape[:2]

        # ── 1. Focus on body center (avoid roof, bumpers, shadow edges) ──────────
        y1, y2 = int(h * 0.15), int(h * 0.85)
        x1, x2 = int(w * 0.10), int(w * 0.90)
        roi = img_bgr[y1:y2, x1:x2]

        img_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        H, S, V = img_hsv[:, :, 0], img_hsv[:, :, 1], img_hsv[:, :, 2]

        # ── 2. Build a validity mask: exclude pure black pixels (shadows/tires) ──
        valid = V > 30  # ignore near-black shadow/tire pixels

        total = np.count_nonzero(valid)
        if total == 0:
            return "Unknown"

        # ── 3. Achromatic detection first (priority order) ───────────────────────
        # Black:  low brightness, any saturation
        black_mask = valid & (V <= 50)
        # Gray:   moderate brightness, very low saturation
        gray_mask = valid & (V > 50) & (V <= 200) & (S < 30)
        # Silver: moderate-high brightness, slight saturation (metallic sheen)
        silver_mask = valid & (V > 100) & (V <= 220) & (S >= 15) & (S < 55)
        # White:  high brightness, very low saturation
        white_mask = valid & (V > 200) & (S < 40)

        black_ratio = np.count_nonzero(black_mask) / total
        gray_ratio = np.count_nonzero(gray_mask) / total
        silver_ratio = np.count_nonzero(silver_mask) / total
        white_ratio = np.count_nonzero(white_mask) / total

        # ── 4. Chromatic color ranges (H-based, only on valid & saturated pixels) ─
        chromatic_mask = valid & (S >= 60)

        color_h_ranges = {
            "Red": [((0, 10), True), ((165, 180), True)],  # wraps around 0
            "Orange": [((10, 25), False)],
            "Yellow": [((25, 35), False)],
            "Green": [((35, 85), False)],
            "Blue": [((85, 130), False)],
            "Purple": [((130, 155), False)],
            "Pink": [((155, 165), False)],
        }

        chromatic_counts = {}
        for color_name, h_ranges in color_h_ranges.items():
            mask = np.zeros(H.shape, dtype=bool)
            for (h_lo, h_hi), _ in h_ranges:
                mask |= (H >= h_lo) & (H <= h_hi)
            mask &= chromatic_mask
            chromatic_counts[color_name] = np.count_nonzero(mask)

        best_chromatic = max(chromatic_counts, key=chromatic_counts.get)
        best_chromatic_ratio = chromatic_counts[best_chromatic] / total

        # ── 5. Decision: chromatic wins only if it's clearly dominant ────────────
        CHROMATIC_THRESHOLD = 0.20  # at least 20% of valid pixels

        if best_chromatic_ratio >= CHROMATIC_THRESHOLD:
            return best_chromatic

        # ── 6. Achromatic decision (priority: Black > White > Silver > Gray) ──────
        achromatic = {
            "Black": black_ratio,
            "White": white_ratio,
            "Silver": silver_ratio,
            "Gray": gray_ratio,
        }

        # Require a minimum ratio to avoid noise
        MIN_ACHROMATIC = 0.15
        dominant = max(achromatic, key=achromatic.get)

        if achromatic[dominant] >= MIN_ACHROMATIC:
            return dominant

        return "Unknown"

    def get_embedding(self,img):
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        img = transform(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feat = self.model(img)
        feat = feat.cpu().numpy()[0]
        feat = feat / np.linalg.norm(feat)
        return feat

    def get_car_details(self):
        try:
            segmented_car = self.crop_car_with_mask(self.image)
            color = self.detect_car_color(segmented_car)
            embeddings = self.get_embedding(segmented_car)
            return color, embeddings
        except Exception as e:
            print(f"Error getting car details: {e}")
            # Return default values
            return "Unknown", np.zeros(2048)  # Adjust 2048 to match your ResNet output size





