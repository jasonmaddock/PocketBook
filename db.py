from datetime import datetime, timedelta
import json
import os
import sqlite3
from typing import Iterable, List, Optional, Sequence, Tuple

from api_connection import ApiConnection as api

DB_PATH = os.getenv("POCKETBOOK_DB", "pocket.db")
DATE_FMT = "%Y-%m-%d %H:%M:%S"

TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS tokens(
    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_type TEXT,
    token TEXT,
    valid_for INTEGER,
    created_dt TEXT
);
"""

ACCOUNTS_TABLE = """
CREATE TABLE IF NOT EXISTS accounts(
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    bank_id TEXT,
    eua_id TEXT,
    req_id TEXT,
    provider_account_id TEXT,
    status TEXT DEFAULT 'pending',
    valid_til TEXT,
    balance REAL,
    balance_dt TEXT
);
"""

TRANSACTIONS_TABLE = """
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

CATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS categories(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    color TEXT,
    budget REAL DEFAULT 0
);
"""

SUBCATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS subcategories(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER,
    name TEXT,
    color TEXT,
    budget REAL DEFAULT 0,
    FOREIGN KEY(category_id) REFERENCES categories(id)
);
"""

RULES_TABLE = """
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
"""
DEBUG DB
import sqlite3
DB_PATH = os.getenv("POCKETBOOK_DB", "pocket.db")
con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row
cursor = con.cursor()
"""

class Db:
    def __init__(self, db_path=DB_PATH):
        self.con = sqlite3.connect(db_path)
        self.con.row_factory = sqlite3.Row
        self.cursor = self.con.cursor()
    
    table_name = ""

    def all_records(self):
        self.cursor.execute(f"SELECT * from {self.table_name}")
        return self.cursor.fetchall()


class TokensConnection(Db):
    add_token_sql = """INSERT INTO tokens (token_type, token, valid_for, created_dt)
                       VALUES (?, ?, ?, ?)"""
    table_name = "tokens"

    @property
    def access_token(self) -> str:
        self.cursor.execute("SELECT * FROM tokens WHERE token_type = 'access' ORDER BY created_dt DESC")
        tokens = self.cursor.fetchall()
        for token in tokens:
            expiry = datetime.strptime(token["created_dt"], DATE_FMT) + timedelta(seconds=token["valid_for"])
            if datetime.now() < expiry:
                return token["token"]
        return self.refresh_access_token()

    def refresh_access_token(self) -> str:
        self.cursor.execute("SELECT * FROM tokens WHERE token_type = 'refresh' ORDER BY created_dt DESC")
        tokens = self.cursor.fetchall()
        if not tokens:
            return self.generate_tokens()
        for token in tokens:
            dt = datetime.now()
            expiry = datetime.strptime(token["created_dt"], DATE_FMT) + timedelta(seconds=token["valid_for"])
            if dt < expiry:
                at = api.generate_access_token(token["token"])
                token_row = ("access", at["access"], at["access_expires"], dt.strftime(DATE_FMT))
                self.cursor.execute(self.add_token_sql, token_row)
                self.con.commit()
                return at["access"]
        return self.generate_tokens()

    def generate_tokens(self) -> str:
        at_rt = api.generate_access_refresh_token()
        dt = datetime.now().strftime(DATE_FMT)
        access_token_row = ("access", at_rt["access"], at_rt["access_expires"], dt)
        refresh_token_row = ("refresh", at_rt["refresh"], at_rt["refresh_expires"], dt)

        for token in (access_token_row, refresh_token_row):
            self.cursor.execute(self.add_token_sql, token)
        self.con.commit()
        return access_token_row[1]


class AccountsConnection(Db):
    def store_account_info(
        self,
        user_id: int,
        bank_id: str,
        eua_id: str,
        req_id: str,
        valid_til: str,
        provider_account_id: str = None,
        status: str = "pending",
    ):
        self.cursor.execute("SELECT account_id FROM accounts WHERE provider_account_id = ? AND status = 'active'", (provider_account_id,))
        existing = self.cursor.fetchone()
        if existing:
            self.cursor.execute(
                """
                UPDATE accounts SET eua_id = ?, req_id = ?, status = ?, valid_til = ? WHERE provider_account_id = ?
                """,
                (eua_id, req_id, status, valid_til, provider_account_id),
            )
            self.con.commit()
        else:
            self.cursor.execute(
                """
                INSERT INTO accounts (user_id, bank_id, eua_id, req_id, provider_account_id, status, valid_til)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, bank_id, eua_id, req_id, provider_account_id, status, valid_til),
            )
            self.con.commit()

    def retrieve_accounts(self, user_id: int = 1, pending_only: bool = False):
        if pending_only:
            self.cursor.execute(
                "SELECT * FROM accounts WHERE user_id = ? AND status = 'pending'",
                (user_id,)
            )
        else:
            self.cursor.execute("SELECT * FROM accounts WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()
    
    def add_balance(self, provider_account_id: str, balance: float):
        dt = datetime.now().strftime(DATE_FMT)
        self.cursor.execute(
            "UPDATE accounts SET balance = ?, balance_dt = ? WHERE provider_account_id = ?",
            (balance, dt, provider_account_id),
        )
        self.con.commit()

    def upsert_provider_account(self, req_id: str, provider_account_id: str, bank_id: str = None, user_id: int = 1, status: str = "active"):
        # If this provider account already exists, just update status/req_id
        self.cursor.execute("SELECT account_id FROM accounts WHERE provider_account_id = ?", (provider_account_id,))
        existing = self.cursor.fetchone()
        if existing:
            self.cursor.execute(
                "UPDATE accounts SET status = ?, req_id = ? WHERE provider_account_id = ?",
                (status, req_id, provider_account_id),
            )
            self.con.commit()
            return

        # Otherwise insert a new row, seeding fields from the requisition row if present
        self.cursor.execute("SELECT bank_id, eua_id, valid_til FROM accounts WHERE req_id = ? LIMIT 1", (req_id,))
        base = self.cursor.fetchone()
        seed_bank = bank_id or (base["bank_id"] if base else None)
        seed_eua = base["eua_id"] if base else None
        seed_valid = base["valid_til"] if base else None
        self.cursor.execute(
            """
            INSERT INTO accounts (user_id, bank_id, eua_id, req_id, provider_account_id, status, valid_til)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, seed_bank, seed_eua, req_id, provider_account_id, status, seed_valid),
        )
        self.con.commit()

    def activate_account(self, req_id: str, provider_account_id: str):
        self.cursor.execute(
            "UPDATE accounts SET status = 'active' WHERE req_id = ? AND provider_account_id = ?",
            (req_id, provider_account_id),
        )
        self.con.commit()

    def delete_account(self, account_id: int):
        # remove transactions for the account then the account row
        self.cursor.execute("DELETE FROM transactions WHERE account_id = ?", (account_id,))
        self.cursor.execute("DELETE FROM accounts WHERE account_id = ?", (account_id,))
        self.con.commit()


class CategoryConnection(Db):
    def add_category(self, name: str, color: str = None) -> int:
        self.cursor.execute(
            "INSERT INTO categories (name, color, budget) VALUES (?, ?, ?)",
            (name, color, 0),
        )
        self.con.commit()
        return self.cursor.lastrowid

    def list_categories(self):
        self.cursor.execute("SELECT * FROM categories ORDER BY name ASC")
        return self.cursor.fetchall()

    def update_category(self, category_id: int, name: str, color: str = None, budget: float = 0):
        self.cursor.execute(
            "UPDATE categories SET name = ?, color = ?, budget = ? WHERE id = ?",
            (name, color, budget, category_id),
        )
        self.con.commit()

    def delete_category(self, category_id: int):
        self.cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.con.commit()

    def get_category_colour(self, category_id: int) -> str: 
        self.cursor.execute("SELECT color FROM categories WHERE id = ?", (category_id,))
        row = self.cursor.fetchone()
        return row["color"] if row else None

    @property
    def default_category_id(self) -> int:
        self.cursor.execute("SELECT id FROM categories WHERE name = ?", ("Uncategorised",))
        row = self.cursor.fetchone()
        return row["id"] if row else 1


class SubcategoryConnection(Db):
    def add_subcategory(self, category_id: int, name: str, color: str = None, budget: float = 0) -> int:
        self.cursor.execute(
            "INSERT INTO subcategories (category_id, name, color, budget) VALUES (?, ?, ?, ?)",
            (category_id, name, color, budget),
        )
        self.con.commit()
        return self.cursor.lastrowid

    def list_subcategories(self, category_id: int = None):
        if category_id:
            self.cursor.execute("SELECT * FROM subcategories WHERE category_id = ? ORDER BY name ASC", (category_id,))
        else:
            self.cursor.execute("SELECT * FROM subcategories ORDER BY category_id ASC, name ASC")
        return self.cursor.fetchall()

    def update_subcategory(self, subcategory_id: int, name: str, color: str = None, budget: float = 0):
        self.cursor.execute(
            "UPDATE subcategories SET name = ?, color = ?, budget = ? WHERE id = ?",
            (name, color, budget, subcategory_id),
        )
        self.con.commit()

    def delete_subcategory(self, subcategory_id: int):
        self.cursor.execute("DELETE FROM subcategories WHERE id = ?", (subcategory_id,))
        self.con.commit()


class RulesConnection(Db):
    def add_rule(
        self,
        name: str,
        merchant_pattern: Optional[str],
        description_pattern: Optional[str],
        category_id: int,
        subcategory_id: Optional[int],
        fuzzy_threshold: float = 0.75,
        priority: int = 100,
    ) -> int:
        self.cursor.execute(
            """
            INSERT INTO rules (name, merchant_pattern, description_pattern, category_id, subcategory_id, fuzzy_threshold, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, merchant_pattern, description_pattern, category_id, subcategory_id, fuzzy_threshold, priority),
        )
        self.con.commit()
        return self.cursor.lastrowid

    def list_rules(self):
        self.cursor.execute(
            """
            SELECT rules.*, categories.name AS category_name, categories.color AS category_color,
                   subcategories.name AS subcategory_name
            FROM rules
            LEFT JOIN categories ON categories.id = rules.category_id
            LEFT JOIN subcategories ON subcategories.id = rules.subcategory_id
            ORDER BY priority ASC, rules.id ASC
            """
        )
        return self.cursor.fetchall()

    def list_by_cat(self, category_id = None, subcategory_id= None):
        clauses = []
        params = []
        if category_id or subcategory_id:
            clauses.append(" WHERE")
            if category_id and not subcategory_id:
                clauses.append(" category_id = ?")
                params.append(category_id)
            elif subcategory_id and not category_id:
                clauses.append(" subcategory_id = ?")
                params.append(subcategory_id)
            else:
                clauses.append(" category_id = ? AND subcategory_id = ?")
                params.extend([category_id, subcategory_id])

        statement = "".join(["SELECT * FROM rules", *clauses, ";"])
        self.cursor.execute(statement, tuple(params))
        return self.cursor.fetchall()

    def update_rule(
        self,
        rule_id: int,
        name: str,
        merchant_pattern: Optional[str],
        description_pattern: Optional[str],
        category_id: int,
        subcategory_id: Optional[int],
        fuzzy_threshold: float,
        priority: int,
    ):
        self.cursor.execute(
            """
            UPDATE rules
            SET name = ?, merchant_pattern = ?, description_pattern = ?, category_id = ?, subcategory_id = ?, fuzzy_threshold = ?, priority = ?
            WHERE id = ?
            """,
            (name, merchant_pattern, description_pattern, category_id, subcategory_id, fuzzy_threshold, priority, rule_id),
        )
        self.con.commit()

    def delete_rule(self, rule_id: int):
        self.cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        self.con.commit()

    def conflict(self, merchant_pattern: str, description_pattern: str) -> list:
        # Return any rule that matches either the merchant or description pattern
        self.cursor.execute(
            "SELECT * FROM rules WHERE (merchant_pattern = ?) OR (description_pattern = ?) LIMIT 1",
            (merchant_pattern, description_pattern),
        )
        return self.cursor.fetchone()

class TransactionsConnection(Db):
    table_name = "transactions"
    def add_transactions(self, account_id: int, user_id: int, transactions: Sequence[dict]):
        rows: List[Tuple] = []
        for t in transactions:
            rows.append(
                (
                    t["provider_id"],
                    account_id,
                    user_id,
                    t["amount"],
                    t["currency"],
                    t["date"],
                    t.get("merchant"),
                    t.get("description"),
                    t.get("category_id") or 1,
                    t.get("subcategory_id"),
                    t.get("rule_id"),
                    json.dumps(t.get("raw", {})),
                )
            )

        response = self.cursor.executemany(
            """
            INSERT OR IGNORE INTO transactions
            (provider_id, account_id, user_id, amount, currency, date, merchant, description, category_id, subcategory_id, rule_id, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.con.commit()

    def list_transactions(self, user_id: int, from_dt: str = None, to_dt: str = None, category_id: str = None):
        clauses = ["transactions.user_id = ?"]
        params = [user_id]
        if from_dt:
            clauses.append("transactions.date >= ?")
            params.append(from_dt)
        if to_dt:
            clauses.append("transactions.date <= ?")
            params.append(to_dt)
        if category_id:
            clauses.append("transactions.category_id = ?")
            params.append(category_id)
        where_clause = " AND ".join(clauses)
        self.cursor.execute(
            f"""
            SELECT transactions.*, categories.name AS category_name, categories.color AS category_color,
                   subcategories.name AS subcategory_name
            FROM transactions
            LEFT JOIN categories ON categories.id = transactions.category_id
            LEFT JOIN subcategories ON subcategories.id = transactions.subcategory_id
            WHERE {where_clause}
            ORDER BY date DESC
            """,
            tuple(params),
        )
        return self.cursor.fetchall()

    def update_category(self, tx_id: int, category_id: Optional[int] = None, rule_id: Optional[int] = None, subcategory_id: Optional[int] = None):
        self.cursor.execute(
            "UPDATE transactions SET category_id = ?, subcategory_id = ?, rule_id = ? WHERE id = ?",
            (category_id, subcategory_id, rule_id, tx_id),
        )
        self.con.commit()
    
