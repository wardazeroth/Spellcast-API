import boto3

async def build_aws_audio(voiceId, ssml, accessKeyId, secretAccessKey, region):
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
    for segment in segments:
        text = segment['text']
        style = segment['inflection']

        block = f'<prosody rate="medium" pitch="+5%">{text}</prosody>'

        ssml += block
    ssml += '</speak>'

    return ssml

        