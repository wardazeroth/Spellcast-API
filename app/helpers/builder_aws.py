import boto3
from app.helpers.aws import build_aws_ssml, build_aws_audio
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
import io, json


async def aws_timeline_builder(segments, accessKeyId, secretAccessKey, region):
    ssml = build_aws_audio(segments).strip()
    # temp_path, timeline= await run_in_threadpool(build_audio_timeline, text=ssml, key=accessKeyId region=service_region)
    # file_stream = open(temp_path, mode='rb')
    return 

async def aws_ssml_build(segments, aws_access_key_id, aws_secret_access_key, region):
    ssml = build_aws_ssml(segments)
    audio_bytes = await build_aws_audio(segments, ssml=ssml, accessKeyId=aws_access_key_id, secretAccessKey=aws_secret_access_key, region=region)
    file_stream = io.BytesIO(audio_bytes)

    def iterfile():
        yield from file_stream

    headers={'Content-Disposition': 'attachment; filename="tts.mp3"'}

    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)
