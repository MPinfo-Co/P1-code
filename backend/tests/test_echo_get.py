"""
Tests for GET /api/echo endpoint (Issue #96)
"""


def test_echo_returns_message(client):
    """對應 T1：傳入 message=hello，應回傳 HTTP 200 及正確 JSON 結構"""
    resp = client.get("/api/echo", params={"message": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "ok"
    assert body["data"]["message"] == "hello"


def test_echo_missing_message_returns_422(client):
    """對應 T2：未傳入 message 參數，應回傳 HTTP 422 驗證錯誤"""
    resp = client.get("/api/echo")
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
