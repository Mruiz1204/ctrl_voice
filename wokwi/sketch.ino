/*
  Control por Voz — Miguel Ruiz
  ESP32 en Wokwi que recibe comandos por MQTT desde la app de Streamlit.

  Pega este código en sketch.ino de tu copia del proyecto:
  https://wokwi.com/projects/377229910598956033

  - LED en el pin 2   -> "enciende las luces" / "apaga las luces"
  - Servo en el pin 13 -> "abre la puerta" (180°) / "cierra la puerta" (90°)
*/

#include <ArduinoJson.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>

// ── Debe coincidir con la app (panel lateral → CONEXIÓN MQTT) ──
const char* ssid        = "Wokwi-GUEST";
const char* password    = "";
const char* mqtt_server = "broker.mqttdashboard.com";
const int   mqtt_port   = 1883;
const char* TOPICO      = "voice_ctrl_miguelruiz";

const int PIN_LED   = 2;
const int PIN_SERVO = 13;

WiFiClient espClient;
PubSubClient client(espClient);
Servo puerta;

void setup_wifi() {
  Serial.print("Conectando a ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
}

void callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.print("JSON inválido: ");
    Serial.println(error.f_str());
    return;
  }

  String comando = doc["Act1"] | "";
  comando.trim();
  comando.toLowerCase();
  Serial.print("Comando recibido: ");
  Serial.println(comando);

  if (comando == "enciende las luces") {
    digitalWrite(PIN_LED, HIGH);
    Serial.println("-> Luces ENCENDIDAS");
  } else if (comando == "apaga las luces") {
    digitalWrite(PIN_LED, LOW);
    Serial.println("-> Luces APAGADAS");
  } else if (comando == "abre la puerta") {
    puerta.write(180);
    Serial.println("-> Puerta ABIERTA");
  } else if (comando == "cierra la puerta") {
    puerta.write(90);
    Serial.println("-> Puerta CERRADA");
  } else {
    Serial.println("-> Comando no reconocido");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Conectando al broker MQTT...");
    // ID único para no chocar con otras simulaciones conectadas al mismo broker
    String clientId = "esp32-miguelruiz-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println(" conectado");
      client.subscribe(TOPICO);
      Serial.print("Escuchando el tópico: ");
      Serial.println(TOPICO);
    } else {
      Serial.print(" falló, rc=");
      Serial.print(client.state());
      Serial.println(" (reintento en 5 s)");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  puerta.setPeriodHertz(50);
  puerta.attach(PIN_SERVO, 500, 2400);
  puerta.write(90);
  randomSeed(micros());
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
