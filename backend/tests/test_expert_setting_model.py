"""ExpertSetting model schema regression tests."""

from app.db.models.fn_expert_setting import ExpertSetting


def test_expert_setting_has_haiku_and_sonnet_enabled():
    assert hasattr(ExpertSetting, "haiku_enabled")
    assert hasattr(ExpertSetting, "sonnet_enabled")
    assert hasattr(ExpertSetting, "haiku_interval_minutes")


def test_expert_setting_removed_legacy_fields():
    assert not hasattr(ExpertSetting, "is_enabled")
    assert not hasattr(ExpertSetting, "frequency")
    assert not hasattr(ExpertSetting, "weekday")


def test_pydantic_schemas_match_model():
    from app.api.schema.fn_expert_setting import (
        ExpertSettingOut,
        ExpertSettingSaveRequest,
    )

    out_fields = set(ExpertSettingOut.model_fields.keys())
    assert "haiku_enabled" in out_fields
    assert "sonnet_enabled" in out_fields
    assert "haiku_interval_minutes" in out_fields
    assert "is_enabled" not in out_fields
    assert "frequency" not in out_fields

    save_fields = set(ExpertSettingSaveRequest.model_fields.keys())
    assert "haiku_enabled" in save_fields
    assert "sonnet_enabled" in save_fields
    assert "haiku_interval_minutes" in save_fields
