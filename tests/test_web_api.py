from fastapi.testclient import TestClient

import dntl_datos.web_api as web_api


def _client_without_data(monkeypatch, tmp_path):
    missing = tmp_path / "missing-data"
    monkeypatch.setattr(web_api, "DATA_ROOT", str(missing))
    return TestClient(web_api.app)


def test_health(monkeypatch, tmp_path):
    client = _client_without_data(monkeypatch, tmp_path)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.2.0"


def test_summary_falls_back_to_validated_demo_counts(monkeypatch, tmp_path):
    client = _client_without_data(monkeypatch, tmp_path)
    response = client.get("/api/summary")
    payload = response.json()

    assert response.status_code == 200
    assert payload["data_mode"] == "demo"
    assert payload["market_rows"] == 9402
    assert payload["artist_rows"] == 1424
    assert payload["catalog_rows"] == 14


def test_markets_demo_never_invents_prices(monkeypatch, tmp_path):
    client = _client_without_data(monkeypatch, tmp_path)
    payload = client.get("/api/markets").json()

    assert payload["data_mode"] == "demo"
    assert payload["items"]
    assert all(item["close"] is None for item in payload["items"])


def test_artist_demo_is_searchable_endpoint(monkeypatch, tmp_path):
    client = _client_without_data(monkeypatch, tmp_path)
    payload = client.get("/api/artists?q=peru").json()

    assert payload["data_mode"] == "demo"
    assert len(payload["items"]) >= 1
    assert "artist_name" in payload["items"][0]


def test_ask_routes_music_questions(monkeypatch, tmp_path):
    client = _client_without_data(monkeypatch, tmp_path)
    payload = client.get("/api/ask", params={"q": "Cuántos artistas de música peruana tenemos?"}).json()

    assert payload["route"] == "music"
    assert "1,424" in payload["answer"]
    assert payload["data_mode"] == "demo"
