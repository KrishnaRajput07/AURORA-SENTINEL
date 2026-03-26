import cv2
import numpy as np
import os
from ultralytics import YOLO
import torch
from concurrent.futures import ThreadPoolExecutor
import time

# ---------------------------------------------------------------------------
# Model file paths — resolved relative to this script's directory so the
# detector works regardless of the current working directory.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))

def _is_lfs_pointer(path):
    """
    Best-effort check for a Git-LFS pointer file masquerading as a .pt weight.
    """
    if not os.path.isfile(path):
        return False
    try:
        if os.path.getsize(path) > 1024:
            return False
        with open(path, 'rb') as fh:
            head = fh.read(256)
        return head.startswith(b"version ") and b"git-lfs.github.com/spec/v1" in head
    except OSError:
        return False


def _candidate_paths(model_name):
    return [
        os.path.join(_HERE, model_name),
        os.path.join(_PROJECT_ROOT, model_name),
    ]


def _resolve_model_path(model_names):
    """
    Resolve model path by checking script dir then project root.
    Accepts a single model name or a list of fallback names.
    Prefers non-LFS files when multiple candidates exist.
    """
    if isinstance(model_names, str):
        model_names = [model_names]

    first_existing = None
    for model_name in model_names:
        for path in _candidate_paths(model_name):
            if os.path.isfile(path):
                if first_existing is None:
                    first_existing = path
                if not _is_lfs_pointer(path):
                    return path

    if first_existing:
        return first_existing

    # Fallback to the first expected location for clearer error reporting.
    return _candidate_paths(model_names[0])[0]

_MODEL_PATHS = {
    'object':  _resolve_model_path('yolov8n.pt'),        # COCO 80-class general detector
    'pose':    _resolve_model_path('yolov8n-pose.pt'),   # Keypoint / pose estimator
    'fire':    _resolve_model_path(['fir.pt', 'fire.pt']),           # Custom fire & smoke detector
    # vehicle.pt / wepon.pt can be Git-LFS pointer stubs (not real weights).
    # These are loaded only when real binary weights are present.
    'vehicle': _resolve_model_path(['vehicle.pt', 'vehicles.pt']),   # Custom vehicle detector
    'weapon':  _resolve_model_path(['weapon.pt', 'wepon.pt', 'weapons.pt', 'gun.pt']),  # Custom weapon detector
}

# ---------------------------------------------------------------------------
# fir.pt was trained with Chinese class labels: {0: '火' (fire), 1: '烟' (smoke)}
# We remap them to English for downstream logic.
# ---------------------------------------------------------------------------
_FIRE_CLASS_REMAP = {0: 'fire', 1: 'smoke'}

# ---------------------------------------------------------------------------
# COCO class ids that are treated as critical objects by the general detector.
# ---------------------------------------------------------------------------
_COCO_CRITICAL = {
    0:  'person',
    24: 'backpack',
    26: 'handbag',
    28: 'suitcase',
    34: 'baseball bat',
    43: 'knife',
    76: 'scissors',
}

# COCO ids that are treated as weapons (subset of _COCO_CRITICAL).
_COCO_WEAPON_IDS = {34, 43, 76}

# Vehicle-related COCO class ids used as a fallback when vehicle.pt is unavailable.
_COCO_VEHICLE_IDS = {
    1:  'bicycle',
    2:  'car',
    3:  'motorcycle',
    5:  'bus',
    7:  'truck',
}


def _try_load_model(path: str, tag: str, device: str):
    """
    Attempt to load a YOLO model from *path*.
    Returns the loaded model on success, or None on failure (e.g. LFS stub).
    """
    if not os.path.isfile(path):
        print(f"[WARN] {tag} model not found at '{path}' — skipping.")
        return None
    if _is_lfs_pointer(path):
        print(
            f"[WARN] {tag} model at '{path}' is a Git-LFS pointer, not real weights. "
            "Run 'git lfs pull' (or copy the actual .pt file) and restart."
        )
        return None
    try:
        model = YOLO(path)
        model.to(device)
        print(f"[INFO] Loaded {tag} model from '{os.path.basename(path)}'.")
        return model
    except Exception as exc:
        print(f"[WARN] Could not load {tag} model ('{path}'): {exc}")
        return None


