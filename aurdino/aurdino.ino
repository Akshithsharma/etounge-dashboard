// Pin mapping
int ldrAnalogPin = A0;   // LDR analog output
int ldrDigitalPin = 2;   // LDR digital output (D0)
int phPin        = A1;   // Soil pH sensor analog output

void setup() {
  Serial.begin(9600);
  pinMode(ldrDigitalPin, INPUT);
}

void loop() {
  // Read LDR values
  int ldrAnalog = analogRead(ldrAnalogPin);     // 0-1023
  int ldrDigital = digitalRead(ldrDigitalPin); // 0 or 1

  // Convert analog LDR to voltage
  float ldrVoltage = ldrAnalog * (5.0 / 1023.0);

  // Read pH sensor
  int phRaw = analogRead(phPin);
  float phVoltage = phRaw * (5.0 / 1023.0);

  // Rough conversion (adjust after calibration with buffer solutions)
  float phValue = 3.5 * phVoltage;  

  // Send JSON to Serial
  Serial.print("{\"LDR_Analog\":");
  Serial.print(ldrVoltage, 2);
  Serial.print(",\"LDR_Digital\":");
  Serial.print(ldrDigital);
  Serial.print(",\"pH\":");
  Serial.print(phValue, 2);
  Serial.println("}");

  delay(1000); // send every 1 second
}
