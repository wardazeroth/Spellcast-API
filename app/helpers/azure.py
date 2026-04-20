from app.config import DEFAULT_VOICE
import os

# def build_ssml(text: str, voice: str) -> str:
#     return f"""
#     <speak version='1.0' xml:lang='es-ES'>
#     <voice xml:lang='es-ES' xml:gender='Male' name='{voice}'>
#         {text}
#     </voice>
#     </speak>
#     """

def build_ssml(segmentos: list):
    ssml = ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
            "xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='es-ES'>"
            )
    for segmento in segmentos:
        voice_name = segmento["voice"]
        if voice_name in ["default", None]:
            voice_name = DEFAULT_VOICE
        text = segmento["text"]
        style = segmento["inflection"]

        if style != "default":
            block = f"<voice name= '{voice_name}'><mstts:express-as style='{style}'>'{text}'</mstts:express-as></voice>"
        else:
            block = f"<voice name= '{voice_name}'>'{text}'</voice>"

        ssml+=block

    ssml+= "</speak>"

    return ssml
    

def remove_file(path):
    try:
        os.remove(path)
        print('Archivo temporal eliminado correctamente')
    except Exception as e: 
        print(f'Error eliminando archivo temporal: {e}')