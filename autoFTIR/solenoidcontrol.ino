int x;
int relay_1 = 1;
int relay_2 = 2;

void setup() {
  pinMode(relay_1, OUTPUT);
  pinMode(relay_2, OUTPUT);
  Serial.begin(115200);
  Serial.setTimeout(1);
}

void  loop() {
  // Vent closed switches to NC poition, vent open switches to NO position
  // HIGH = open state, LOW = close state
  while (!Serial.available());
  x = Serial.readString().toInt();
  if (x==1){
    // open relay 1
    int relayState = digitalRead(relay_1);
    if (relayState == HIGH) {
    Serial.print("Vent Valve already open");
    }else{
    digitalWrite(relay_1,HIGH);
    Serial.print("Vent valve open");
  }
  }
  if (x==2){
    // close relay 1
    int relayState = digitalRead(relay_1);
    if (relayState == LOW) {
    Serial.print("Vent valve already closed");
    }else{
      digitalWrite(relay_1, LOW);
     Serial.print("Vent valve closed"); 
    }
  }
  if (x==3){
    // open relay 2
    int relayState = digitalRead(relay_2);
    if (relayState == HIGH) {
      Serial.print("Relay 2 already open");
    }else{
      digitalWrite(relay_2, HIGH);
      Serial.print("Relay 2 open");
    }
    }
  if (x==4){
    //close relay 2
    int relayState = digitalRead(relay_2);
    if (relayState == LOW) {
      Serial.print("Relay 2 already closed");
    }else{
      digitalWrite(relay_2, LOW);
      Serial.print("Relay 2 closed");
    }
    }
  }

