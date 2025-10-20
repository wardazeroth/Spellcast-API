import os

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