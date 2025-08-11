from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
import azure.cognitiveservices.speech as speechsdk
from sqlalchemy.orm import Session, registry
from sqlalchemy import MetaData, Table, Column, Integer, String, select
from app.database import SessionLocal
from app.database import DATABASE_URL
from pydantic import BaseModel
from sqlalchemy import create_engine
from dotenv import load_dotenv
import io, os
import tempfile
load_dotenv()

metadata= MetaData()
mapper_registry = registry()

engine = create_engine(
    DATABASE_URL
)

class Users:
    pass

class TTSRequest(BaseModel):
    text: str
    voice: str | None= "es-ES-AlvaroNeural"

tabla_usuarios= Table("users", metadata, autoload_with=engine)
mapper_registry.map_imperatively(Users, tabla_usuarios)


router = APIRouter(prefix="/tts", tags=["tts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    

@router.post('/')
async def text_to_speech(request: Request, tts_req: TTSRequest, db: Session = Depends(get_db)): 
    # user_id = request.state.user.get('id')
    # print('el id del user es: ', user_id)
    # usuario= db.query(Users).filter(Users.id == user_id).first()
    # print(usuario)

    # if not usuario:
    #     raise HTTPException(status_code=404, detail="User not found")
    
    speech_key =os.getenv("AZURE_API_KEY")
    service_region = "brazilsouth"

    # Crear el objeto del servicio
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_synthesis_voice_name = tts_req.voice
    # Configurar formato mp3
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    
    #Guardar el audio en un archivo
    # audio_output = speechsdk.audio.AudioOutputConfig(filename="salida.mp3")

    # Crear el sintetizador
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    # Texto a convertir
    text = tts_req.text

    # Realizar la conversión
    result = speech_synthesizer.speak_text_async(text).get()

    # Verificar si fue exitoso
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        #AudioDataStream, para obtener bytes mp3
        audio_stream = speechsdk.AudioDataStream(result)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            audio_stream.save_to_wav_file(tmp_file.name)
            tmp_file.flush()
            tmp_file.seek(0)
        print("¡Texto convertido a voz exitosamente!")
    else:
        print(f"Error: {result.reason}")
        
    return StreamingResponse (
        open(tmp_file.name, 'rb'), media_type='audio/mpeg',
        headers= {
            'Content-Disposition': 'attachment; filename="tts.wav"'
        }
    )