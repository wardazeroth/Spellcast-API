import boto3
from app.helpers.aws import build_aws_ssml, build_aws_audio, build_aws_timeline
from app.helpers.azure import remove_file
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
import io, json
import tempfile

async def aws_timeline_builder(segments, voice_id, accessKeyId, secretAccessKey, region):
    ssml = build_aws_ssml(segments).strip()
    audio_bytes = await run_in_threadpool(build_aws_audio, voiceId=voice_id, ssml=ssml, accessKeyId=accessKeyId, secretAccessKey=secretAccessKey, region=region)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_file.write(audio_bytes)
    temp_path = temp_file.name
    temp_file.close()
    timeline= await run_in_threadpool(build_aws_timeline, ssml=ssml, voiceId = voice_id, accessKeyId=accessKeyId, secretAccessKey=secretAccessKey, region=region)
    file_stream = open(temp_path, mode='rb')
    def iterfile():
        try:
            yield from file_stream
        finally: 
            file_stream.close()
            remove_file(temp_path)


    json_timeline = json.dumps(timeline, ensure_ascii=False)
    headers = {
    "Content-Disposition": 'attachment; filename="tts.mp3"',
    "X-Timeline" : json_timeline.encode('utf-8').decode('latin-1'),
    "Access-Control-Expose-Headers" : "X-Timeline"
    }
    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)

async def aws_ssml_build(voice_id, segments, aws_access_key_id, aws_secret_access_key, region):
    ssml = build_aws_ssml(segments)
    audio_bytes = await run_in_threadpool(build_aws_audio, voiceId=voice_id, ssml=ssml, accessKeyId=aws_access_key_id, secretAccessKey=aws_secret_access_key, region=region)
    file_stream = io.BytesIO(audio_bytes)

    def iterfile():
        yield from file_stream

    headers={'Content-Disposition': 'attachment; filename="tts.mp3"'}

    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)
