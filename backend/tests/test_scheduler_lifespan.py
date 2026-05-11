import pathlib
from fastapi.testclient import TestClient
from app.main import app
from app import scheduler


def test_lifespan_starts_and_stops_scheduler():
    assert scheduler._scheduler is None
    with TestClient(app):
        s = scheduler._scheduler
        assert s is not None and s.running is True
        job_ids = {j.id for j in s.get_jobs()}
        assert "haiku_job" in job_ids
        assert "sonnet_job" in job_ids
        assert "settings_sync" in job_ids
    assert scheduler._scheduler is None or not scheduler._scheduler.running


def test_no_celery_imports_in_repo():
    repo = pathlib.Path(__file__).resolve().parents[1]
    bad = []
    for py in repo.rglob("*.py"):
        if (
            ".venv" in py.parts
            or "old_task" in py.parts
            or py == pathlib.Path(__file__).resolve()
        ):
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        if "import celery" in text or "from celery" in text:
            bad.append(str(py))
    assert bad == [], f"celery still imported in: {bad}"


def test_no_old_task_or_worker_files():
    repo = pathlib.Path(__file__).resolve().parents[1]
    assert not (repo / "app" / "worker.py").exists()
    assert not (repo / "app" / "tasks" / "old_task").exists()
    assert not (repo / "app" / "tasks" / "cybersecurity_scheduler.py").exists()
