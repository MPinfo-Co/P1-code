"""Tests for haiku_task orchestrator (Task 6 — sd-209)."""


class FakeSSB:
    def __init__(self, logs):
        self.logs = logs
        self.calls = 0

    def fetch_logs(self, *, time_from, time_to, search_expression):
        self.calls += 1
        return self.logs
