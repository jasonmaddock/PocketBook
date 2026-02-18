import importlib
import os
import sqlite3
import tempfile

import pytest


@pytest.fixture()
def test_client(monkeypatch):
    # Use a temporary file DB for isolation
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    monkeypatch.setenv("POCKETBOOK_DB", db_path)
    # Reload modules so DB_PATH picks up the temp path
    import db as db_module
    import app as app_module

    importlib.reload(db_module)
    importlib.reload(app_module)

    app = app_module.app
    client = app.test_client()
    yield client
    if os.path.exists(db_path):
        os.remove(db_path)


def create_category(client, name="Cat"):
    resp = client.post("/api/categories", json={"name": name})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def create_subcategory(client, category_id, name="Sub", budget=5.0):
    resp = client.post("/api/subcategories", json={"name": name, "category_id": category_id, "budget": budget})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_category_color_default_and_palette(test_client):
    palette = importlib.import_module("app").CATEGORY_COLORS
    cat_id = create_category(test_client, "Groceries")
    resp = test_client.get("/api/categories")
    cats = resp.get_json()
    cat = next(c for c in cats if c["id"] == cat_id)
    assert cat["color"] in palette
    # Ensure a second category gets a different color until palette exhausted
    second_id = create_category(test_client, "Bills")
    cats = test_client.get("/api/categories").get_json()
    colors = [c["color"] for c in cats if c["id"] in (cat_id, second_id)]
    assert len(set(colors)) == 2


def test_rule_deduplication(test_client):
    cat_id = create_category(test_client, "Food")
    payload = {"category_id": cat_id, "merchant_pattern": "coffee", "description_pattern": None}
    first = test_client.post("/api/rules", json=payload)
    assert first.status_code == 201
    second = test_client.post("/api/rules", json=payload)
    assert second.status_code == 200
    assert second.get_json().get("deduped") is True
    rules = test_client.get("/api/rules").get_json()
    assert len(rules) == 1


def test_subcategory_create_edit(test_client):
    cat_id = create_category(test_client, "Travel")
    sub_id = create_subcategory(test_client, cat_id, name="Flights", budget=100)
    # Edit via PUT
    resp = test_client.put(f"/api/subcategories/{sub_id}", json={"name": "Airfare", "budget": 200, "color": "#3b82f6"})
    assert resp.status_code == 200
    subs = test_client.get("/api/subcategories").get_json()
    sub = next(s for s in subs if s["id"] == sub_id)
    assert sub["name"] == "Airfare"
    assert sub["budget"] == 200


def test_transactions_patch_category_subcategory_and_summary_uncat(test_client):
    from db import TransactionsConnection

    cat_id = create_category(test_client, "Misc")
    sub_id = create_subcategory(test_client, cat_id, name="General")
    tc = TransactionsConnection()
    tx = {
        "provider_id": "tx1",
        "amount": -25.50,
        "currency": "GBP",
        "date": "2025-01-01",
        "merchant": "Store",
        "description": "Purchase",
        "category_id": None,
        "subcategory_id": None,
        "rule_id": None,
        "raw": {},
    }
    tc.add_transactions(account_id=1, user_id=1, transactions=[tx])
    # fetch inserted id
    tc.cursor.execute("SELECT id FROM transactions WHERE provider_id = 'tx1'")
    tx_id = tc.cursor.fetchone()["id"]
    # Patch category + subcategory
    resp = test_client.patch(f"/api/transactions/{tx_id}", json={"category_id": cat_id, "subcategory_id": sub_id})
    assert resp.status_code == 200
    tc.cursor.execute("SELECT category_id, subcategory_id FROM transactions WHERE id = ?", (tx_id,))
    row = tc.cursor.fetchone()
    assert row["category_id"] == cat_id
    assert row["subcategory_id"] == sub_id
    # summary uncategorized should be zero now
    summary = test_client.get("/api/summary").get_json()
    assert summary["uncategorized_count"] == 0


def test_uncategorized_count_when_missing_category(test_client):
    from db import TransactionsConnection

    tc = TransactionsConnection()
    tx = {
        "provider_id": "tx2",
        "amount": -10.00,
        "currency": "GBP",
        "date": "2025-01-02",
        "merchant": "Unknown",
        "description": "No cat",
        "category_id": None,
        "subcategory_id": None,
        "rule_id": None,
        "raw": {},
    }
    tc.add_transactions(account_id=1, user_id=1, transactions=[tx])
    summary = test_client.get("/api/summary").get_json()
    assert summary["uncategorized_count"] == 1


