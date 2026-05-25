from app.interfaces.editor import Node

def parser_nodes(node: Node):
    segments = []

    if node.type == 'text':
        current_voice = 'default'
        inflection = 'default'

        if node.marks:
            for mark in node.marks:
                if mark.type == 'tts':
                    current_voice = mark.attrs.voice
                    inflection = mark.attrs.inflection
                    

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