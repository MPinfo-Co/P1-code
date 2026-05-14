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
