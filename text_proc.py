from happytransformer import HappyTextToText, TTSettings

happy_tt = HappyTextToText("T5", "vennify/t5-base-grammar-correction")

args = TTSettings(num_beams=5, min_length=1)


def enhance_text(text: str) -> str:
    """Return the enhanced text"""
    return happy_tt.generate_text(f'grammar: {text}', args=args).text
