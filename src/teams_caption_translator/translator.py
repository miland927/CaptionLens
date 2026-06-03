from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .text_utils import normalize_text

_LANG_NAMES = {
    "ja": "日语", "zh-CN": "中文", "zh-TW": "繁体中文",
    "en": "英语", "ko": "韩语", "auto": "自动检测",
}

_LRU_MAX = 256


@dataclass
class TranslationResult:
    text: str
    provider: str
    from_cache: bool = False


class Translator:
    provider = "base"

    def translate(self, text: str, source_lang: str, target_lang: str, context: list[str]) -> TranslationResult:
        raise NotImplementedError


class _LruCache:
    def __init__(self, maxsize: int = _LRU_MAX) -> None:
        self._data: OrderedDict[str, str] = OrderedDict()
        self._max = maxsize

    def get(self, key: str) -> str | None:
        if key in self._data:
            self._data.move_to_end(key)
            return self._data[key]
        return None

    def set(self, key: str, value: str) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        else:
            if len(self._data) >= self._max:
                self._data.popitem(last=False)
        self._data[key] = value


class DeepSeekTranslator(Translator):
    provider = "deepseek"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key.strip()
        self._cache = _LruCache()

    def translate(self, text: str, source_lang: str, target_lang: str, context: list[str]) -> TranslationResult:
        key = normalize_text(text)
        cached = self._cache.get(key)
        if cached is not None:
            return TranslationResult(cached, self.provider, from_cache=True)

        src = _LANG_NAMES.get(source_lang, source_lang)
        tgt = _LANG_NAMES.get(target_lang, target_lang)
        system = f"你是一名专业实时字幕翻译员，将{src}翻译成{tgt}。只输出翻译结果，不加任何解释或标点以外的内容。"
        if context:
            system += f"\n\n前文上下文（仅供参考，不需翻译）：\n" + "\n".join(context[-3:])

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "max_tokens": 512,
            "temperature": 0.2,
        }

        request = Request(
            "https://api.deepseek.com/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DeepSeek API 错误 {exc.code}: {body[:300]}") from exc
        except URLError as exc:
            raise RuntimeError(f"DeepSeek 网络连接失败: {exc.reason}") from exc

        translated = data["choices"][0]["message"]["content"].strip()
        if not translated:
            translated = text
        self._cache.set(key, translated)
        return TranslationResult(translated, self.provider)


class GoogleTranslatorProvider(Translator):
    provider = "google"

    def __init__(self) -> None:
        self._cache = _LruCache()

    def translate(self, text: str, source_lang: str, target_lang: str, context: list[str]) -> TranslationResult:
        key = normalize_text(text)
        cached = self._cache.get(key)
        if cached is not None:
            return TranslationResult(cached, self.provider, from_cache=True)
        from deep_translator import GoogleTranslator

        try:
            translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        except Exception:
            translated = text
        self._cache.set(key, translated)
        return TranslationResult(translated, self.provider)


class EchoTranslator(Translator):
    provider = "echo"

    def translate(self, text: str, source_lang: str, target_lang: str, context: list[str]) -> TranslationResult:
        return TranslationResult(text=text, provider=self.provider)


def create_translator(name: str, api_key: str = "") -> Translator:
    if name == "echo":
        return EchoTranslator()
    if name == "deepseek":
        if not api_key.strip():
            raise ValueError("deepseek_api_key 未配置")
        return DeepSeekTranslator(api_key)
    try:
        return GoogleTranslatorProvider()
    except Exception:
        return EchoTranslator()
