"""Guided two-hand webcam preview. Run directly; Q or Esc exits."""

from pathlib import Path
import time
import sys
import argparse
import json
import socket
import threading
import queue
from dataclasses import asdict
from math import isfinite

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
from lapsim_ai.control.public_setup import GuidedSetup, CAMERA_GUIDANCE, home_direction

MODEL = (Path(__file__).resolve().parents[3] / "assets" / "third_party"
         / "mediapipe_hand_landmarker" / "hand_landmarker.task")
CHAINS = ((0, 1, 2, 3, 4), (0, 5, 6, 7, 8), (5, 9, 10, 11, 12),
          (9, 13, 14, 15, 16), (13, 17, 18, 19, 20), (0, 17))


def draw_public_preview(frame, stable, setup, status, runtime):
    """Mirrored secondary preview; guidance never obscures the camera image."""
    frame = cv2.resize(frame, (420, round(frame.shape[0]*420/frame.shape[1])))
    height, width = frame.shape[:2]
    active = runtime.get("state") in ("LIVE", "TRACKING_LOST", "PAUSED", "COMPLETE", "LIVE_COUNTDOWN")
    lines = [runtime.get("message", "") if active else status.message]
    if status.remaining is not None and not active:
        lines.append(str(status.remaining))
    if setup.stage == 'neutral' and status.remaining is None:
        lines.extend(CAMERA_GUIDANCE)
    for side, state in stable.items():
        text = "TRACKED" if state.tracked else "HAND LOST"
        lines.append(side.upper() + " " + text + (" / CALIBRATED" if state.calibration.ready else " / SETUP"))
        if side in setup.home:
            home = setup.home[side]
            center = (int(home[0]*width), int(home[1]*height))
            cv2.ellipse(frame, center, (int(.065*width), int(.065*height)), 0, 0, 360, (220, 190, 80), 1)
            cv2.drawMarker(frame, center, (220, 190, 80), cv2.MARKER_CROSS, 12, 1)
            cv2.putText(frame, side[0] + " HOME", (center[0]+8, center[1]-8),
                        cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1)
            if runtime.get("state") != "LIVE":
                position = state.palm_center if state.tracked else None
                direction = home_direction(position, home)
                lines.append(side.upper() + " " + direction)
                if direction == 'HOME':
                    cv2.circle(frame, center, 4, (100, 220, 120), -1)
                elif position is not None:
                    current = (int(position[0]*width), int(position[1]*height))
                    cv2.arrowedLine(frame, current, center, (220, 190, 80), 2, tipLength=.18)
    lines.append("Fallback in Blender: Space pause | R retry | Esc stop")
    # Guidance below the image leaves landmarks and HOME unobscured.
    rows = []
    for i, line in enumerate(lines):
        scale = 1.2 if line.isdigit() else .55 if i == 0 else .44
        row = ''
        for word in line.split():
            candidate = (row + ' ' + word).strip()
            if row and cv2.getTextSize(candidate, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)[0][0] > width-20:
                rows.append((row, scale))
                row = word
            else:
                row = candidate
        rows.append((row, scale))
    panel = cv2.copyMakeBorder(frame, 0, sum(42 if scale > 1 else 22 for _,scale in rows)+12,
                              0, 0, cv2.BORDER_CONSTANT)
    y = height + 4
    for line, scale in rows:
        y += 42 if scale > 1 else 22
        cv2.putText(panel, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                    scale, (240, 240, 240), 1, cv2.LINE_AA)
    return panel


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
    setup = GuidedSetup()
    runtime = {}
    window = "LapSim - Camera and HOME"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 420, 640)
    print("Guided setup: show both hands, hold neutral, open, then pinch. Q/Esc exits.")
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
                bounds = {}
                for i, landmarks in enumerate(result.hand_landmarks):
                    if len(landmarks) != 21 or not all(isfinite(v) for p in landmarks for v in (p.x, p.y, p.z)):
                        continue
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
                        bounds[state.handedness] = (min(p.x for p in landmarks), min(p.y for p in landmarks),
                                                   max(p.x for p in landmarks), max(p.y for p in landmarks))
                        cv2.putText(frame, state.handedness.upper(), points[0], cv2.FONT_HERSHEY_SIMPLEX,
                                    .5, (255, 255, 255), 1, cv2.LINE_AA)
                if bridge:
                    while not bridge.messages.empty():
                        runtime = bridge.messages.get_nowait()
                        if runtime.get("action") == "recenter":
                            setup.recenter(paused=True, manipulating=False)
                        elif runtime.get("action") == "retry":
                            runtime = {}
                status = setup.update(raw_states, bounds, capture_time, stabilizer)
                stable = stabilizer.update(raw_states, timestamp / 1000)
                mapper = HandMapper(MappingSettings(image_aspect=width / height))
                commands = {side.upper(): mapper.map(state) for side, state in stable.items()}
                if bridge:
                    bridge.send(commands, stable, capture_time, asdict(status))
                panel = draw_public_preview(frame, stable, setup, status, runtime)
                cv2.imshow(window, panel)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    break
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
        self.messages = queue.Queue(maxsize=16)
        threading.Thread(target=self._watch_parent, daemon=True).start()

    def _watch_parent(self):
        for line in sys.stdin.buffer:
            try:
                message = json.loads(line)
                if self.messages.full():
                    self.messages.get_nowait()
                self.messages.put_nowait(message)
            except (ValueError, queue.Empty, queue.Full):
                pass
        self.stopped.set()

    def send(self, commands, states, timestamp, setup=None):
        packet = dict(token=self.token, time=timestamp, setup=setup or {},
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
