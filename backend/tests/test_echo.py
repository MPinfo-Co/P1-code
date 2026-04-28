def test_echo_returns_message(client):
    """對應 T1"""
    resp = client.get("/api/echo?message=hello")
    assert resp.status_code == 200
    assert resp.json() == {"message": "ok", "data": "hello"}


def test_echo_missing_message_returns_422(client):
    """對應 T2"""
    resp = client.get("/api/echo")
    assert resp.status_code == 422
