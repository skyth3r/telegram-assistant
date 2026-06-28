from assistant.bot import build_application
from assistant.commands import COMMANDS
from assistant.config import Config


def make_config():
    return Config(
        bot_token="123456:FAKE-TOKEN-FOR-TESTS",
        chat_id="42",
        summary_time="07:00",
        summary_tz="Europe/London",
        upcoming_days=14,
        stadium_url="https://example.com/events",
        allowed_chat_ids=[42, 99],
    )


def test_build_application_registers_all_commands():
    app = build_application(make_config())
    # Every command in the registry should be wired into the app.
    handler_count = sum(len(group) for group in app.handlers.values())
    assert handler_count == len(COMMANDS)


def test_build_application_schedules_morning_summary():
    app = build_application(make_config())
    jobs = app.job_queue.get_jobs_by_name("morning_summary")
    assert len(jobs) == 1


def test_build_application_stores_runtime_config():
    app = build_application(make_config())
    assert app.bot_data["chat_id"] == "42"
    assert app.bot_data["upcoming_days"] == 14
    assert app.bot_data["stadium_url"] == "https://example.com/events"


def test_commands_restricted_to_allowed_chats():
    config = make_config()
    app = build_application(config)
    handlers = [h for group in app.handlers.values() for h in group]
    assert handlers, "expected at least one registered command handler"
    for handler in handlers:
        # Each command's filter must cover exactly the allowlisted chat ids.
        assert handler.filters is not None
        assert set(handler.filters.chat_ids) == set(config.allowed_chat_ids)
