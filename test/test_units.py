import importlib
from types import SimpleNamespace

import pytest


def fake_response(payload, status=200):
    class Resp:
        def __init__(self, data, status_code):
            self._data = data
            self.status_code = status_code

        def json(self):
            return self._data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception("HTTP error")

    return Resp(payload, status)


def test_api_connection_requests(monkeypatch):
    import api_connection

    called = {}

    def fake_post(url=None, headers=None, json=None, timeout=None):
        called["url"] = url
        called["headers"] = headers
        called["json"] = json
        return fake_response({"access": "token", "access_expires": 1, "refresh": "r", "refresh_expires": 2})

    monkeypatch.setattr(api_connection.requests, "post", fake_post)
    resp = api_connection.ApiConnection.generate_access_refresh_token()
    assert resp["access"] == "token"
    assert "application/json" in called["headers"]["Content-Type"]
    assert called["json"]["secret_id"] == api_connection.SECRET_ID


def test_generate_bank_list_filters(monkeypatch):
    import adding_accounts

    class DummyToken:
        @property
        def access_token(self):
            return "tok"

    def fake_list(access_token, country):
        assert access_token == "tok"
        return [
            {"id": "a", "countries": ["GB"]},
            {"id": "b", "countries": ["US"]},
        ]

    monkeypatch.setattr(adding_accounts, "TokensConnection", DummyToken)
    monkeypatch.setattr(adding_accounts.ApiConnection, "retrieve_bank_list", fake_list)

    gb_list = adding_accounts.generate_bank_list("GB")
    assert [b["id"] for b in gb_list] == ["a"]
    all_list = adding_accounts.generate_bank_list("")
    assert len(all_list) == 2


def test_normalize_transaction():
    import adding_accounts

    raw = {
        "transactionId": "id1",
        "transactionAmount": {"amount": 10.5, "currency": "GBP"},
        "bookingDate": "2025-01-01",
        "creditorName": "Shop",
        "remittanceInformationUnstructured": "Desc",
    }
    norm = adding_accounts._normalize_transaction(raw)
    assert norm["provider_id"] == "id1"
    assert norm["amount"] == 10.5
    assert norm["merchant"] == "Shop"
    assert norm["description"] == "Desc"


def test_config_dummy(monkeypatch):
    # Reload config with empty env to get dummy values
    monkeypatch.setenv("GOCARDLESS_SECRET_KEY", "")
    monkeypatch.setenv("GOCARDLESS_SECRET_ID", "")
    # Prevent .env loading
    cfg_mod = importlib.import_module("config")
    monkeypatch.setattr(cfg_mod, "_load_env_file", lambda filename=".env": None)
    cfg = importlib.reload(cfg_mod)
    assert cfg.GOCARDLESS_SECRET_KEY == "DUMMY"
    assert cfg.GOCARDLESS_SECRET_ID == "DUMMY"
