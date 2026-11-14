# Hand-Tracking Robotic Hand

A robotic hand that copies the finger movements of a human hand. It can follow
the hand in two ways:

- **Vision mode:** a webcam and MediaPipe Hands track the hand on a PC, and the
  PC sends the finger positions to the Arduino over USB.
- **Glove mode:** five flex sensors on a glove are read directly by the Arduino.

Video of the hand: [Dropbox](https://www.dropbox.com/scl/fi/xaq31twtbmii226mrkzmc/Hand-tracking-Robotic-Arm.mp4?rlkey=q7535gngdewxcc4kclbl8yfhm&st=cfkio6oy&dl=0)

## How it works

```
Vision mode:  webcam -> MediaPipe Hands (21 landmarks) -> joint angles -> bend % per finger
                     -> USB serial "thumb,index,middle,ring,pinky" -> Arduino Uno -> 5 servos

Glove mode:   5 flex sensors -> Arduino analog inputs -> bend % per finger -> 5 servos
```

In vision mode the bend of each finger is the sum of its joint angles, taken
from MediaPipe's 3D world landmarks (in metres), so it does not change with the
distance to the camera. The bend is scaled to 0 to 100% between calibrated
"open" and "closed" values and smoothed before it is sent.

Each servo pulls one finger tendon. The Arduino maps 0 to 100% to each servo's
own open and closed angle.

## Hardware

- Arduino Uno
- 5 hobby servos, one per finger
- 5 flex sensors on a glove, with 47 kΩ divider resistors
- External 5 V to 6 V servo supply
- PC with a webcam (vision mode)

Parts list, pin table, wiring and calibration: [hardware/README.md](hardware/README.md).

## Software

- Arduino IDE 2 with the built-in Servo library
- Python 3.9 to 3.12 on the PC, packages in `vision/requirements.txt`

## Install

```bash
git clone https://github.com/Fanuelpeter007/Hand-Tracking-Robotic-Hand.git
cd Hand-Tracking-Robotic-Hand
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r vision/requirements.txt
```

Open `arduino/robotic_hand/robotic_hand.ino` in the Arduino IDE and upload it
to the Uno.

## Usage

Vision mode (leave pin 2 open):

```bash
python vision/hand_tracking.py --port COM3            # Windows
python vision/hand_tracking.py --port /dev/ttyACM0    # Linux
```

Run without `--port` to test the tracking without the hand. Add
`--show-degrees` to see the raw bend of each finger, then adjust
`DEFAULT_OPEN_DEG` and `DEFAULT_CLOSED_DEG` in `vision/hand_geometry.py`.
Press q to quit. The hand opens before the program exits.

Glove mode: connect pin 2 to GND. No PC is needed after upload.

Tests for the finger geometry:

```bash
pip install pytest
python -m pytest tests
```

## Project structure

```
arduino/robotic_hand/   Arduino Uno sketch: servos, flex sensors, serial protocol
hardware/               Parts list, pins, wiring, calibration
tests/                  Unit tests for the finger geometry
vision/                 Webcam hand tracking and serial output
```

## Limitations

- Each finger has one servo, so it bends as a whole. Joints cannot be set
  one at a time, and there is no sideways finger movement.
- Vision mode needs the whole hand in view. Fingers hidden behind the palm
  give poor readings.
- The open and closed values need calibration for each camera, glove and hand.
- There is no force feedback from the robotic hand.

## License

[MIT](LICENSE)
