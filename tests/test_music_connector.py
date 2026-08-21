import requests

from dntl_datos.connectors import music


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_get_json_retries_transient_503(monkeypatch):
    responses = iter([
        FakeResponse(503),
        FakeResponse(200, {"artists": []}),
    ])
    sleeps = []

    monkeypatch.setattr(music.requests, "get", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr(music.time, "sleep", lambda seconds: sleeps.append(seconds))

    payload = music._get_json(
        "https://example.test/api",
        params={"q": "peru"},
        timeout=1,
        attempts=3,
    )

    assert payload == {"artists": []}
    assert len(sleeps) == 1
    assert sleeps[0] >= 1.2
