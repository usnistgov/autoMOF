/* 
 * Arduino MKR Zero - Solenoid Control via Python vacuumPy script
 */
 // Valve 1 is connected to relay 1. This is the output valve.
 // VAlve 2 is connected to relay 2. This is the vacuum switching valve.
const int OUTPUT_VALVE_1 = 1; 
const int INPUT_VALVE_2 = 2; 
const int PRESSURE_SWITCH_PIN = 4;


const bool SWITCH_IS_NORMALLY_OPEN = false;  // Pressure switch
const int VALVE_CLOSED = LOW;
const int VALVE_OPEN = HIGH;

void setup() {
  Serial.begin(9600);
  pinMode(OUTPUT_VALVE_1, OUTPUT);
  pinMode(INPUT_VALVE_2, OUTPUT);
  digitalWrite(OUTPUT_VALVE_1, VALVE_CLOSED);
  digitalWrite(INPUT_VALVE_2, VALVE_CLOSED);
  pinMode(PRESSURE_SWITCH_PIN, INPUT_PULLUP);
}

void loop() {
  handlePythonCommands();
  //checkPressureSwitch();
  
  if (digitalRead(PRESSURE_SWITCH_PIN) == LOW) {
    Serial.println("PRESSURE_TRIGGERED");
    Serial.println(digitalRead(PRESSURE_SWITCH_PIN));
  }
}

void handlePythonCommands() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == '1') { // OPEN both valves
      digitalWrite(OUTPUT_VALVE_1, VALVE_OPEN);
      digitalWrite(INPUT_VALVE_2, VALVE_OPEN); 
      Serial.println("MANUAL_OPEN_BOTH");
    } 
    else if (cmd == '0') { // CLOSE both valves
      digitalWrite(OUTPUT_VALVE_1, VALVE_CLOSED);
      digitalWrite(INPUT_VALVE_2, VALVE_CLOSED);

      Serial.println("MANUAL_CLOSE_BOTH");
    }
    else if (cmd == 'T') { // TOGGLE both valves
      int newState = (digitalRead(OUTPUT_VALVE_1) == VALVE_OPEN) ? VALVE_CLOSED : VALVE_OPEN;
      digitalWrite(OUTPUT_VALVE_1, newState);
      digitalWrite(INPuT_VALVE_2, newState);
      Serial.println(newState == VALVE_OPEN ? "TOGGLE_OPEN_BOTH" : "TOGGLE_CLOSE_BOTH");
    }
    // Individual Commands
    else if (cmd == 'A') { // Valve 1 Open
      digitalWrite(OUTPUT_VALVE_1, VALVE_OPEN);
      Serial.println("V1_OUTPUT_OPEN");
    }
    else if (cmd == 'a') { // Valve 1 Close
      digitalWrite(OUTPUT_VALVE_1, VALVE_CLOSED);
      Serial.println("V1_OUTPUT_CLOSED");
    }
    else if (cmd == 'B') { // Valve 2 Open
      digitalWrite(INPUT_VALVE_2, VALVE_OPEN);
      Serial.println("V2_INPUT_VACUUM);
    }
    else if (cmd == 'b') { // Valve 2 Close
      digitalWrite(INPUT_VALVE_2, VALVE_CLOSED);
      Serial.println("V2_INPUT_GAS");
    }
  }
}

//void checkPressureSwitch() {
//  bool switchState = digitalRead(PRESSURE_SWITCH_PIN);
//  bool isTriggered = SWITCH_IS_NORMALLY_OPEN ? (switchState == HIGH) : (switchState == LOW)

//  if (isTriggered) {
//    Serial.println("PRESSURE_TRIGGERED)");
//  } else {
//    Serial.println("PRESSURE_OK");
//    delay(100);
//  }
//}