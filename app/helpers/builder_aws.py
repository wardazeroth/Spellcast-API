import boto3
from app.helpers.aws import build_aws_ssml, build_aws_audio, build_aws_timeline
from app.helpers.azure import remove_file
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
import io, json


async def aws_timeline_builder(segments, accessKeyId, secretAccessKey, region):
    ssml = build_aws_ssml(segments).strip()
    
    temp_path, timeline= await run_in_threadpool(build_aws_timeline, ssml=ssml, accessKeyId=accessKeyId, secretAccessKey=secretAccessKey, region=region)
    file_stream = open(temp_path, mode='rb')
    def iterfile():
        try:
            yield from file_stream
        finally:
            file_stream.close()
            remove_file(temp_path)
    headers={"Content-Disposition": 'attachment; filename="tts.mp3"'}

    json_timeline = json.dumps(timeline, ensure_ascii=False)
    headers["X-Timeline"] = json_timeline.encode('utf-8').decode('latin-1')
    headers["Access-Control-Expose-Headers"] = "X-Timeline"
    
    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)

async def aws_ssml_build(voice_id, segments, aws_access_key_id, aws_secret_access_key, region):
    ssml = build_aws_ssml(segments)
    audio_bytes = build_aws_audio(voiceId=voice_id, ssml=ssml, accessKeyId=aws_access_key_id, secretAccessKey=aws_secret_access_key, region=region)
    file_stream = io.BytesIO(audio_bytes)

    def iterfile():
        yield from file_stream

    headers={'Content-Disposition': 'attachment; filename="tts.mp3"'}

    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)
