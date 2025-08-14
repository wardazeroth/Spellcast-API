from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
# import azure.cognitiveservices.speech as speechsdk
from sqlalchemy.orm import Session, registry
from app.database import get_db
from pydantic import BaseModel
from app.models.models import Users, AzureCredentials
from dotenv import load_dotenv
import io, os, httpx
import tempfile
load_dotenv()


class TTSRequest(BaseModel):
    text: str
    voice: str | None= "es-ES-AlvaroNeural"


router = APIRouter(prefix="/tts", tags=["tts"])

# def iterfile(path:str):
#     with open(path, 'rb') as file_like:
#         yield from file_like
#     os.remove(path)
    
def build_ssml(text: str, voice: str) -> str:
    return f"""
    <speak version='1.0' xml:lang='es-ES'>
    <voice xml:lang='es-ES' xml:gender='Male' name='{voice}'>
        {text}
    </voice>
    </speak>
    """
def remove_file(path):
    try:
        os.remove(path)
        print('Archivo temporal eliminado correctamente')
    except Exception as e: 
        print(f'Error eliminando archivo temporal: {e}')
    
# @router.post('/')
# async def text_to_speech(request: Request, tts_req: TTSRequest, db: Session = Depends(get_db)): 
#     # user_id = request.state.user.get('id')
#     # print('el id del user es: ', user_id)
#     # usuario= db.query(Users).filter(Users.id == user_id).first()
#     # print(usuario)

#     # if not usuario:
#     #     raise HTTPException(status_code=404, detail="User not found")
    
#     speech_key =os.getenv("AZURE_API_KEY")
#     service_region = "brazilsouth"

#     # Crear el objeto del servicio
#     speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
#     speech_config.speech_synthesis_voice_name = tts_req.voice
#     # Configurar formato mp3
#     speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    
#     #Guardar el audio en un archivo
#     # audio_output = speechsdk.audio.AudioOutputConfig(filename="salida.mp3")

#     # Crear el sintetizador
#     speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

#     # Texto a convertir
#     text = tts_req.text

#     # Realizar la conversión
#     result = speech_synthesizer.speak_text_async(text).get()

#     # Verificar si fue exitoso
#     if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
#         #AudioDataStream, para obtener bytes mp3
#         audio_stream = speechsdk.AudioDataStream(result)
#         with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
#             audio_stream.save_to_wav_file(tmp_file.name)
#             temp_path = tmp_file.name
#         print("¡Texto convertido a voz exitosamente!")
#     else:
#         print(f"Error: {result.reason}")
        
#     return StreamingResponse (
#         iterfile(temp_path), media_type='audio/mpeg', 
#         headers= {
#             'Content-Disposition': 'attachment; filename="tts.wav"'
#         }
#     )

@router.post('/')
async def text_to_speech(request: Request, tts_req: TTSRequest, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    print('el id del user es: ', user_id)
    usuario= db.query(Users).filter(Users.id == user_id).first()
    print(usuario)
    
    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    if usuario.subscription.plan == 'suscriber':
        azure_api_key =os.getenv("AZURE_API_KEY")
        service_region = "brazilsouth"
        
    else: 
        credenciales = db.query(AzureCredentials).filter(AzureCredentials.user_id == user_id).first()
        azure_api_key = credenciales.azure_key
        service_region = credenciales.region
        voice = credenciales.voice
        
    endpoint = f"https://{service_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    
    headers = {
        "Ocp-Apim-Subscription-Key": azure_api_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
        "User-Agent": "fastapi-tts"
    }
    
    ssml = build_ssml(tts_req.text, tts_req.voice)
    
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(endpoint, headers= headers, content=ssml)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail= response.text)
    
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tmp_file.write(response.content)
    tmp_file.flush()
    tmp_file.close()
        
    #Abrir el archivo para hacer streaming 
    file_stream = open(tmp_file.name, mode='rb')
    
    def iterfile():
        try:
            yield from file_stream
        finally: 
            file_stream.close()
            remove_file(tmp_file.name) #Se elimina el archivo temporal solo al finalizar el streaming
    
    return StreamingResponse(  
        iterfile(), media_type='audio/mpeg',
        headers={"Content-Disposition": 'attachment; filename="tts.mp3"'}
    )
    
    
    
