import httpx
from fastapi import HTTPException
from botocore.exceptions import ClientError
import boto3


async def validate_aws_key(aws_access_key: str, aws_secret_access_key: str, region: str, sessionToken: str):
    try:
        client = boto3.client(
            'polly',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=sessionToken,
            region_name= region
        )

        client.describe_voices()
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['UnrecognizedClientException', 'InvalidSignatureException']:
            raise HTTPException(status_code = 422, detail= 'Las claves de aws son incorrectas')
        elif error_code == 'AccessDeniedException':
            raise HTTPException(status_code = 422, detail= 'Las claves existen pero no tiene permiso para servicios tts (Text to Speech)')
        else:
            raise HTTPException(status_code= 422, detail= f"Error de AWS ({error_code}): {e.response['Error']['Message']}")