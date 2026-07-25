import httpx


def test_health(client_factory) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("Health check must not call Google.")

    with client_factory(handler) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "heypico-local-maps-assistant-api",
        "version": "0.1.0",
    }
