# ml/detector.py
"""
YOLO26n inference module.
Loads a trained model ONCE and exposes run_inference() for the rest of the app.
This module does NOT train or fine-tune anything — training already happened
elsewhere and produced best.pt.
"""

import os
from datetime import datetime, timezone
from ultralytics import YOLO

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "best.onnx")

_model = None  # cached model instance, loaded lazily


def load_model():
    """Load the YOLO model once and cache it. Raises a clear error if missing."""
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PATH}. "
                "Place your trained best.pt inside the 'model/' folder."
            )
        _model = YOLO(MODEL_PATH)
    return _model


def run_inference(image_path: str, conf_threshold: float = 0.25):
    """
    Run YOLO inference on a single image.

    Args:
        image_path: path to a JPG/JPEG/PNG image on disk.
        conf_threshold: minimum confidence to keep a detection (configurable).

    Returns:
        dict with:
            image_name, image_path, timestamp,
            detections: list of {debris_type, confidence, bbox: [x1,y1,x2,y2]}
            annotated_image_path: path to the saved image with boxes drawn
    """
    model = load_model()

    results = model.predict(
        source=image_path,
        conf=conf_threshold,
        verbose=False,
    )
    result = results[0]  # single image in, single result out

    detections = []
    for box in result.boxes:
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]

        detections.append({
            "debris_type": class_name,
            "confidence": round(confidence, 4),
            "bbox": [x1, y1, x2, y2],
        })

    # Save the annotated image (boxes drawn by Ultralytics) to outputs/
    outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    image_name = os.path.basename(image_path)
    annotated_path = os.path.join(outputs_dir, f"annotated_{image_name}")

    annotated_array = result.plot()  # numpy array (BGR) with boxes drawn
    import cv2
    cv2.imwrite(annotated_path, annotated_array)

    return {
        "image_name": image_name,
        "image_path": image_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detections": detections,
        "annotated_image_path": annotated_path,
    }