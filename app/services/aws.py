from fastapi import HTTPException
from botocore.exceptions import ClientError
import boto3


async def validate_aws_key(aws_access_key: str, aws_secret_access_key: str, region: str, sessionToken: str | None = None):
    await get_aws_voices_list(aws_access_key, aws_secret_access_key, region, sessionToken)
    return True

async def get_aws_voices_list(aws_access_key: str, aws_secret_access_key: str, region: str, sessionToken: str | None = None):
    try:
        client = boto3.client(
            'polly',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=sessionToken,
            region_name= region
        )

        voices = client.describe_voices()
        voices_list = []
        for voice in voices['Voices']:
            voice_format= {}
            voice_format['value'] = voice.get('Id')
            voice_format['name'] = voice.get('Name')
            voice_format['gender'] = voice.get('Gender')
            voice_format['language'] = voice.get('LanguageCode')
            voice_format['language_name'] = voice.get('LanguageName')
            voices_list.append(voice_format)
        return voices_list
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['UnrecognizedClientException', 'InvalidSignatureException']:
            raise HTTPException(status_code = 422, detail= 'Las claves de aws son incorrectas')
        elif error_code == 'AccessDeniedException':
            raise HTTPException(status_code = 422, detail= 'Las claves existen pero no tiene permiso para servicios tts (Text to Speech)')
        else:
            raise HTTPException(status_code= 422, detail= f"Error de AWS ({error_code}): {e.response['Error']['Message']}")
