import azure.cognitiveservices.speech as speechsdk
from fastapi import HTTPException
from app.config import DEFAULT_VOICE
import tempfile
import os, httpx, html

AZURE_VOICE_LIMIT = 50


def remove_file(path):
    try:
        os.remove(path)
    except Exception as e:
        print(e)


def _synthesize_chunk(ssml: str, segments: list, key: str, region: str):
    """Synthesize one SSML chunk. Returns (temp_path, timeline, error_detail, http_status)."""
    segment_ranges = []
    search_from = 0
    for segment in segments:
        safe_text = html.escape(segment["text"])
        pos = ssml.find(safe_text, search_from)
        if pos != -1:
            segment_ranges.append((pos, pos + len(safe_text)))
            search_from = pos + len(safe_text)
        else:
            segment_ranges.append(None)

    segment_starts = {}
    segment_ends = {}

    def on_word(evt):
        offset = evt.text_offset
        for i, r in enumerate(segment_ranges):
            if r and r[0] <= offset < r[1]:
                if i not in segment_starts:
                    segment_starts[i] = evt.audio_offset
                duration_ticks = int(evt.duration.total_seconds() * 10_000_000)
                segment_ends[i] = evt.audio_offset + duration_ticks
                break

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_path = tmp_file.name
    tmp_file.close()

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.synthesis_word_boundary.connect(on_word)

    result = synthesizer.speak_ssml_async(ssml).get()
    del synthesizer

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        error_detail = f"Azure synthesis failed: reason={result.reason}"
        http_status = 500
        if result.reason == speechsdk.ResultReason.Canceled:
            details = result.cancellation_details
            error_detail = f"Azure canceled: {details.reason} — {details.error_details}"
            detail_str = details.error_details or ""
            if "429" in detail_str:
                http_status = 429
            elif "403" in detail_str or "401" in detail_str:
                http_status = 403
        remove_file(temp_path)
        return None, [], error_detail, http_status

    total_ticks = int(result.audio_duration.total_seconds() * 10_000_000)
    timeline = []
    prev_end = 0

    for i, segment in enumerate(segments):
        start = segment_starts.get(i, prev_end)
        end = segment_ends.get(i, prev_end + 1)
        timeline.append({
            "text": segment["text"],
            "start": start // 10000,
            "end": end // 10000,
        })
        prev_end = end

    chunk_duration_ms = total_ticks // 10000
    return temp_path, timeline, chunk_duration_ms, None


def build_audio_timeline(segments: list, key: str, region: str):
    """Synthesize segments in chunks of AZURE_VOICE_LIMIT, concatenate audio and merge timelines."""
    chunks = [segments[i:i + AZURE_VOICE_LIMIT] for i in range(0, len(segments), AZURE_VOICE_LIMIT)]

    combined_audio = b''
    combined_timeline = []
    time_offset_ms = 0

    for chunk in chunks:
        chunk_ssml = build_ssml(chunk).strip()
        temp_path, timeline, chunk_duration_ms, error = _synthesize_chunk(chunk_ssml, chunk, key, region)

        if not temp_path:
            # error is (error_detail, http_status) packed as chunk_duration_ms=error_detail, error=http_status
            # Actually _synthesize_chunk returns (None, [], error_detail, http_status) on failure
            # Unpack correctly: temp_path=None, timeline=[], chunk_duration_ms=error_detail, error=http_status
            return None, [], chunk_duration_ms, error

        with open(temp_path, 'rb') as f:
            combined_audio += f.read()
        remove_file(temp_path)

        for entry in timeline:
            combined_timeline.append({
                "text": entry["text"],
                "start": entry["start"] + time_offset_ms,
                "end": entry["end"] + time_offset_ms,
            })

        time_offset_ms += chunk_duration_ms

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tmp_file.write(combined_audio)
    tmp_file.close()

    return tmp_file.name, combined_timeline, None, None


async def build_audio_apirest(ssml, azure_api_key, service_region):
    endpoint = f"https://{service_region}.tts.speech.microsoft.com/cognitiveservices/v1"

    headers = {
        "Ocp-Apim-Subscription-Key": azure_api_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
        "User-Agent": "fastapi-tts"
    }

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(endpoint, headers=headers, content=ssml)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.content


def build_ssml(segments: list):
    ssml = ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
            "xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='es-ES'>")
    for segment in segments:
        voice_name = segment["voice"]
        if voice_name in ["default", None]:
            voice_name = DEFAULT_VOICE
        text = segment["text"]
        style = segment["inflection"]

        safe_text = html.escape(text)
        if style != "default":
            block = f'<voice name="{voice_name}"><mstts:express-as style="{style}">{safe_text}</mstts:express-as></voice>'
        else:
            block = f'<voice name="{voice_name}">{safe_text}</voice>'

        ssml += block

    ssml += "</speak>"
    return ssml
