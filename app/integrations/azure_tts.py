import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

load_dotenv()
# Configuración
speech_key =os.getenv("AZURE_API_KEY")
service_region = "brazilsouth"

# Crear el objeto del servicio
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "es-CL-CatalinaNeural"  # Ejemplo de voz en español chileno

# Crear el sintetizador
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

# Texto a convertir
text = "Buena chuchetumare"

# Realizar la conversión
result = speech_synthesizer.speak_text_async(text).get()

# Verificar si fue exitoso
if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("¡Texto convertido a voz exitosamente!")
else:
    print(f"Error: {result.reason}")
