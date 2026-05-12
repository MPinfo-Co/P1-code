"""Tests for Sonnet pipeline company-data injection behaviour (issue-265).

Covers TDD items: T1, T2, T3, T4, T5, T10 (pro_task / aggregate_daily),
and T-EV-04, T-EV-05 (GET /events/{id} affected_detail content).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

from app import scheduler
from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
from app.db.models.events import SecurityEvent
from app.db.models.fn_company_data import CompanyData
from app.tasks.pro_task import run_pro_task
from app.tasks import claude_pro


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_chunks(db, today: date, events: list[dict]) -> None:
    """Seed one done LogBatch + one done ChunkResult for the given day."""
    start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    batch = LogBatch(
        time_from=start,
        time_to=start + timedelta(hours=1),
        status="done",
        records_fetched=len(events),
        chunks_total=1,
        chunks_done=1,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    db.add(
        ChunkResult(
            batch_id=batch.id,
            chunk_index=0,
            chunk_size=len(events),
            events=events,
            status="done",
        )
    )
    db.commit()


def _seed_company_data(db, rows: list[dict]) -> None:
    """Seed tb_company_data with given name/content rows."""
    for r in rows:
        db.add(CompanyData(name=r["name"], content=r["content"]))
    db.commit()


def _fake_anthropic(events: list[dict]) -> MagicMock:
    """Return an Anthropic client mock returning the given events as a tool_use block.

    對齊 main 上 #211 改造後的 claude_pro.aggregate_daily：Sonnet 改用
    `emit_daily_events` tool call 回傳事件清單，不再走 JSON 文字輸出。
    """
    ant = MagicMock()
    block = MagicMock()
    block.type = "tool_use"
    block.name = "emit_daily_events"
    block.input = {"events": events}
    ant.messages.create.return_value = MagicMock(content=[block])
    return ant


def _enable_scheduler():
    scheduler._runtime = scheduler.RuntimeSettings(is_enabled=True)


# ---------------------------------------------------------------------------
# T1 — Normal-behaviour event excluded when company data matches
# ---------------------------------------------------------------------------


def test_t1_normal_behaviour_event_not_written(db_session):
    """對應 T1

    When tb_company_data describes an activity as normal, Sonnet excludes it.
    The mock simulates Sonnet returning an empty list (event filtered out).
    """
    _enable_scheduler()
    today = date.today()

    _seed_company_data(
        db_session,
        [
            {
                "name": "IT 維運規範",
                "content": "每日備份帳號 backup_svc 在凌晨 02:00 登入屬正常行為。",
            },
        ],
    )
    _seed_chunks(
        db_session,
        today,
        [
            {
                "star_rank": 3,
                "title": "backup_svc 凌晨登入",
                "affected_summary": "backup_svc (host01)",
                "affected_detail": "【異常發現】backup_svc 於 02:00 登入\n【風險分析】可能為可疑活動",
                "match_key": "win-backup-svc",
                "log_ids": ["1"],
                "ioc_list": [],
                "mitre_tags": [],
            }
        ],
    )

    # Sonnet judges this as normal behaviour → returns empty list
    ant = _fake_anthropic([])

    run_pro_task(
        today=today,
        anthropic_client_factory=lambda: ant,
        db_factory=lambda: db_session,
    )

    assert db_session.query(SecurityEvent).count() == 0
    da = db_session.query(DailyAnalysis).filter_by(analysis_date=today).one()
    assert da.status == "done"
    assert da.events_created == 0


# ---------------------------------------------------------------------------
# T2 — suggests reflects company data's disposal convention
# ---------------------------------------------------------------------------


def test_t2_suggests_reflects_company_data_convention(db_session):
    """對應 T2

    When Sonnet still judges an event as a security event and the company data
    contains a disposal convention, the written event's suggests field reflects it.
    """
    _enable_scheduler()
    today = date.today()

    _seed_company_data(
        db_session,
        [
            {
                "name": "資安應變手冊",
                "content": "外部 IP 掃描事件應聯絡資訊組 A，並封鎖來源 IP。",
            },
        ],
    )
    _seed_chunks(
        db_session,
        today,
        [
            {
                "star_rank": 4,
                "title": "外部 IP 掃描",
                "affected_summary": "防火牆 (外部來源)",
                "affected_detail": "【異常發現】偵測到外部 IP 掃描\n【風險分析】高風險\n【攻擊來源】1.2.3.4",
                "match_key": "deny_external_1.2.3",
                "log_ids": ["2"],
                "ioc_list": ["1.2.3.4"],
                "mitre_tags": ["T1046"],
            }
        ],
    )

    sonnet_output = [
        {
            "match_key": "deny_external_1.2.3",
            "star_rank": 4,
            "title": "外部 IP 掃描",
            "description": "外部 IP 進行端口掃描",
            "affected_summary": "防火牆 (外部來源)",
            "affected_detail": "【異常發現】偵測到外部 IP 掃描\n【風險分析】高風險\n【攻擊來源】1.2.3.4",
            "detection_count": 1,
            "ioc_list": ["1.2.3.4"],
            "mitre_tags": ["T1046"],
            "suggests": ["聯絡資訊組 A", "封鎖來源 IP 1.2.3.4", "檢查防火牆規則"],
            "continued_from_match_key": None,
        }
    ]
    ant = _fake_anthropic(sonnet_output)

    run_pro_task(
        today=today,
        anthropic_client_factory=lambda: ant,
        db_factory=lambda: db_session,
    )

    ev = (
        db_session.query(SecurityEvent).filter_by(match_key="deny_external_1.2.3").one()
    )
    assert ev.suggests is not None
    assert any("資訊組 A" in s for s in ev.suggests)


# ---------------------------------------------------------------------------
# T3 — affected_detail末尾包含【分析依據】段落
# ---------------------------------------------------------------------------


def test_t3_affected_detail_has_analysis_basis(db_session):
    """對應 T3

    When company data only affects interpretation (not disposal), Sonnet appends
    a 【分析依據】paragraph to affected_detail.
    """
    _enable_scheduler()
    today = date.today()

    _seed_company_data(
        db_session,
        [
            {
                "name": "設備清冊",
                "content": "IP 10.0.0.5 為研發部測試伺服器，偶發異常流量屬預期行為。",
            },
        ],
    )
    _seed_chunks(
        db_session,
        today,
        [
            {
                "star_rank": 3,
                "title": "10.0.0.5 異常流量",
                "affected_summary": "10.0.0.5 (研發部)",
                "affected_detail": "【異常發現】10.0.0.5 發送異常流量\n【風險分析】中風險",
                "match_key": "deny_internal_10.0.0.5",
                "log_ids": ["3"],
                "ioc_list": [],
                "mitre_tags": [],
            }
        ],
    )

    detail_with_basis = (
        "【異常發現】10.0.0.5 發送異常流量\n"
        "【風險分析】中風險\n"
        "【分析依據】參考公司資料『設備清冊』：IP 10.0.0.5 為研發部測試伺服器，偶發異常流量屬預期行為。"
    )
    sonnet_output = [
        {
            "match_key": "deny_internal_10.0.0.5",
            "star_rank": 3,
            "title": "10.0.0.5 異常流量",
            "description": "研發部測試伺服器流量",
            "affected_summary": "10.0.0.5 (研發部)",
            "affected_detail": detail_with_basis,
            "detection_count": 1,
            "ioc_list": [],
            "mitre_tags": [],
            "suggests": ["持續監控", "確認測試計畫", "記錄異常時間"],
            "continued_from_match_key": None,
        }
    ]
    ant = _fake_anthropic(sonnet_output)

    run_pro_task(
        today=today,
        anthropic_client_factory=lambda: ant,
        db_factory=lambda: db_session,
    )

    ev = (
        db_session.query(SecurityEvent)
        .filter_by(match_key="deny_internal_10.0.0.5")
        .one()
    )
    assert "【分析依據】" in ev.affected_detail
    assert "設備清冊" in ev.affected_detail


# ---------------------------------------------------------------------------
# T4 — tb_company_data 為空時行為與既有相同
# ---------------------------------------------------------------------------


def test_t4_empty_company_data_behaves_as_before(db_session):
    """對應 T4

    When tb_company_data has no rows, the pipeline produces the same output
    as before (no 【分析依據】 paragraph).
    """
    _enable_scheduler()
    today = date.today()

    # No company data seeded
    _seed_chunks(
        db_session,
        today,
        [
            {
                "star_rank": 3,
                "title": "Port scan",
                "affected_summary": "firewall",
                "affected_detail": "【異常發現】端口掃描\n【風險分析】中風險",
                "match_key": "deny_external_5.6.7",
                "log_ids": ["4"],
                "ioc_list": [],
                "mitre_tags": [],
            }
        ],
    )

    affected_no_basis = "【異常發現】端口掃描\n【風險分析】中風險"
    sonnet_output = [
        {
            "match_key": "deny_external_5.6.7",
            "star_rank": 3,
            "title": "Port scan",
            "description": "外部端口掃描",
            "affected_summary": "firewall",
            "affected_detail": affected_no_basis,
            "detection_count": 1,
            "ioc_list": [],
            "mitre_tags": [],
            "suggests": ["封鎖 IP", "更新規則"],
            "continued_from_match_key": None,
        }
    ]
    ant = _fake_anthropic(sonnet_output)

    run_pro_task(
        today=today,
        anthropic_client_factory=lambda: ant,
        db_factory=lambda: db_session,
    )

    ev = (
        db_session.query(SecurityEvent).filter_by(match_key="deny_external_5.6.7").one()
    )
    assert "【分析依據】" not in (ev.affected_detail or "")
    da = db_session.query(DailyAnalysis).filter_by(analysis_date=today).one()
    assert da.status == "done"


# ---------------------------------------------------------------------------
# T5 — 公司資料存在但未命中時，行為與空時相同
# ---------------------------------------------------------------------------


def test_t5_company_data_not_matched_no_analysis_basis(db_session):
    """對應 T5

    When company data exists but Sonnet does not reference any of it,
    affected_detail should not contain 【分析依據】.
    """
    _enable_scheduler()
    today = date.today()

    _seed_company_data(
        db_session,
        [
            {
                "name": "其他規範",
                "content": "辦公室印表機 IP 192.168.1.100 的流量屬正常。",
            },
        ],
    )
    _seed_chunks(
        db_session,
        today,
        [
            {
                "star_rank": 4,
                "title": "暴力破解攻擊",
                "affected_summary": "主機 host02",
                "affected_detail": "【異常發現】多次登入失敗\n【風險分析】高風險",
                "match_key": "win-brute-admin",
                "log_ids": ["5"],
                "ioc_list": [],
                "mitre_tags": ["T1110"],
            }
        ],
    )

    # Sonnet does not reference company data — no 【分析依據】
    affected_no_basis = "【異常發現】多次登入失敗\n【風險分析】高風險"
    sonnet_output = [
        {
            "match_key": "win-brute-admin",
            "star_rank": 4,
            "title": "暴力破解攻擊",
            "description": "admin 帳號暴力破解",
            "affected_summary": "主機 host02",
            "affected_detail": affected_no_basis,
            "detection_count": 1,
            "ioc_list": [],
            "mitre_tags": ["T1110"],
            "suggests": ["鎖定帳號", "啟用 MFA", "檢查日誌"],
            "continued_from_match_key": None,
        }
    ]
    ant = _fake_anthropic(sonnet_output)

    run_pro_task(
        today=today,
        anthropic_client_factory=lambda: ant,
        db_factory=lambda: db_session,
    )

    ev = db_session.query(SecurityEvent).filter_by(match_key="win-brute-admin").one()
    assert "【分析依據】" not in (ev.affected_detail or "")


# ---------------------------------------------------------------------------
# T10 — 異常時寫入 status=failed，不污染 tb_security_events
# ---------------------------------------------------------------------------


def test_t10_exception_writes_failed_status_no_events(db_session):
    """對應 T10

    When an exception occurs during company data loading or pipeline execution,
    tb_daily_analysis.status must be 'failed' with error_message recorded,
    and tb_security_events must not have any new rows.
    """
    _enable_scheduler()
    today = date.today()

    _seed_company_data(
        db_session,
        [
            {"name": "規範", "content": "測試資料"},
        ],
    )
    _seed_chunks(
        db_session,
        today,
        [
            {
                "star_rank": 3,
                "title": "Test event",
                "affected_summary": "host",
                "affected_detail": "【異常發現】test",
                "match_key": "win-test",
                "log_ids": ["1"],
                "ioc_list": [],
                "mitre_tags": [],
            }
        ],
    )

    # Simulate aggregate_daily raising an exception (e.g., Anthropic API error)
    def failing_factory():
        raise RuntimeError("Anthropic API 連線失敗")

    run_pro_task(
        today=today,
        anthropic_client_factory=failing_factory,
        db_factory=lambda: db_session,
    )

    da = db_session.query(DailyAnalysis).filter_by(analysis_date=today).one()
    assert da.status == "failed"
    assert da.error_message is not None
    assert "Anthropic API 連線失敗" in da.error_message
    # No new security events should be written
    assert db_session.query(SecurityEvent).count() == 0


# ---------------------------------------------------------------------------
# T-EV-04 — GET /events/{id}: affected_detail without 【分析依據】
# ---------------------------------------------------------------------------


def test_ev04_get_event_detail_without_analysis_basis(client, engine):
    """對應 T-EV-04

    GET /events/{id} for an event without 【分析依據】 returns 200
    and affected_detail does not contain that section.
    """
    from sqlalchemy.orm import sessionmaker as _sm
    from app.db.models.events import SecurityEvent as SE
    from app.utils.util_store import create_access_token

    # main 把 SecurityEvent 放 _TASK_TABLES、client/engine fixture 只建 _SEED_TABLES，
    # PG #207 HTTP test 在 test 內自行補建（不動 main conftest 分組）
    SE.__table__.create(bind=engine, checkfirst=True)

    Session_ = _sm(bind=engine)
    db = Session_()

    ev = SE(
        event_date=date.today(),
        star_rank=3,
        title="外部掃描",
        affected_summary="firewall",
        affected_detail="【異常發現】偵測到外部掃描\n【風險分析】中風險",
        match_key="deny_external_no_basis",
        detection_count=1,
        current_status="pending",
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    ev_id = ev.id
    db.close()

    # Use a dummy user_id=1 for JWT — authenticate() only checks JWT + blacklist
    token = create_access_token(user_id=1)
    resp = client.get(
        f"/events/{ev_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "【分析依據】" not in (data.get("affected_detail") or "")


# ---------------------------------------------------------------------------
# T-EV-05 — GET /events/{id}: affected_detail with 【分析依據】
# ---------------------------------------------------------------------------


def test_ev05_get_event_detail_with_analysis_basis(client, engine):
    """對應 T-EV-05

    GET /events/{id} for an event whose affected_detail ends with a 【分析依據】
    paragraph returns 200 and the full paragraph is visible in the response.
    """
    from sqlalchemy.orm import sessionmaker as _sm
    from app.db.models.events import SecurityEvent as SE
    from app.utils.util_store import create_access_token

    # 同 T-EV-04 註：在 test 內自行補建 SecurityEvent（main _TASK_TABLES 含、client 不建）
    SE.__table__.create(bind=engine, checkfirst=True)

    Session_ = _sm(bind=engine)
    db = Session_()

    detail_with_basis = (
        "【異常發現】10.0.0.5 發送異常流量\n"
        "【風險分析】中風險\n"
        "【分析依據】參考公司資料『設備清冊』：IP 10.0.0.5 為研發部測試伺服器。"
    )
    ev = SE(
        event_date=date.today(),
        star_rank=3,
        title="10.0.0.5 異常流量",
        affected_summary="10.0.0.5 (研發部)",
        affected_detail=detail_with_basis,
        match_key="deny_internal_10.0.0.5_basis",
        detection_count=1,
        current_status="pending",
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    ev_id = ev.id
    db.close()

    token = create_access_token(user_id=1)
    resp = client.get(
        f"/events/{ev_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "【分析依據】" in (data.get("affected_detail") or "")
    assert "設備清冊" in (data.get("affected_detail") or "")


# ---------------------------------------------------------------------------
# Additional unit tests for _build_company_data_prompt
# ---------------------------------------------------------------------------


def test_build_company_data_prompt_empty():
    """Empty company_data returns empty string."""
    result = claude_pro._build_company_data_prompt([])
    assert result == ""


def test_build_company_data_prompt_with_data():
    """Company data injection includes correct structure."""
    rows = [
        {"name": "規範 A", "content": "內容 A"},
        {"name": "規範 B", "content": "內容 B"},
    ]
    result = claude_pro._build_company_data_prompt(rows)
    assert "【公司背景資料】" in result
    assert "共 2 筆" in result
    assert "規範 A" in result
    assert "內容 A" in result
    assert "規範 B" in result
    assert "【引用規則】" in result
    assert "其餘因長度未列入" not in result


def test_build_company_data_prompt_truncation(monkeypatch):
    """When total length exceeds max_tokens, header reports total vs included."""
    monkeypatch.setattr(
        "app.tasks.claude_pro.settings",
        type("S", (), {"sonnet_company_data_max_tokens": 50})(),
    )
    rows = [
        {"name": "規範 A", "content": "A" * 100},
        {"name": "規範 B", "content": "B" * 100},
    ]
    result = claude_pro._build_company_data_prompt(rows)
    assert "共 2 筆" in result
    assert "其餘因長度未列入" in result
