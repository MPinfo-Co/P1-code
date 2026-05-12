"""Tests for app/config/settings.py — Anthropic + scheduler fields.

Issue-290: SSB_URL / SSB_USERNAME / SSB_PASSWORD env vars have been removed;
SSB 連線資訊一律由 tb_expert_settings 提供。
"""

from app.config.settings import Settings

_ENV_FIELDS = [
    "ANTHROPIC_API_KEY",
    "ANALYSIS_MODE",
    "HAIKU_INTERVAL_MINUTES",
    "HAIKU_CHUNK_SIZE",
    "HAIKU_MAX_RETRY",
    "EXPERT_SETTINGS_RELOAD_MINUTES",
]


def test_settings_has_anthropic_and_scheduler_fields(monkeypatch, tmp_path):
    """Settings 應包含 Anthropic 及排程相關欄位；SSB 連線 env 已移除（issue-290）。"""
    for var in _ENV_FIELDS:
        monkeypatch.delenv(var, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql://u:p@localhost/db\n"
        "JWT_SECRET_KEY=x\n"
        "ANTHROPIC_API_KEY=test-key\n"
        "HAIKU_INTERVAL_MINUTES=10\n"
        "HAIKU_CHUNK_SIZE=100\n"
        "HAIKU_MAX_RETRY=8\n"
    )
    s = Settings(_env_file=str(env_file))
    assert s.anthropic_api_key == "test-key"
    assert s.haiku_interval_minutes == 10
    assert s.haiku_chunk_size == 100
    assert s.haiku_max_retry == 8
    assert s.analysis_mode == "full"  # default
    assert s.expert_settings_reload_minutes == 60  # default


def test_settings_ssb_env_vars_removed(monkeypatch, tmp_path):
    """SSB_HOST / SSB_USERNAME / SSB_PASSWORD env vars 已不再是 Settings 欄位（issue-290）。

    SSB 連線資訊改由 tb_expert_settings 動態提供，不從 .env 讀取。
    """
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql://u:p@localhost/db\n"
        "JWT_SECRET_KEY=x\n"
        "SSB_HOST=https://1.2.3.4\n"
        "SSB_USERNAME=admin\n"
        "SSB_PASSWORD=secret\n"
    )
    s = Settings(_env_file=str(env_file))
    # Settings no longer has ssb_host / ssb_username / ssb_password attributes
    assert not hasattr(s, "ssb_host"), (
        "ssb_host should be removed from Settings (issue-290)"
    )
    assert not hasattr(s, "ssb_username"), (
        "ssb_username should be removed from Settings (issue-290)"
    )
    assert not hasattr(s, "ssb_password"), (
        "ssb_password should be removed from Settings (issue-290)"
    )
