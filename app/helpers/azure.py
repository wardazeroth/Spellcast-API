import azure.cognitiveservices.speech as speechsdk
from app.misc.consts import DEFAULT_VOICES
from fastapi import HTTPException
import tempfile
import os, httpx

AZURE_INFLECTION_PRESETS = {
    # Positive Emotions
    "cheerful": '<mstts:express-as style="cheerful" styledegree="1.8"><prosody pitch="+12%" rate="+8%">{text}</prosody></mstts:express-as>',
    "excited": '<mstts:express-as style="excited" styledegree="1.8"><prosody pitch="+18%" rate="+18%">{text}</prosody></mstts:express-as>',
    "friendly": '<mstts:express-as style="friendly" styledegree="1.8"><prosody pitch="+6%" rate="+3%">{text}</prosody></mstts:express-as>',
    "hopeful": '<mstts:express-as style="hopeful" styledegree="1.8"><prosody pitch="+8%" rate="+5%">{text}</prosody></mstts:express-as>',

    # Down Emotions
    "calm": '<mstts:express-as style="calm" styledegree="1.8"><prosody pitch="-4%" rate="-10%">{text}</prosody></mstts:express-as>',
    "sad": '<mstts:express-as style="sad" styledegree="1.8"><prosody pitch="-12%" rate="-18%">{text}</prosody></mstts:express-as>',

    # whisper / fear
    "whispering": '<mstts:express-as style="whispering" styledegree="2"><prosody volume="x-soft" pitch="-5%" rate="-10%">{text}</prosody></mstts:express-as>',
    "fearful": '<mstts:express-as style="fearful" styledegree="1.8"><prosody pitch="+10%" rate="+12%">{text}</prosody></mstts:express-as>',
    "terrified": '<mstts:express-as style="terrified" styledegree="2"><prosody pitch="+22%" rate="+20%">{text}</prosody></mstts:express-as>',

    # Hostile
    "angry": '<mstts:express-as style="angry" styledegree="1.8"><prosody volume="loud" pitch="-6%" rate="+10%">{text}</prosody></mstts:express-as>',
    "unfriendly": '<mstts:express-as style="unfriendly" styledegree="1.8"><prosody pitch="-8%" rate="-5%">{text}</prosody></mstts:express-as>',
    "shouting": '<mstts:express-as style="shouting" styledegree="2"><prosody volume="x-loud" pitch="+10%" rate="+12%">{text}</prosody></mstts:express-as>',

    # prosody
    "fast": '<prosody rate="+35%">{text}</prosody>',
    "slow": '<prosody rate="-30%">{text}</prosody>',
    "emphasis": '<emphasis level="strong">{text}</emphasis>'
    }

class AzureTimelineManager:
    def __init__(self):
        self.timeline = []
        self.current_words = []
        self.start_tick = 0

    def on_word_boundary(self, event):
        try:
            word = event.text.strip()
            if not word: return
            
            if not self.current_words:
                self.start_tick = event.audio_offset
            
            self.current_words.append(word)

            cuts = ('.', '!', '?', ';')
            
            if any(c in word for c in cuts):
                duration_ticks = int(event.duration.total_seconds()* 10_000_000)
                end_tick = event.audio_offset + duration_ticks
                self.close_phrase(end_tick)
        except Exception as e:
            print(e)
                
    def close_phrase(self, end_tick):
        if not self.current_words:
            return

        full_text = " ".join(self.current_words).strip()
        new_dict = {
            "text": full_text,
            "start": (self.start_tick) // 10000,
            "end": (end_tick)// 10000
        }
        self.timeline.append(new_dict)

        self.current_words.clear()
        self.start_tick = 0

    def get_final_timeline(self, final_duration_ticks):
        if self.current_words and any(w.strip() for w in self.current_words):
            self.close_phrase(final_duration_ticks)
        return self.timeline

def remove_file(path):
    try:
        os.remove(path)
    except Exception as e: 
        print(e)

def build_audio_timeline(text, key, region):
    manager = AzureTimelineManager()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_path = tmp_file.name
    tmp_file.close()

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)   
    audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
    synthesizer= speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    #callback:
    synthesizer.synthesis_word_boundary.connect(manager.on_word_boundary)
    result = synthesizer.speak_ssml_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        total_ticks = int(result.audio_duration.total_seconds() * 10_000_000)
        timeline = manager.get_final_timeline(total_ticks)

        return temp_path, timeline
    else:
        return None, []
    
async def build_audio_apirest(ssml, azure_api_key, service_region):
        endpoint = f"https://{service_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    
        headers = {
            "Ocp-Apim-Subscription-Key": azure_api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
            "User-Agent": "fastapi-tts"
        }

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(endpoint, headers= headers, content=ssml)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail= response.text)
        return response.content

def build_ssml(segments: list):
    primary_voice = segments[0].get('voice') if segments else DEFAULT_VOICES.get('azure')
    parts = primary_voice.split("-")
    doc_lang = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "es-CL"

    ssml = (f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
            f"xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='{doc_lang}'>"
            )
    for segment in segments:
        voice_name = segment["voice"]
        text = segment["text"]
        style = segment["inflection"]

        if style and style != "default":
            styled = apply_azure_inflection(text, style)
            block = f'<voice name="{voice_name}">{styled}</voice>'
        else:
            block = f'<voice name="{voice_name}">{text}</voice>'

        ssml+=block

    ssml+= "</speak>"

    return ssml

def apply_azure_inflection(text:str, inflection:str) -> str:
    template = AZURE_INFLECTION_PRESETS.get(inflection)
    if not template:
        return text
    return template.format(text=text)




