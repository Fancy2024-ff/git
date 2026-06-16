"""speech.tts / speech.asr adapter —— 配音/语音转写（当前 stub）。

注：capability_name 用 speech.tts 作为主标识；asr 作为同一 adapter 的另一操作。
app_type speech_ai 的 required_capabilities 含 speech.tts 与 speech.asr，
registry 对 speech.asr 也能解析到本 adapter（见 registry 别名映射）。
"""

from __future__ import annotations

from capabilities.base import BaseAdapter
from capabilities.speech.providers.stub import SpeechStubProvider


class SpeechAdapter(BaseAdapter):
    capability_name = "speech.tts"
    display_name = "语音(TTS/ASR)"
    supported_operations = ["tts", "asr"]

    def __init__(self, provider=None):
        super().__init__(provider or SpeechStubProvider())

    def _notes(self) -> str:
        return "配置 SPEECH_API_KEY 接入语音 provider 后 runtime_ready；同一 adapter 覆盖 tts 与 asr。"
