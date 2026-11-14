/*
 * Robotic hand controller for Arduino Uno.
 *
 * Five servos pull the five finger tendons. The bend of each finger comes from
 * one of two sources, chosen with the mode jumper on pin 2:
 *
 *   Pin 2 open (HIGH)  -> vision mode: the PC sends finger bends over USB serial
 *   Pin 2 to GND (LOW) -> glove mode:  five flex sensors on A0..A4
 *
 * Serial protocol (vision mode), 115200 baud, one line per update:
 *   "<thumb>,<index>,<middle>,<ring>,<pinky>\n"
 * Each value is the finger bend in percent: 0 = straight, 100 = fully bent.
 *
 * Calibrate the servo angles and flex sensor readings in the tables below.
 * Set CALIBRATE to 1 to print raw flex sensor readings in glove mode.
 */
#include <Servo.h>
#include <stdlib.h>
#include <string.h>

#define CALIBRATE 0

const uint8_t NUM_FINGERS = 5;

// Order everywhere: thumb, index, middle, ring, pinky.
const uint8_t SERVO_PINS[NUM_FINGERS] = {3, 5, 6, 9, 10};
const uint8_t FLEX_PINS[NUM_FINGERS]  = {A0, A1, A2, A3, A4};
const uint8_t MODE_PIN = 2;

// Servo angle in degrees for a straight and a fully bent finger.
// Swap the values for a finger whose servo turns the other way.
const int SERVO_OPEN_DEG[NUM_FINGERS]   = {0, 0, 0, 0, 0};
const int SERVO_CLOSED_DEG[NUM_FINGERS] = {180, 180, 180, 180, 180};

// Flex sensor ADC readings (0..1023) for a straight and a fully bent finger.
// With a 47 kOhm resistor to GND, a straight sensor reads higher than a bent one.
const int FLEX_STRAIGHT[NUM_FINGERS] = {670, 670, 670, 670, 670};
const int FLEX_BENT[NUM_FINGERS]     = {330, 330, 330, 330, 330};

const unsigned long BAUD = 115200;
const unsigned long GLOVE_PERIOD_MS = 20;   // 50 Hz glove update

Servo servos[NUM_FINGERS];
char line[32];
uint8_t lineLen = 0;

// Move one finger to a bend between 0 (straight) and 100 (fully bent) percent.
void setFinger(uint8_t i, int bendPercent) {
  bendPercent = constrain(bendPercent, 0, 100);
  servos[i].write(map(bendPercent, 0, 100, SERVO_OPEN_DEG[i], SERVO_CLOSED_DEG[i]));
}

// Parse "a,b,c,d,e" into five bend values. Returns true if all five are present.
bool parseLine(char *s, int out[NUM_FINGERS]) {
  uint8_t n = 0;
  char *tok = strtok(s, ",");
  while (tok != NULL && n < NUM_FINGERS) {
    out[n++] = atoi(tok);
    tok = strtok(NULL, ",");
  }
  return n == NUM_FINGERS && tok == NULL;
}

// Read serial characters; apply a complete line when one arrives.
void handleSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\r') {
      continue;
    }
    if (c == '\n') {
      line[lineLen] = '\0';
      int bends[NUM_FINGERS];
      if (lineLen > 0 && parseLine(line, bends)) {
        for (uint8_t i = 0; i < NUM_FINGERS; i++) {
          setFinger(i, bends[i]);
        }
      }
      lineLen = 0;
    } else if (lineLen < sizeof(line) - 1) {
      line[lineLen++] = c;
    } else {
      lineLen = 0;  // line too long: drop it
    }
  }
}

// Read the flex sensors and copy the glove's finger bends to the hand.
void handleGlove() {
  static unsigned long last = 0;
  unsigned long now = millis();
  if (now - last < GLOVE_PERIOD_MS) {
    return;
  }
  last = now;

  for (uint8_t i = 0; i < NUM_FINGERS; i++) {
    int raw = analogRead(FLEX_PINS[i]);
    setFinger(i, map(raw, FLEX_STRAIGHT[i], FLEX_BENT[i], 0, 100));
#if CALIBRATE
    Serial.print(raw);
    Serial.print(i < NUM_FINGERS - 1 ? '\t' : '\n');
#endif
  }
}

void setup() {
  Serial.begin(BAUD);
  pinMode(MODE_PIN, INPUT_PULLUP);
  for (uint8_t i = 0; i < NUM_FINGERS; i++) {
    servos[i].attach(SERVO_PINS[i]);
    setFinger(i, 0);  // start with an open hand
  }
}

void loop() {
  if (digitalRead(MODE_PIN) == LOW) {
    handleGlove();
  } else {
    handleSerial();
  }
}
