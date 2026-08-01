from app.helpers.azure import build_ssml, remove_file, build_audio_timeline, build_audio_apirest
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
import io, json

async def timeline_builder(segments, api_key, service_region):
    ssml = build_ssml(segments).strip()
    temp_path, timeline= await run_in_threadpool(build_audio_timeline, text=ssml, key=api_key, region=service_region)
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

async def ssml_build(segments, api_key, service_region):   
    ssml = build_ssml(segments)
    audio_bytes = await build_audio_apirest(ssml=ssml, azure_api_key=api_key, service_region=service_region)
    file_stream = io.BytesIO(audio_bytes)

    def iterfile():
        yield from file_stream 
        
    headers={"Content-Disposition": 'attachment; filename="tts.mp3"'}

    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)