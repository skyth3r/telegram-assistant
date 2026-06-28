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


def test_bin_disabled_by_default(monkeypatch):
    monkeypatch.delenv("BIN_COUNCIL", raising=False)
    assert load_config().bin_enabled is False


def test_bin_council_rejects_non_london(monkeypatch):
    monkeypatch.setenv("BIN_COUNCIL", "NotALondonBorough")
    with pytest.raises(RuntimeError):
        load_config()


def test_bin_enabled_with_council_url_and_uprn(monkeypatch):
    monkeypatch.setenv("BIN_COUNCIL", "BarnetCouncil")
    monkeypatch.setenv("BIN_COUNCIL_URL", "https://example.invalid")
    monkeypatch.setenv("BIN_UPRN", "100012345")
    cfg = load_config()
    assert cfg.bin_enabled is True
    assert cfg.bin_skip_get_url is True
    assert cfg.bin_reminder_time == "20:00"
