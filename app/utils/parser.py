from app.interfaces.editor import Node
from app.misc.consts import DEFAULT_INFLECTION
from app.config import DEFAULT_VOICE

def parser_nodes(node: Node):
    segments = []

    if node.type == 'text':
        current_voice = DEFAULT_VOICE
        inflection = DEFAULT_INFLECTION

        if node.marks:
            for mark in node.marks:
                if mark.type == 'tts' and mark.attrs:
                    current_voice = mark.attrs.voice or DEFAULT_VOICE
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
            result = parser_nodes(child)
            segments.extend(result)
    return segments