"""Tests for app/config/settings.py — new SSB + Anthropic fields."""
from app.config.settings import Settings

_SSB_FIELDS = [
    "ANTHROPIC_API_KEY",
    "SSB_HOST",
    "SSB_USERNAME",
    "SSB_PASSWORD",
    "SSB_LOGSPACE",
    "ANALYSIS_MODE",
    "HAIKU_INTERVAL_MINUTES",
    "HAIKU_CHUNK_SIZE",
    "HAIKU_MAX_RETRY",
    "EXPERT_SETTINGS_RELOAD_MINUTES",
]


def test_settings_has_anthropic_and_ssb_fields(monkeypatch, tmp_path):
    for var in _SSB_FIELDS:
        monkeypatch.delenv(var, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql://u:p@localhost/db\n"
        "JWT_SECRET_KEY=x\n"
        "ANTHROPIC_API_KEY=test-key\n"
        "SSB_HOST=https://1.2.3.4\n"
        "HAIKU_INTERVAL_MINUTES=10\n"
        "HAIKU_CHUNK_SIZE=100\n"
        "HAIKU_MAX_RETRY=8\n"
    )
    s = Settings(_env_file=str(env_file))
    assert s.anthropic_api_key == "test-key"
    assert s.ssb_host == "https://1.2.3.4"
    assert s.ssb_username is None
    assert s.ssb_password is None
    assert s.haiku_interval_minutes == 10
    assert s.haiku_chunk_size == 100
    assert s.haiku_max_retry == 8
    assert s.ssb_logspace == "ALL"          # default
    assert s.analysis_mode == "full"        # default
    assert s.expert_settings_reload_minutes == 60  # default