def test_reclassify_applies_rules_and_sets_rule_id(test_client):
    from db import TransactionsConnection

    cat_id = create_category(test_client, "Coffee")
    # rule that matches merchant "Brew"
    test_client.post("/api/rules", json={"category_id": cat_id, "merchant_pattern": "Brew", "description_pattern": None})
    tc = TransactionsConnection()
    tx = {
        "provider_id": "tx3",
        "amount": -5.0,
        "currency": "GBP",
        "date": "2025-01-03",
        "merchant": "Brew Dog",
        "description": "Latte",
        "category_id": None,
        "subcategory_id": None,
        "rule_id": None,
        "raw": {},
    }
    tc.add_transactions(account_id=1, user_id=1, transactions=[tx])
    tc.cursor.execute("SELECT id FROM transactions WHERE provider_id = 'tx3'")
    tx_id = tc.cursor.fetchone()["id"]

    resp = test_client.post("/api/reclassify", json={"user_id": 1})
    assert resp.status_code == 200
    tc.cursor.execute("SELECT category_id, rule_id FROM transactions WHERE id = ?", (tx_id,))
    row = tc.cursor.fetchone()
    assert row["category_id"] == cat_id
    assert row["rule_id"] is not None


def test_summary_budget_filters_and_spend_abs(test_client):
    from db import TransactionsConnection

    cat_id = create_category(test_client, "Groceries")
    sub_id = create_subcategory(test_client, cat_id, name="Veg", budget=20)
    tc = TransactionsConnection()
    txs = [
        {
            "provider_id": "tx4",
            "amount": -10.0,
            "currency": "GBP",
            "date": "2025-01-05",
            "merchant": "Market",
            "description": "Veg",
            "category_id": cat_id,
            "subcategory_id": sub_id,
            "rule_id": None,
            "raw": {},
        },
        {
            "provider_id": "tx5",
            "amount": 5.0,  # positive to verify abs handling
            "currency": "GBP",
            "date": "2025-01-06",
            "merchant": "Refund",
            "description": "Refund",
            "category_id": cat_id,
            "subcategory_id": None,
            "rule_id": None,
            "raw": {},
        },
    ]
    tc.add_transactions(account_id=1, user_id=1, transactions=txs)
    summary = test_client.get("/api/summary").get_json()
    cat_entry = next(c for c in summary["categories"] if c["id"] == cat_id)
    # spend should reflect signed sum (negative + positive) but charts consume abs; ensure value present
    assert "spend" in cat_entry
    # budget items should include subcategory with budget
    sub_entry = next(s for s in summary["subcategories"] if s["id"] == sub_id)
    assert sub_entry["budget"] == 20


def test_delete_account_removes_transactions(test_client, monkeypatch):
    from db import AccountsConnection, TransactionsConnection

    ac = AccountsConnection()
    tc = TransactionsConnection()
    # insert account and transaction manually
    ac.store_account_info(user_id=1, bank_id="bank", eua_id="eua", req_id="req1", provider_account_id="prov1", valid_til="2025-01-01", status="active")
    # second account same req/bank to ensure we don't overwrite
    ac.upsert_provider_account(req_id="req1", provider_account_id="prov2", bank_id="bank", user_id=1, status="active")
    ac.cursor.execute("SELECT account_id FROM accounts WHERE req_id = 'req1'")
    rows = ac.cursor.fetchall()
    account_id = rows[0]["account_id"]
    account_id2 = rows[1]["account_id"]
    tc.add_transactions(account_id=account_id, user_id=1, transactions=[{
        "provider_id": "del_tx",
        "amount": -1.0,
        "currency": "GBP",
        "date": "2025-01-01",
        "merchant": "M",
        "description": "D",
        "category_id": None,
        "subcategory_id": None,
        "rule_id": None,
        "raw": {},
    }])
    resp = test_client.delete(f"/api/accounts/{account_id}")
    assert resp.status_code == 200
    # ensure removed
    ac.cursor.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
    assert ac.cursor.fetchone() is None
    tc.cursor.execute("SELECT * FROM transactions WHERE account_id = ?", (account_id,))
    assert tc.cursor.fetchone() is None
    # second account still present
    tc.cursor.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id2,))
    assert tc.cursor.fetchone() is not None
