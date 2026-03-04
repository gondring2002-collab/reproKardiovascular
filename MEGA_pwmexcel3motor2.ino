int p1 = 0;
int p2 = 0;
int p3 = 0;

String dataString = "";

void setup() {
  Serial.begin(115200);

  pinMode(4, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(13, OUTPUT);
}

void loop() {

  // Tunggu satu baris lengkap dari Python (akhiran \n)
  if (Serial.available()) {

    dataString = Serial.readStringUntil('\n');
    dataString.trim();  // hapus spasi / CR

    int space1 = dataString.indexOf(' ');
    int space2 = dataString.indexOf(' ', space1 + 1);

    if (space1 > 0 && space2 > space1) {

      p1 = dataString.substring(0, space1).toInt();
      p2 = dataString.substring(space1 + 1, space2).toInt();
      p3 = dataString.substring(space2 + 1).toInt();

      p1 = constrain(p1, 0, 255);
      p2 = constrain(p2, 0, 255);
      p3 = constrain(p3, 0, 255);

      analogWrite(4, p1);
      analogWrite(3, p2);
      analogWrite(12, p3);
    }
  }
}
