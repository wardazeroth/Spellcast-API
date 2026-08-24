import re
from app.interfaces.editor import Node
from app.misc.consts import DEFAULT_INFLECTION, DEFAULT_VOICES

# Mirrors the frontend's sentence splitter (magictext/utils/extractTTSSegments.ts,
# PdfProcessor.extractSentencesFromJSON): split after a sentence-ending punctuation mark that
# isn't itself followed by another dot (so ellipses "..." don't get sliced mid-way).
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])(?!\s*\.)')

def split_sentences(text: str):
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def _resolve_voice_inflection(mark_attrs, default_voice):
    if mark_attrs is None:
        return default_voice, DEFAULT_INFLECTION
    requested_voice = mark_attrs.voice
    voice = requested_voice if (requested_voice and requested_voice != 'default') else default_voice
    inflection = mark_attrs.inflection or DEFAULT_INFLECTION
    return voice, inflection


def _build_char_info(node: Node, provider: str):
    """Flatten a paragraph/heading's direct inline children (text/hardBreak) into one merged
    string, tracking the resolved (voice, inflection) for every character. Mirrors the
    frontend's buildCharInfo() in extractTTSSegments.ts — splitting sentences must happen on
    this same merged text, not per text-node, or a paragraph with any inline mark (bold, a
    'tts' mark on part of a sentence, etc.) — which Tiptap always represents as multiple text
    nodes — would produce different sentence boundaries here than in the reader's own
    highlighting, and shorter, mismatched pieces sent to the TTS provider."""
    default_voice = DEFAULT_VOICES.get(provider)
    full_text = ''
    chars = []

    for inline in (node.content or []):
        if inline.type == 'text' and inline.text:
            tts_mark = next((m for m in (inline.marks or []) if m.type == 'tts'), None)
            voice, inflection = _resolve_voice_inflection(tts_mark.attrs if tts_mark else None, default_voice)
            full_text += inline.text
            chars.extend([(voice, inflection)] * len(inline.text))
        elif inline.type == 'hardBreak':
            full_text += ' '
            chars.append((default_voice, DEFAULT_INFLECTION))

    return full_text, chars


def _parse_block(node: Node, provider: str):
    """Split one paragraph/heading's merged text into sentence segments, resolving each
    sentence's voice/inflection from the character info at the sentence's start position —
    same approach as extractTTSSegments.ts's per-sentence `chars[pos]?.tts` lookup."""
    full_text, chars = _build_char_info(node, provider)
    if not full_text.strip():
        return []

    default_voice = DEFAULT_VOICES.get(provider)
    segments = []
    search_from = 0
    for sentence in split_sentences(full_text):
        pos = full_text.find(sentence, search_from)
        if pos == -1:
            pos = search_from
        search_from = pos + len(sentence)
        voice, inflection = chars[pos] if pos < len(chars) else (default_voice, DEFAULT_INFLECTION)
        segments.append({"text": sentence, "voice": voice, "inflection": inflection})

    return segments


def parser_nodes(node: Node, provider: str):
    segments = []

    if node.type in ('paragraph', 'heading'):
        segments.extend(_parse_block(node, provider))
        return segments

    if node.content:
        for child in node.content:
            segments.extend(parser_nodes(child, provider))

    return segments