class UnifiedDetector:
    """
    Combines object detection, pose estimation, fire/smoke detection,
    vehicle detection and weapon detection with SimpleTracker.

    Model inventory
    ---------------
    yolov8n.pt       — general COCO detector  (persons, bags, knives, …)
    yolov8n-pose.pt  — keypoint / pose model
    fir.pt           — custom fire & smoke detector  (classes: fire, smoke)
    vehicle.pt       — custom vehicle detector       (Git-LFS stub — loads if available)
    wepon.pt         — custom weapon detector        (Git-LFS stub — loads if available)
    """

    def __init__(self, device=None):
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        if self.device == 'cuda':
            torch.backends.cudnn.benchmark = True

        print(f"Initializing UnifiedDetector on {self.device}...")

        # ── Core models (always required) ──────────────────────────────────
        print("Loading models...")
        self.object_model  = YOLO(_MODEL_PATHS['object'])
        self.object_model.to(self.device)

        self.pose_model    = YOLO(_MODEL_PATHS['pose'])
        self.pose_model.to(self.device)

        # ── Specialist models (optional — degrade gracefully if LFS stubs) ─
        self.fire_model    = _try_load_model(_MODEL_PATHS['fire'],    'fire',    self.device)
        self.vehicle_model = _try_load_model(_MODEL_PATHS['vehicle'], 'vehicle', self.device)
        self.weapon_model  = _try_load_model(_MODEL_PATHS['weapon'],  'weapon',  self.device)

        # COCO class mappings
        self.critical_objects = _COCO_CRITICAL

        # Tracker & thread pool
        self.tracker  = SimpleTracker()
        self.executor = ThreadPoolExecutor(max_workers=3)

        # Always use FP32 for stability (FP16 causes dtype mismatches on some GPUs)
        self.use_half = False
        print("[INFO] Using FP32 (Full Precision) for stability.")

    # ── Internal helpers ────────────────────────────────────────────────────

    def _check_blur(self, frame):
        """Blur detection via Laplacian variance (Innovation #16)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance < 100

    def _calculate_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0]);  yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2]);  yB = min(boxA[3], boxB[3])
        interArea  = max(0, xB - xA) * max(0, yB - yA)
        boxAArea   = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea   = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea + 1e-6)

    @staticmethod
    def _get_center(bbox):
        return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]

    # ── Per-modality detection methods ──────────────────────────────────────

    def detect_objects(self, frame):
        """
        Detect and track critical COCO objects (persons, bags, blunt/bladed
        weapons) using yolov8n.pt + SimpleTracker.
        """
        is_blurry = self._check_blur(frame)

        results = self.object_model.predict(
            frame,
            verbose=False,
            device=self.device,
            classes=list(self.critical_objects.keys()),
            half=self.use_half,
        )[0]

        raw_boxes = []
        if results.boxes is not None:
            for box in results.boxes:
                cls  = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()

                if cls in self.critical_objects and conf > 0.3:
                    raw_boxes.append({
                        'class':      self.critical_objects[cls],
                        'confidence': conf,
                        'bbox':       xyxy.tolist(),
                        'is_blurry':  is_blurry,
                    })

        return self.tracker.update(raw_boxes)

    def detect_poses(self, frame):
        """
        Detect human poses using yolov8n-pose.pt.
        Returns a list of dicts with 'keypoints', 'confidence', and 'bbox'.
        """
        results = self.pose_model(
            frame, verbose=False, device=self.device, half=self.use_half
        )[0]

        poses = []
        if results.keypoints is not None:
            for i, keypoints in enumerate(results.keypoints):
                if hasattr(keypoints, 'xy'):
                    kpts = keypoints.xy[0].cpu().numpy()
                    conf = (
                        keypoints.conf[0].cpu().numpy()
                        if keypoints.conf is not None
                        else np.ones(len(kpts))
                    )
                elif hasattr(keypoints, 'data'):
                    data = keypoints.data[0].cpu().numpy()
                    kpts = data[:, :2]
                    conf = data[:, 2] if data.shape[1] > 2 else np.ones(len(kpts))
                else:
                    continue

                bbox = [0, 0, 0, 0]
                if results.boxes is not None and i < len(results.boxes):
                    bbox = results.boxes[i].xyxy[0].cpu().numpy().tolist()

                poses.append({
                    'keypoints':  kpts.tolist(),
                    'confidence': conf.tolist(),
                    'bbox':       bbox,
                })

        return poses

    def detect_fire(self, frame):
        """
        Detect fire and smoke using fir.pt.

        fir.pt class map  →  {0: '火' (fire),  1: '烟' (smoke)}
        We remap to English: {0: 'fire', 1: 'smoke'}.

        Falls back to an empty list when fir.pt is unavailable.
        """
        if self.fire_model is None:
            return []

        results = self.fire_model.predict(
            frame,
            verbose=False,
            device=self.device,
            conf=0.35,
            half=self.use_half,
        )[0]

        detections = []
        if results.boxes is not None:
            names = results.names or {}
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf   = float(box.conf[0])
                xyxy   = box.xyxy[0].cpu().numpy()
                raw_name = str(names.get(cls_id, '')).strip().lower()

                if raw_name in {'fire', 'flame', 'burning', '火'} or 'fire' in raw_name:
                    label = 'fire'
                elif raw_name in {'smoke', 'fume', '烟'} or 'smoke' in raw_name:
                    label = 'smoke'
                else:
                    label = _FIRE_CLASS_REMAP.get(cls_id, raw_name if raw_name else f'fire_cls_{cls_id}')

                detections.append({
                    'class':      label,           # 'fire' or 'smoke'
                    'confidence': conf,
                    'bbox':       xyxy.tolist(),
                })

        return detections

    def detect_vehicles(self, frame):
        """
        Detect vehicles using vehicle.pt when available.

        vehicle.pt is a custom model (Git-LFS stub in the current upload).
        When the real weights are present, its predictions are used directly.
        When unavailable, falls back to COCO vehicle classes from yolov8n.pt
        (bicycle, car, motorcycle, bus, truck).
        """
        if self.vehicle_model is not None:
            # Use the specialist model — trust its own class names
            results = self.vehicle_model.predict(
                frame,
                verbose=False,
                device=self.device,
                conf=0.35,
                half=self.use_half,
            )[0]

            vehicles = []
            if results.boxes is not None:
                names = results.names
                for box in results.boxes:
                    cls_id   = int(box.cls[0])
                    cls_name = names.get(cls_id, f'vehicle_{cls_id}').lower()
                    conf     = float(box.conf[0])
                    xyxy     = box.xyxy[0].cpu().numpy()
                    vehicles.append({
                        'class':      cls_name,
                        'confidence': conf,
                        'bbox':       xyxy.tolist(),
                    })
            return vehicles

        # ── Fallback: COCO vehicle classes from the general detector ───────
        results = self.object_model.predict(
            frame,
            verbose=False,
            device=self.device,
            classes=list(_COCO_VEHICLE_IDS.keys()),
            conf=0.35,
            half=self.use_half,
        )[0]

        vehicles = []
        if results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf   = float(box.conf[0])
                xyxy   = box.xyxy[0].cpu().numpy()
                if cls_id in _COCO_VEHICLE_IDS:
                    vehicles.append({
                        'class':      _COCO_VEHICLE_IDS[cls_id],
                        'confidence': conf,
                        'bbox':       xyxy.tolist(),
                    })
        return vehicles

    def detect_weapons(self, frame):
        """
        Detect weapons using wepon.pt when available.

        wepon.pt is a custom model (Git-LFS stub in the current upload).
        When the real weights are present, predictions are filtered to
        explicitly weapon-related class names.
        When unavailable, falls back to COCO weapon classes (knife, baseball
        bat, scissors) detected by yolov8n.pt.
        """
        if self.weapon_model is not None:
            results = self.weapon_model.predict(
                frame,
                verbose=False,
                device=self.device,
                conf=0.40,
                half=self.use_half,
            )[0]

            weapons = []
            if results.boxes is not None:
                names = results.names
                for box in results.boxes:
                    cls_id   = int(box.cls[0])
                    cls_name = names.get(cls_id, 'unknown').lower()
                    conf     = float(box.conf[0])
                    xyxy     = box.xyxy[0].cpu().numpy()

                    is_weapon = any(
                        w in cls_name
                        for w in ['gun', 'weapon', 'firearm', 'handgun', 'pistol', 'rifle', 'shotgun', 'knife',
                                  'machete', 'sword', 'bat', 'scissors']
                    )

                    if is_weapon and conf > 0.45:
                        weapons.append({
                            'class':     'weapon',
                            'sub_class': cls_name if cls_name != 'unknown' else 'unidentified_threat',
                            'confidence': conf,
                            'bbox':       xyxy.tolist(),
                        })
            return weapons

        # ── Fallback: COCO weapon classes from the general detector ────────
        results = self.object_model.predict(
            frame,
            verbose=False,
            device=self.device,
            classes=list(_COCO_WEAPON_IDS),
            conf=0.40,
            half=self.use_half,
        )[0]

        weapons = []
        if results.boxes is not None:
            names = results.names
            for box in results.boxes:
                cls_id   = int(box.cls[0])
                cls_name = names.get(cls_id, 'unknown').lower()
                conf     = float(box.conf[0])
                xyxy     = box.xyxy[0].cpu().numpy()
                if cls_id in _COCO_WEAPON_IDS and conf > 0.40:
                    weapons.append({
                        'class':      'weapon',
                        'sub_class':  cls_name,
                        'confidence': conf,
                        'bbox':       xyxy.tolist(),
                    })
        return weapons

    # ── Pose ↔ track assignment ─────────────────────────────────────────────

    def _assign_tracks_to_poses(self, objects, poses):
        """
        Match detected poses to tracked person objects via IoU.
        Adds 'track_id' to each pose dict when a good match is found.
        """
        if not objects or not poses:
            return

        persons = [o for o in objects if o['class'] == 'person' and 'track_id' in o]

        for pose in poses:
            if 'bbox' not in pose or not pose['bbox']:
                continue

            best_match, max_iou = None, 0.0
            for person in persons:
                iou = self._calculate_iou(pose['bbox'], person['bbox'])
                if iou > max_iou:
                    max_iou = iou
                    best_match = person

            if best_match and max_iou > 0.5:
                pose['track_id'] = best_match['track_id']

    # ── Main pipeline ───────────────────────────────────────────────────────

    def process_frame(self, frame):
        """
        Complete sequential detection pipeline.

        Returns
        -------
        dict with keys:
            objects   — tracked COCO critical objects (persons, bags, …)
            poses     — human pose keypoints (+ track_id when matched)
            weapons   — weapon detections  (wepon.pt or COCO fallback)
            vehicles  — vehicle detections (vehicle.pt or COCO fallback)
            fire      — fire / smoke detections (fir.pt)
            timestamp — Unix timestamp (float)
        """
        objects  = self.detect_objects(frame)
        poses    = self.detect_poses(frame)
        weapons  = self.detect_weapons(frame)
        vehicles = self.detect_vehicles(frame)
        fire     = self.detect_fire(frame)

        self._assign_tracks_to_poses(objects, poses)

        return {
            'objects':   objects,
            'poses':     poses,
            'weapons':   weapons,
            'vehicles':  vehicles,
            'fire':      fire,
            'timestamp': time.time(),
        }

    def warmup(self):
        """Run dummy frames through models to initialise CUDA/weights."""
        print("Warming up models...")
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        # One pass is enough to initialize kernels while keeping startup latency manageable.
        self.process_frame(dummy)
        print("Model warmup complete.")


# ---------------------------------------------------------------------------
# Simple centroid + IoU tracker (no ByteTrack dependency)
# ---------------------------------------------------------------------------

class SimpleTracker:
    def __init__(self):
        self.tracks    = {}   # track_id -> bbox
        self.next_id   = 0
        self.max_age   = 30
        self.track_age = {}   # track_id -> frames since last match

    def update(self, detections):
        if not detections:
            self._increment_ages()
            return []

        for det in detections:
            det['center']   = self._get_center(det['bbox'])
            det['track_id'] = -1

        matched_tracks = set()

        for det in detections:
            best_iou, best_tid = 0, -1

            for tid, track_box in self.tracks.items():
                if tid in matched_tracks:
                    continue
                iou          = self._calculate_iou(det['bbox'], track_box)
                track_center = self._get_center(track_box)
                dist         = np.linalg.norm(
                    np.array(det['center']) - np.array(track_center)
                )
                h = track_box[3] - track_box[1]

                if (iou > 0.3 and iou > best_iou) or (iou <= 0.3 and dist < h * 0.8):
                    best_iou = iou if iou > 0.3 else 0.31
                    best_tid = tid

            if best_tid != -1:
                det['track_id']        = best_tid
                self.tracks[best_tid]  = det['bbox']
                self.track_age[best_tid] = 0
                matched_tracks.add(best_tid)
            else:
                det['track_id']              = self.next_id
                self.tracks[self.next_id]    = det['bbox']
                self.track_age[self.next_id] = 0
                self.next_id += 1

        for tid in list(self.tracks.keys()):
            if tid not in matched_tracks:
                self.track_age[tid] += 1
                if self.track_age[tid] > self.max_age:
                    del self.tracks[tid]
                    del self.track_age[tid]

        return detections

    def _increment_ages(self):
        for tid in list(self.tracks.keys()):
            self.track_age[tid] += 1
            if self.track_age[tid] > self.max_age:
                del self.tracks[tid]
                del self.track_age[tid]

    @staticmethod
    def _get_center(bbox):
        return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]

    @staticmethod
    def _calculate_iou(boxA, boxB):
        xA = max(boxA[0], boxB[0]);  yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2]);  yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea  = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea  = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea + 1e-6)


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    detector = UnifiedDetector()

    print("Running test on dummy frame...")
    dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    results = detector.process_frame(dummy_frame)

    print(
        f"Test Successful: "
        f"{len(results['objects'])} objects, "
        f"{len(results['poses'])} people, "
        f"{len(results['weapons'])} weapons, "
        f"{len(results['vehicles'])} vehicles, "
        f"{len(results['fire'])} fire/smoke detections."
    )
