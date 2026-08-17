import asyncio
import io
import json
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from app.helpers.azure import build_ssml, remove_file, build_audio_timeline, build_audio_apirest

# Azure Speech SDK is not safe for concurrent use in the same process — serialize the
# timeline synthesis (which drives the SDK) behind a single-permit semaphore, matching the
# guard main's tts.py used before the credential refactor.
_azure_semaphore = asyncio.Semaphore(1)


async def azure_time_builder(segments, api_key, service_region):
    # main's build_audio_timeline takes the raw segment list (it builds/escapes SSML itself
    # for word-boundary mapping) and returns a 4-tuple.
    async with _azure_semaphore:
        temp_path, timeline, error, error_status = await run_in_threadpool(
            build_audio_timeline, segments, api_key, service_region
        )
    if not temp_path:
        raise HTTPException(status_code=error_status or 500, detail=error or "Audio synthesis failed")

    file_stream = open(temp_path, mode='rb')

    def iterfile():
        try:
            yield from file_stream
        finally:
            file_stream.close()
            remove_file(temp_path)

    json_timeline = json.dumps(timeline, ensure_ascii=True)
    headers = {
        "Content-Disposition": 'attachment; filename="tts.mp3"',
        "X-Timeline": json_timeline,
        "Access-Control-Expose-Headers": "X-Timeline",
    }
    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)


async def azure_ssml_build(segments, api_key, service_region):
    ssml = build_ssml(segments)
    audio_bytes = await build_audio_apirest(ssml=ssml, azure_api_key=api_key, service_region=service_region)
    file_stream = io.BytesIO(audio_bytes)

    def iterfile():
        yield from file_stream

    headers = {"Content-Disposition": 'attachment; filename="tts.mp3"'}
    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)
