"""
SQLite migration helper to align an existing PocketBook database with the
current schema (categories model, rule/transaction category IDs, provider accounts, etc.).

Run: python3 migrate_db.py

It will:
- Create missing tables (categories, rules).
- Ensure a default 'Uncategorized' category exists.
- Add any missing columns to accounts/transactions.
- Convert legacy rule/transaction category text into category IDs.
- Upgrade legacy tokens table shape if needed.

Make sure to back up pocket.db before running (a .bak copy is recommended).
"""
import os
import sqlite3
from typing import Dict

DB_PATH = os.getenv("POCKETBOOK_DB", "pocket.db")
DATE_FMT = "%Y-%m-%d %H:%M:%S"


def has_column(cur, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def ensure_categories(cur) -> Dict[str, int]:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            color TEXT,
            budget REAL DEFAULT 0
        );
        """
    )
    if not has_column(cur, "categories", "budget"):
        cur.execute("ALTER TABLE categories ADD COLUMN budget REAL DEFAULT 0")
    cur.execute("INSERT OR IGNORE INTO categories (name, color, budget) VALUES (?, ?, ?)", ("Uncategorized", "#6b7280", 0))
    cur.connection.commit()

    cur.execute("SELECT id, name FROM categories")
    return {row["name"]: row["id"] for row in cur.fetchall()}


def migrate_tokens(cur):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tokens'")
    if not cur.fetchone():
        return
    # If already in new shape, skip
    if has_column(cur, "tokens", "token_type"):
        return
    # Legacy columns: TokenType, Token, ValidFor, CreatedDt
    cur.execute(
        """
        CREATE TABLE tokens_new(
            token_id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_type TEXT,
            token TEXT,
            valid_for INTEGER,
            created_dt TEXT
        );
        """
    )
    cur.execute("INSERT INTO tokens_new (token_type, token, valid_for, created_dt) SELECT TokenType, Token, ValidFor, CreatedDt FROM tokens")
    cur.execute("DROP TABLE tokens")
    cur.execute("ALTER TABLE tokens_new RENAME TO tokens")
    cur.connection.commit()


def migrate_accounts(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts(
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bank_id TEXT,
            eua_id TEXT,
            req_id TEXT,
            provider_account_id TEXT,
            valid_til TEXT,
            balance REAL,
            balance_dt TEXT
        );
        """
    )
    if not has_column(cur, "accounts", "provider_account_id"):
        cur.execute("ALTER TABLE accounts ADD COLUMN provider_account_id TEXT")
    if not has_column(cur, "accounts", "balance"):
        cur.execute("ALTER TABLE accounts ADD COLUMN balance REAL")
    if not has_column(cur, "accounts", "balance_dt"):
        cur.execute("ALTER TABLE accounts ADD COLUMN balance_dt TEXT")
    cur.connection.commit()


def migrate_rules(cur, category_ids: Dict[str, int]):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS rules(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            merchant_pattern TEXT,
            description_pattern TEXT,
            category_id INTEGER,
            subcategory_id INTEGER,
            fuzzy_threshold REAL DEFAULT 0.75,
            priority INTEGER DEFAULT 100,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        );
        """
    )
    if not has_column(cur, "rules", "category_id"):
        cur.execute("ALTER TABLE rules ADD COLUMN category_id INTEGER")
    if not has_column(cur, "rules", "subcategory_id"):
        cur.execute("ALTER TABLE rules ADD COLUMN subcategory_id INTEGER")
    # Backfill category_id from legacy text column if present
    if has_column(cur, "rules", "category"):
        cur.execute("SELECT id, category FROM rules WHERE category_id IS NULL OR category_id = ''")
        for row in cur.fetchall():
            cid = category_ids.get(row["category"]) or category_ids["Uncategorized"]
            cur.execute("UPDATE rules SET category_id = ? WHERE id = ?", (cid, row["id"]))
    cur.connection.commit()


def migrate_transactions(cur, category_ids: Dict[str, int]):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id TEXT UNIQUE,
            account_id INTEGER,
            user_id INTEGER,
            amount REAL,
            currency TEXT,
            date TEXT,
            merchant TEXT,
            description TEXT,
            category_id INTEGER,
            subcategory_id INTEGER,
            rule_id INTEGER,
            raw_json TEXT
        );
        """
    )
    if not has_column(cur, "transactions", "category_id"):
        cur.execute("ALTER TABLE transactions ADD COLUMN category_id INTEGER")
    if not has_column(cur, "transactions", "subcategory_id"):
        cur.execute("ALTER TABLE transactions ADD COLUMN subcategory_id INTEGER")
    # Backfill from legacy text column if present
    if has_column(cur, "transactions", "category"):
        cur.execute("SELECT id, category FROM transactions WHERE category_id IS NULL")
        for row in cur.fetchall():
            cid = category_ids.get(row["category"]) or category_ids["Uncategorized"]
            cur.execute("UPDATE transactions SET category_id = ? WHERE id = ?", (cid, row["id"]))
    cur.connection.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    migrate_tokens(cur)
    migrate_accounts(cur)
    category_ids = ensure_categories(cur)
    migrate_rules(cur, category_ids)
    migrate_transactions(cur, category_ids)

    conn.commit()
    conn.close()
    print("Migration complete for", DB_PATH)


if __name__ == "__main__":
    main()
