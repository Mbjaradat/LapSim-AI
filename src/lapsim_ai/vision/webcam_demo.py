"""Minimal two-hand webcam preview. Run directly; Q or Esc exits."""

from pathlib import Path
import time
import sys
import argparse
import json
import socket
import threading
from dataclasses import asdict

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

if __package__:
    from .hand_state import extract_hand_state
    from .stabilization import HandStabilizer
else:
    from hand_state import extract_hand_state
    from stabilization import HandStabilizer
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lapsim_ai.control.hand_mapping import HandMapper, MappingSettings

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


def main(bridge=None):
    if not MODEL.is_file():
        raise FileNotFoundError(f"Official MediaPipe model missing: {MODEL}")
    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(MODEL)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
    )
    camera = None
    stabilizer = HandStabilizer()
    selected = "Right"
    print("1: select Left; 2: select Right. Hold each pose BEFORE pressing its key:")
    print("N: neutral wrist; O: open pinch; C: closed pinch (30 consecutive samples each).")
    print("R: reset selected hand including calibration. Q/Esc: quit.")
    print("N: comfortable hand distance, palm toward camera. Move closer: retract; farther: insert.")
    print("Small wrist travel: yaw/pitch. Tilt knuckle line clockwise/counter-clockwise: roll.")
    try:
        with vision.HandLandmarker.create_from_options(options) as detector:
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                raise RuntimeError("Cannot open default webcam (index 0).")
            timestamp = -1
            while True:
                started = time.monotonic()
                if bridge and bridge.stopped.is_set():
                    break
                ok, frame = camera.read()
                if not ok:
                    raise RuntimeError("Could not read a frame from the webcam.")
                capture_time = time.perf_counter()  # Same QPC clock in Python 3.12 and Blender 3.13.
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                timestamp = max(timestamp + 1, time.monotonic_ns() // 1_000_000)
                result = detector.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp)
                height, width = frame.shape[:2]
                raw_states = []
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
                        mirrored_input=True, image_aspect=width / height)
                    if state is not None:
                        raw_states.append(state)
                stable = stabilizer.update(raw_states, timestamp / 1000)
                mapper = HandMapper(MappingSettings(image_aspect=width / height))
                commands = {side.upper(): mapper.map(state) for side, state in stable.items()}
                if bridge:
                    bridge.send(commands, stable, capture_time)
                debug_lines = []
                for state in stable.values():
                    wrist = (f"{state.wrist[0]:.2f},{state.wrist[1]:.2f}"
                             if state.wrist is not None else "--")
                    pinch = f"{state.normalized_pinch:.2f}" if state.normalized_pinch is not None else "--"
                    tracking = "tracked" if state.tracked else ("lost" if state.available else "unavailable")
                    debug_lines.append(f"{state.handedness}: {tracking} | {state.status}")
                    command = mapper.map(state)
                    if command.valid:
                        debug_lines.append(f"yaw {command.yaw:+.2f} pitch {command.pitch:+.2f} depth {command.insertion:+.2f}")
                        debug_lines.append(f"roll {command.rotation:+.2f} jaw {command.jaw:.2f}")
                    else:
                        debug_lines.append(f"command invalid | wrist {wrist} | pinch {pinch}")
                debug_lines.append(f"Selected {selected} | 1:Left 2:Right | N:neutral O:open C:closed")
                debug_lines.append("Depth: hand closer=retract, farther=insert | R:reset | Q/Esc:quit")
                # Draw last so neither the feed nor another hand's landmarks hide the text.
                frame = draw_debug_lines(frame, debug_lines)
                cv2.imshow("LapSim-AI hand detection - Q / Esc to exit", frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    break
                if key in (ord("1"), ord("2")):
                    selected = "Left" if key == ord("1") else "Right"
                elif chr(key).lower() in ("n", "o", "c"):
                    stabilizer.calibrate(selected, {"n": "neutral", "o": "open", "c": "closed"}[chr(key).lower()])
                elif chr(key).lower() == "r":
                    stabilizer.reset(selected)
                if bridge:
                    bridge.stopped.wait(max(0, 1 / 30 - (time.monotonic() - started)))
    finally:
        if camera is not None:
            camera.release()
        cv2.destroyAllWindows()


class PreviewBridge:
    """Only plain data leaves this process. EOF also detects parent termination."""
    def __init__(self, port, token):
        self.address = ("127.0.0.1", port)
        self.token = token
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stopped = threading.Event()
        threading.Thread(target=self._watch_parent, daemon=True).start()

    def _watch_parent(self):
        sys.stdin.buffer.read(1)
        self.stopped.set()

    def send(self, commands, states, timestamp):
        packet = dict(token=self.token, time=timestamp,
                      hands={side: asdict(command) for side, command in commands.items()},
                      state={side.upper(): {"calibrated": bool(s.calibration.ready), "tracked": bool(s.tracked)}
                             for side, s in states.items()},
                      status={side.upper(): f"{'tracked' if s.tracked else 'lost'} / {s.status}"
                              for side, s in states.items()})
        self.socket.sendto(json.dumps(packet, allow_nan=False).encode(), self.address)

    def close(self):
        self.stopped.set()
        self.socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bridge-port", type=int)
    parser.add_argument("--bridge-token")
    args = parser.parse_args()
    bridge = PreviewBridge(args.bridge_port, args.bridge_token) if args.bridge_port else None
    try:
        main(bridge)
    finally:
        if bridge:
            bridge.close()
