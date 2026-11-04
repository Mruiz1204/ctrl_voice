# 🎙️ Control por Voz — Miguel Ruiz

Interfaz multimodal + IoT del curso *Creación de Interfaces Multimodales* (Clase 13).
Hablas un comando, la app lo transcribe, lo interpreta y lo publica por **MQTT**;
un **ESP32 simulado en Wokwi** lo recibe y enciende las luces o abre la puerta.

```
Voz → App Streamlit → broker.mqttdashboard.com (tópico voice_ctrl_miguelruiz) → ESP32 en Wokwi
```

## Comandos
| Dices | El ESP32 hace |
|---|---|
| «enciende las luces» | LED (pin 2) encendido |
| «apaga las luces» | LED apagado |
| «abre la puerta» | Servo (pin 13) a 180° |
| «cierra la puerta» | Servo a 90° |

La app también entiende variaciones («prende la luz», «cerrar la puerta», «apaga el bombillo») y siempre
envía el comando exacto que espera el ESP32: `{"Act1": "enciende las luces"}`.

## Qué incluye
- Grabación de voz con el micrófono y transcripción en español.
- Botones de comando rápido y campo de texto como respaldo.
- Confirmación hablada del comando (gTTS).
- Estado del circuito (luces y puerta) e historial de mensajes enviados.
- Broker, puerto y tópico configurables desde el panel lateral.

## Wokwi
El código del ESP32 está en [`wokwi/sketch.ino`](wokwi/sketch.ino). Pégalo en tu copia del proyecto
https://wokwi.com/projects/377229910598956033 e inicia la simulación. El tópico del sketch y el de la app
deben ser el mismo (`voice_ctrl_miguelruiz`).

## Ejecutar
```bash
pip install -r requirements.txt
streamlit run app.py
```
