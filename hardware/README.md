# Hardware

## Parts list

| Part | Qty | Notes |
|---|---|---|
| Arduino Uno | 1 | Drives the servos, reads the glove |
| Hobby servo | 5 | One per finger, pulls the finger tendon. TODO: servo model |
| Flex sensor | 5 | One per glove finger. TODO: sensor model and length |
| 47 kΩ resistor | 5 | Voltage divider for each flex sensor |
| Glove | 1 | Flex sensors sewn or glued along the back of each finger |
| Robotic hand frame with tendons | 1 | TODO: frame source or design files |
| 5 V to 6 V supply for the servos, at least 3 A | 1 | Do not power five servos from the Uno's 5 V pin |
| Jumper wire or switch | 1 | Mode select on pin 2 |
| USB cable and webcam | 1 each | For vision mode on the PC |

## Pins

| Function | Arduino pin | Notes |
|---|---|---|
| Thumb servo signal | D3 | |
| Index servo signal | D5 | |
| Middle servo signal | D6 | |
| Ring servo signal | D9 | |
| Pinky servo signal | D10 | |
| Thumb flex sensor | A0 | |
| Index flex sensor | A1 | |
| Middle flex sensor | A2 | |
| Ring flex sensor | A3 | |
| Pinky flex sensor | A4 | |
| Mode select | D2 | Open = vision mode, to GND = glove mode |

## Wiring

Servos:

```
Servo supply +5..6 V ---- servo red (x5)
Servo supply GND     ---- servo brown/black (x5) ---- Arduino GND
Arduino D3/D5/D6/D9/D10 ---- servo orange/yellow (signal)
```

The servo supply ground and the Arduino ground must be connected.

Each flex sensor is half of a voltage divider:

```
Arduino 5V ---- flex sensor ----+---- Arduino A0..A4
                                |
                              47 kΩ
                                |
Arduino GND --------------------+
```

A straight sensor has a lower resistance than a bent one, so the analog
reading falls as the finger bends.

## Calibration

1. Set `CALIBRATE` to `1` in `arduino/robotic_hand/robotic_hand.ino`, upload,
   connect pin 2 to GND and open the Serial Monitor at 115200 baud.
2. Hold each finger straight, then fully bent, and note the readings.
3. Write them into `FLEX_STRAIGHT` and `FLEX_BENT`.
4. Set `SERVO_OPEN_DEG` and `SERVO_CLOSED_DEG` so each finger opens and closes
   fully without the servo straining at the end of its travel.
5. Set `CALIBRATE` back to `0` and upload again.
