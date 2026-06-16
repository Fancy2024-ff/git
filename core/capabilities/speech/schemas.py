"""speech 能力 schema。"""
TTS_INPUT = {"text": "str", "voice": "str?"}
ASR_INPUT = {"audio_ref": "str"}
TTS_OUTPUT = {"audio_url": "str"}
ASR_OUTPUT = {"text": "str"}
