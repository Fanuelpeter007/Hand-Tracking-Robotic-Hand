"""Track a hand with a webcam and drive the robotic hand over USB serial.

MediaPipe Hands finds 21 landmarks on the hand. The bend of each finger is
computed from the joint angles, smoothed, and sent to the Arduino as five
percentages (see arduino/robotic_hand/robotic_hand.ino).

Usage:
    python vision/hand_tracking.py                      # preview only
    python vision/hand_tracking.py --port COM3          # Windows
    python vision/hand_tracking.py --port /dev/ttyACM0  # Linux
    python vision/hand_tracking.py --show-degrees       # show raw bend for calibration

Press q in the preview window to quit.
"""

import argparse
import time

import cv2
import mediapipe as mp
import numpy as np

from hand_geometry import (DEFAULT_CLOSED_DEG, DEFAULT_OPEN_DEG, FINGER_NAMES,
                           encode_command, finger_bend_deg, hand_bends)


def parse_args():
    """Read command line options."""
    p = argparse.ArgumentParser(description="Webcam hand tracking for the robotic hand.")
    p.add_argument("--port", help="Arduino serial port, for example COM3 or /dev/ttyACM0. "
                                  "Leave out to run without the hand.")
    p.add_argument("--baud", type=int, default=115200, help="Serial baud rate (default: 115200)")
    p.add_argument("--camera", type=int, default=0, help="Webcam index (default: 0)")
    p.add_argument("--rate", type=float, default=30.0, help="Commands per second (default: 30)")
    p.add_argument("--smoothing", type=float, default=0.5,
                   help="Weight of the newest frame, 0..1 (default: 0.5, 1 = no smoothing)")
    p.add_argument("--show-degrees", action="store_true",
                   help="Show each finger's raw bend in degrees, for calibration")
    return p.parse_args()


def open_serial(port, baud):
    """Open the Arduino port and wait for the board to reset."""
    import serial  # imported here so preview mode works without pyserial

    ser = serial.Serial(port, baud, timeout=0)
    time.sleep(2.0)  # the Uno resets when the port opens
    return ser


def draw_overlay(frame, bends, degrees=None):
    """Write each finger's bend on the preview frame."""
    for i, name in enumerate(FINGER_NAMES):
        text = f"{name:>6}: {bends[i]:3d}%"
        if degrees is not None:
            text += f"  ({degrees[i]:5.1f} deg)"
        cv2.putText(frame, text, (10, 30 + 28 * i), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)


def main():
    args = parse_args()
    ser = open_serial(args.port, args.baud) if args.port else None

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print("Error: cannot open the webcam.")
        return 1

    mp_hands = mp.solutions.hands
    drawer = mp.solutions.drawing_utils
    smoothed = None
    period = 1.0 / args.rate
    last_send = 0.0

    try:
        with mp_hands.Hands(max_num_hands=1, model_complexity=1,
                            min_detection_confidence=0.6, min_tracking_confidence=0.5) as hands:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("Error: cannot read a frame from the webcam.")
                    break

                frame = cv2.flip(frame, 1)  # mirror view, easier to follow
                result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                if result.multi_hand_world_landmarks:
                    # World landmarks are in metres, so joint angles do not
                    # depend on the distance to the camera.
                    world = result.multi_hand_world_landmarks[0].landmark
                    pts = np.array([[p.x, p.y, p.z] for p in world])

                    bends = np.array(hand_bends(pts, DEFAULT_OPEN_DEG, DEFAULT_CLOSED_DEG), dtype=float)
                    smoothed = bends if smoothed is None else (
                        args.smoothing * bends + (1.0 - args.smoothing) * smoothed)
                    shown = [int(round(b)) for b in smoothed]

                    degrees = [finger_bend_deg(pts, f) for f in FINGER_NAMES] if args.show_degrees else None
                    drawer.draw_landmarks(frame, result.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)
                    draw_overlay(frame, shown, degrees)

                    now = time.monotonic()
                    if ser is not None and now - last_send >= period:
                        ser.write(encode_command(shown))
                        last_send = now

                cv2.imshow("Hand tracking", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        if ser is not None:
            ser.write(encode_command([0, 0, 0, 0, 0]))  # open the hand before exit
            ser.close()
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
