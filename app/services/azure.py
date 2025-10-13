import httpx
from fastapi import HTTPException

async def validate_key(region: str, azure_key: str) -> bool:
    url = f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {"Ocp-Apim-Subscription-Key": azure_key,
    'Content-Type': 'application/x-www-form-urlencoded'} 
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail='error fetching key')
        return resp

async def get_voices_list(region, azure_key):
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
    headers = {"Ocp-Apim-Subscription-Key": azure_key}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail='error fetching voice in list')
        
        voices_list = []
        voices = resp.json()
        for voice in voices:
            voice_format = {}
            voice_format['value'] = voice.get('ShortName')
            voice_format['label'] = voice.get('DisplayName') + ' - ' + voice.get('LocaleName') + ', ' + voice.get('Gender')
            voice_format['gender'] = voice.get('Gender')
            voices_list.append(voice_format)

        return voices_list