from app.interfaces.editor import Node
from app.misc.consts import DEFAULT_INFLECTION, DEFAULT_VOICES

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
            node_text = node.text
            segments.append(
                {
                    "text": node_text,
                    "voice": current_voice,
                    "inflection": inflection
                }
            )

    if node.content:
        for child in node.content:
            result = parser_nodes(child, provider)
            segments.extend(result)
    return segments
