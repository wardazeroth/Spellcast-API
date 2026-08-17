import re
from app.interfaces.editor import Node
from app.misc.consts import DEFAULT_INFLECTION, DEFAULT_VOICES

# Mirrors the frontend's old client-side split (services/tts.ts's pre-TCORE-77 buildSegments):
# split after a sentence-ending punctuation mark that isn't itself followed by another dot
# (so ellipses "..." don't get sliced mid-way). Splitting here — inside each text node, after
# marks are resolved — instead of once per whole node keeps AI-voice timeline entries at
# sentence granularity, matching what the browser-voice `sentences` array and the reader's own
# highlighting already assume; a single unmarked text node otherwise spans a whole paragraph.
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])(?!\s*\.)')

def split_sentences(text: str):
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]

def parser_nodes(node: Node, provider: str):
    segments = []

    if node.type == 'text':
        default_voice = DEFAULT_VOICES.get(provider)
        current_voice = default_voice
        inflection = DEFAULT_INFLECTION

        if node.marks:
            for mark in node.marks:
                if mark.type == 'tts' and mark.attrs:
                    requested_voice = mark.attrs.voice
                    if requested_voice and requested_voice != 'default':
                        current_voice = requested_voice
                    else:
                        current_voice = default_voice
                    inflection = mark.attrs.inflection or DEFAULT_INFLECTION

        if node.text:
            for sentence in split_sentences(node.text):
                segments.append(
                    {
                        "text": sentence,
                        "voice": current_voice,
                        "inflection": inflection
                    }
                )

    if node.content:
        for child in node.content:
            result = parser_nodes(child, provider)
            segments.extend(result)
    return segments
