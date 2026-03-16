import asyncio
import base64
from pathlib import Path

import pytest

import bot.services.ollama as ollama
from bot.state import chat_history


class _DummySemaphore:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass


class _FakeResponse:
    def __init__(self, data):
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def json(self):
        return self.data


class _FakeSession:
    def __init__(self, captured, response):
        self.captured = captured
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    def post(self, url, json):
        self.captured["url"] = url
        self.captured["payload"] = json
        return _FakeResponse(self.response)


@pytest.fixture(autouse=True)
def reset_chat_history():
    chat_history.clear()
    yield
    chat_history.clear()


def _patch_session(monkeypatch, response):
    captured = {}

    def make_session(timeout=None):
        captured["timeout"] = getattr(timeout, "total", None)
        return _FakeSession(captured, response)

    monkeypatch.setattr(ollama.aiohttp, "ClientSession", make_session)
    monkeypatch.setattr(ollama, "ollama_semaphore", _DummySemaphore())
    return captured


def test_ask_ollama_includes_file_context(tmp_path, monkeypatch):
    captured = _patch_session(monkeypatch, {"response": "ok"})
    payload_file = tmp_path / "note.txt"
    payload_file.write_text("Line A\nLine B")

    asyncio.run(ollama.ask_ollama("user1", "Please read this", files=[str(payload_file)]))

    message_payload = captured["payload"]["messages"][-1]
    assert message_payload["content"].startswith("Please read this")
    assert "File: note.txt" in message_payload["content"]
    assert "Line A" in message_payload["content"]


def test_ask_ollama_converts_heic_and_encodes_image(tmp_path, monkeypatch):
    captured = _patch_session(monkeypatch, {"response": "ok"})
    heic_file = tmp_path / "photo.heic"
    heic_file.write_bytes(b"heic-data")

    def fake_convert(source, dest, max_size=(1024, 1024), quality=70):
        Path(dest).write_bytes(b"jpg-bytes")

    monkeypatch.setattr(ollama, "convert_heic_to_jpg", fake_convert)

    asyncio.run(ollama.ask_ollama("user2", "Describe this", files=[str(heic_file)]))

    images = captured["payload"]["messages"][-1]["images"]
    expected = base64.b64encode(b"jpg-bytes").decode()
    assert images == [expected]
