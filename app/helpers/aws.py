import boto3
import json

class AWSTimelinemanager:
    def __init__(self):
        self.timeline = []
        self.current_words = []
        self.start_time = 0

    def process_marks(self, raw_marks: str, ssml_text:str):
        clean_marks = raw_marks.strip().split('\n')
        items = [json.loads(line) for line in clean_marks if line.strip()]
        for i in range(len(items)):
            current_item= items[i]
            item_type = current_item.get('type')
            timestamp = current_item.get('time')
            if item_type == 'word':
                word = current_item.get('value')
                if not self.current_words:
                    self.start_time = timestamp
                self.current_words.append(word)
            elif item_type == 'ssml':
                if self.current_words:
                    end_time = timestamp
                    self.close_phrase(end_time)
        last_timestamp = items[-1].get('time') + 300 if items else 0
        return self.get_final_timeline(last_timestamp)

    def close_phrase(self, end_time):
        if not self.current_words:
            return
        full_text = " ".join(self.current_words).strip()
        new_dict = {
            "text": full_text,
            "start": self.start_time,
            "end": end_time
        }
        self.timeline.append(new_dict)
        self.current_words.clear()
        self.start_time = 0

    def get_final_timeline(self, final_duration):
        if self.current_words and any(w.strip() for w in self.current_words):
            self.close_phrase(final_duration)
        return self.timeline


def build_aws_timeline(ssml, voiceId, accessKeyId, secretAccessKey, region):
    client = boto3.client(
    'polly',
    aws_access_key_id=accessKeyId,
    aws_secret_access_key=secretAccessKey,
    region_name=region
    )
    response = client.synthesize_speech(
        OutputFormat='json',
        SpeechMarkTypes= ['word', 'ssml'],
        Text=ssml,
        TextType='ssml',
        VoiceId=voiceId
    )

    marks_timeline = response['AudioStream'].read().decode('utf-8')
    manager = AWSTimelinemanager()
    timeline = manager.process_marks(marks_timeline, ssml_text=ssml)
    return timeline

def build_aws_audio(voiceId, ssml, accessKeyId, secretAccessKey, region):
    client = boto3.client(
    'polly',
    aws_access_key_id=accessKeyId,
    aws_secret_access_key=secretAccessKey,
    region_name=region
    )

    response = client.synthesize_speech(
        OutputFormat='mp3',
        SampleRate='8000',
        Text=ssml,
        TextType='ssml',
        VoiceId=voiceId
    )

    return response['AudioStream'].read()

def build_aws_ssml(segments: list) -> str:
    ssml = ("<speak>")
    cuts = ('.', '!', '?', ';')
    for segment in segments:
        text = segment['text']
        style = segment['inflection']

        for c in cuts:
            text= text.replace(c, f"{c}<mark name='cut'/>")

        block = f'<prosody rate="medium" pitch="+5%">{text}</prosody>'

        ssml += block
    ssml += '</speak>'

    return ssml


        