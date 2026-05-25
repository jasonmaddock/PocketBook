import importlib
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

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


def test_get_balance_and_transactions_uses_aiohttp_session(monkeypatch):
    import api_connection
    from test import assets

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        async def json(self):
            return self.payload

    class FakeGetContext:
        def __init__(self, payload):
            self.payload = payload

        async def __aenter__(self):
            return FakeResponse(self.payload)

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class FakeSession:
        def __init__(self):
            self.get = Mock(side_effect=[
                FakeGetContext(assets.mock_balance),
                FakeGetContext(assets.mock_trans),
            ])

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    fake_session = FakeSession()
    monkeypatch.setattr(api_connection.aiohttp, "ClientSession", lambda: fake_session)

    result = asyncio.run(
        api_connection.ApiConnection.get_balance_and_transactions(
            "account-id",
            "access-token",
        )
    )

    assert result == {
        "account_id": "account-id",
        "response": {
            "balances": assets.mock_balance["balances"],
            "transactions": assets.mock_trans["transactions"],
        },
    }
    assert fake_session.get.call_count == 2
    first_call, second_call = fake_session.get.call_args_list
    assert first_call.kwargs["url"].endswith("/accounts/account-id/balances/")
    assert second_call.kwargs["url"].endswith("/accounts/account-id/transactions/")
    assert first_call.kwargs["headers"]["Authorization"] == "Bearer access-token"


def test_get_balances_and_transactions_calls_api_for_each_account(monkeypatch):
    import adding_accounts
    from test import assets

    class DummyToken:
        @property
        def access_token(self):
            return "access-token"

    async def fake_get_balance_and_transactions(account_id, access_token):
        response = deepcopy(assets.mock_get_accounts_and_trans)
        response["account_id"] = account_id
        return response

    api_mock = AsyncMock(side_effect=fake_get_balance_and_transactions)

    monkeypatch.setattr(adding_accounts, "TokensConnection", DummyToken)
    monkeypatch.setattr(
        adding_accounts.ApiConnection,
        "get_balance_and_transactions",
        api_mock,
    )

    account_list = [
        {"provider_account_id": "account-1"},
        {"provider_account_id": "account-2"},
    ]

    result = asyncio.run(adding_accounts.get_balances_and_transactions(account_list))

    assert [r["account_id"] for r in result] == ["account-1", "account-2"]
    assert result[0]["response"] == assets.mock_get_accounts_and_trans["response"]
    assert result[1]["response"] == assets.mock_get_accounts_and_trans["response"]
    assert api_mock.await_count == 2
    api_mock.assert_any_await("account-1", "access-token")
    api_mock.assert_any_await("account-2", "access-token")



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
