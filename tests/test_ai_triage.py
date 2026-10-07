import json
from types import SimpleNamespace

import pytest

from src.triage import ai_triage_free


def test_parse_json_response_accepts_surrounding_text():
    payload = {"assessment": "uncertain", "reasoning": "The supplied evidence is mixed."}
    text = f"Result follows:\n```json\n{json.dumps(payload)}\n```"
    assert ai_triage_free.parse_json_response(text) == payload


def test_parse_json_response_rejects_invalid_assessment():
    with pytest.raises(ValueError):
        ai_triage_free.parse_json_response('{"assessment":"confirmed","reasoning":"Not allowed."}')


def test_assess_row_uses_configured_model(monkeypatch):
    captured = {}
    def create(**kwargs):
        captured.update(kwargs)
        message = SimpleNamespace(content='prefix {"assessment":"likely_noise","reasoning":"Repeated thin trading."}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(ai_triage_free, "MODEL", "test/model")
    assessment, reasoning = ai_triage_free.assess_row(
        {"symbole": "TEST", "date": "2025-01-01"}, 2, client, max_retries=1
    )
    assert assessment == "likely_noise"
    assert reasoning == "Repeated thin trading."
    assert captured["model"] == "test/model"
    assert captured["max_completion_tokens"] == 1500
    assert captured["reasoning_effort"] == "low"
    assert captured["response_format"] == {"type": "json_object"}


def test_assess_row_retries_empty_content(monkeypatch):
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        content = "" if len(calls) == 1 else '{"assessment":"uncertain","reasoning":"Limited evidence."}'
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )

    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    monkeypatch.setattr(ai_triage_free.time, "sleep", lambda _seconds: None)
    result = ai_triage_free.assess_row(
        {"symbole": "TEST", "date": "2025-01-01"}, 1, client, max_retries=2
    )
    assert result == ("uncertain", "Limited evidence.")
    assert len(calls) == 2
