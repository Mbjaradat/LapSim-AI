"""Minimal two-hand webcam preview. Run directly; Q or Esc exits."""

from pathlib import Path
import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

if __package__:
    from .hand_state import extract_hand_state
else:
    from hand_state import extract_hand_state

MODEL = (Path(__file__).resolve().parents[3] / "assets" / "third_party"
         / "mediapipe_hand_landmarker" / "hand_landmarker.task")
CHAINS = ((0, 1, 2, 3, 4), (0, 5, 6, 7, 8), (5, 9, 10, 11, 12),
          (9, 13, 14, 15, 16), (13, 17, 18, 19, 20), (0, 17))


def draw_debug_lines(frame, lines):
    if not lines:
        return frame
    font, scale = cv2.FONT_HERSHEY_SIMPLEX, .65
    widest = max(cv2.getTextSize(line, font, scale, 2)[0][0] for line in lines)
    scale *= min(1.0, (frame.shape[1] - 24) / max(1, widest))
    (_, text_height), baseline = cv2.getTextSize("Right", font, scale, 2)
    row_height = text_height + baseline + 10
    frame = cv2.rectangle(frame, (0, 0), (frame.shape[1] - 1, len(lines) * row_height + 8),
                          (0, 0, 0), cv2.FILLED)
    for i, line in enumerate(lines):
        frame = cv2.putText(frame, line, (10, 8 + text_height + i * row_height),
                            font, scale, (255, 255, 255), 2, cv2.LINE_AA)
    return frame


def main():
    if not MODEL.is_file():
        raise FileNotFoundError(f"Official MediaPipe model missing: {MODEL}")
    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(MODEL)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
    )
    camera = None
    try:
        with vision.HandLandmarker.create_from_options(options) as detector:
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                raise RuntimeError("Cannot open default webcam (index 0).")
            timestamp = -1
            while True:
                ok, frame = camera.read()
                if not ok:
                    raise RuntimeError("Could not read a frame from the webcam.")
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                timestamp = max(timestamp + 1, time.monotonic_ns() // 1_000_000)
                result = detector.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp)
                height, width = frame.shape[:2]
                debug_lines = []
                for i, landmarks in enumerate(result.hand_landmarks):
                    points = [(int(p.x * width), int(p.y * height)) for p in landmarks]
                    for chain in CHAINS:
                        for a, b in zip(chain, chain[1:]):
                            cv2.line(frame, points[a], points[b], (0, 220, 0), 2)
                    for point in points:
                        cv2.circle(frame, point, 3, (0, 220, 255), -1)
                    categories = result.handedness[i] if i < len(result.handedness) else []
                    state = extract_hand_state(
                        landmarks, categories[0].category_name if categories else None,
                        mirrored_input=True)
                    debug = (f"{state.handedness}  wrist {state.wrist[0]:.2f}, {state.wrist[1]:.2f}"
                             f"  pinch {state.pinch_distance:.3f}" if state else "Hand: identity unavailable")
                    debug_lines.append(debug)
                # Draw last so neither the feed nor another hand's landmarks hide the text.
                frame = draw_debug_lines(frame, debug_lines)
                cv2.imshow("LapSim-AI hand detection - Q / Esc to exit", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
                    break
    finally:
        if camera is not None:
            camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
