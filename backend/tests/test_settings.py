"""Tests for app/config/settings.py — new SSB + Anthropic fields."""
import os
from app.config.settings import Settings


def test_settings_has_anthropic_and_ssb_fields(monkeypatch, tmp_path):
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
    assert s.haiku_interval_minutes == 10
    assert s.haiku_chunk_size == 100
    assert s.haiku_max_retry == 8
    assert s.ssb_logspace == "ALL"          # default
    assert s.analysis_mode == "full"        # default
    assert s.expert_settings_reload_minutes == 60  # default
