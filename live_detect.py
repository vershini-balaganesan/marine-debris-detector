"""
MVP Demo: Live webcam waste detection for the marine survey project.

What this does:
- Opens your webcam (or phone camera via IP webcam / DroidCam)
- Runs your trained YOLO26n model on every frame
- Draws bounding boxes + class labels (bottle / plastic / metal / glass / other)
- Optionally POSTs each detection to your FastAPI backend

Usage:
    pip install ultralytics opencv-python requests

    python live_detect.py --weights best.pt
    python live_detect.py --weights best.pt --source 0          # default webcam
    python live_detect.py --weights best.pt --source 1          # second camera
    python live_detect.py --weights best.pt --log-url http://localhost:8000/detections

Press 'q' to quit the demo window.
"""

import argparse
import time
from datetime import datetime, timezone

import cv2
import requests
from ultralytics import YOLO


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--weights", type=str, required=True,
                    help="Path to your trained model, e.g. best.pt")
    p.add_argument("--source", default=0,
                    help="Camera index (0,1,...) or a video/stream URL "
                         "(e.g. http://<phone-ip>:8080/video for IP Webcam app)")
    p.add_argument("--conf", type=float, default=0.4,
                    help="Confidence threshold for showing/logging a detection")
    p.add_argument("--log-url", type=str, default=None,
                    help="FastAPI endpoint to POST detections to, e.g. "
                         "http://localhost:8000/detections. Leave unset to skip logging.")
    p.add_argument("--log-every", type=float, default=2.0,
                    help="Minimum seconds between log POSTs per class, to avoid flooding the backend")
    return p.parse_args()


def main():
    args = parse_args()

    # Camera index passed as string "0" needs to become int for cv2
    source = int(args.source) if str(args.source).isdigit() else args.source

    model = YOLO(args.weights)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera/source: {source}")

    last_logged = {}  # class_name -> last log timestamp, for rate limiting

    print("Demo running. Press 'q' in the video window to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Frame grab failed, stopping.")
            break

        results = model.predict(frame, conf=args.conf, verbose=False)[0]
        annotated = results.plot()  # frame with boxes + labels drawn

        # Optionally log each detected class to the backend, rate-limited
        if args.log_url and results.boxes is not None:
            now = time.time()
            for box in results.boxes:
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                conf = float(box.conf[0])

                if now - last_logged.get(cls_name, 0) < args.log_every:
                    continue
                last_logged[cls_name] = now

                payload = {
                    "class_name": cls_name,
                    "confidence": round(conf, 3),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    requests.post(args.log_url, json=payload, timeout=1)
                except requests.exceptions.RequestException as e:
                    print(f"[warn] Could not reach backend: {e}")

        cv2.imshow("Marine Waste Detection - MVP Demo", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()