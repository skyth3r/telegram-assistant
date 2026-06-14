import pytest

from assistant.config import load_config


@pytest.fixture(autouse=True)
def base_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:FAKE")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.delenv("ALLOWED_CHAT_IDS", raising=False)


def test_allowed_chat_ids_parsed(monkeypatch):
    monkeypatch.setenv("ALLOWED_CHAT_IDS", "42,99")
    assert load_config().allowed_chat_ids == [42, 99]


def test_allowed_chat_ids_tolerates_spaces_and_trailing_comma(monkeypatch):
    monkeypatch.setenv("ALLOWED_CHAT_IDS", " 42 , 99, ")
    assert load_config().allowed_chat_ids == [42, 99]


def test_allowed_chat_ids_defaults_to_chat_id():
    # ALLOWED_CHAT_IDS unset (cleared by base_env fixture).
    assert load_config().allowed_chat_ids == [42]


def test_allowed_chat_ids_blank_defaults_to_chat_id(monkeypatch):
    monkeypatch.setenv("ALLOWED_CHAT_IDS", "   ")
    assert load_config().allowed_chat_ids == [42]


def test_allowed_chat_ids_supports_negative_group_id(monkeypatch):
    monkeypatch.setenv("ALLOWED_CHAT_IDS", "-100123,42")
    assert load_config().allowed_chat_ids == [-100123, 42]
