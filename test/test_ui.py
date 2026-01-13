import importlib
import os
import re
import tempfile

import pytest


def make_client(monkeypatch):
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    monkeypatch.setenv("POCKETBOOK_DB", db_path)
    import db as db_module
    import app as app_module
    importlib.reload(db_module)
    importlib.reload(app_module)
    client = app_module.app.test_client()
    return client, db_path


@pytest.fixture()
def ui_client(monkeypatch):
    client, db_path = make_client(monkeypatch)
    yield client
    if os.path.exists(db_path):
        os.remove(db_path)


def test_dashboard_range_tabs(ui_client):
    resp = ui_client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    for day in ("30", "90", "180", "365"):
        assert f'data-days="{day}"' in html


def test_transactions_sort_headers_and_modal(ui_client):
    resp = ui_client.get("/transactions")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    for key in ("date", "merchant", "description", "amount", "category"):
        assert f'data-sort="{key}"' in html
    assert html.count("sort-arrow") >= 5
    assert 'id="modal-status"' in html
    assert 'id="preview-section"' in html


def test_categories_page_has_status_and_form(ui_client):
    resp = ui_client.get("/categories")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'id="modal-status"' in html
    assert 'id="cat-name"' in html
    assert 'id="cat-color"' in html
    assert 'id="cat-budget"' in html
    assert 'id="save-cat-btn"' in html


def test_accounts_page_loads(ui_client):
    resp = ui_client.get("/accounts")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert re.search(r"Accounts", html)
