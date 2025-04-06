from datetime import datetime, timedelta

import sqlite3

from api_connection import ApiConnection as api

BASE_API_URL = "https://bankaccountdata.gocardless.com/api/v2/"

class Db:
    def __init__(self):
        self.con = sqlite3.connect("pocket.db")
        self.con.row_factory = sqlite3.Row
        self.cursor = self.con.cursor()

class TokensConnection(Db):

    add_token_sql = f"""INSERT INTO tokens (TokenType,Token,ValidFor,CreatedDt)
                        VALUES(?,?,?,?)"""


    @property
    def access_token(self):
        self.cursor.execute("SELECT * from tokens WHERE TokenType='access'")
        tokens = self.cursor.fetchall()
        for token in tokens:  ## For another day - Shouldnt we calculate token expirey on creation and then just look for valid tokens in the SQL search? Much simpler
            expiry = datetime.strptime(token["CreatedDt"], "%Y-%m-%d %H:%M:%S") + timedelta(seconds=token["Validfor"])
            valid = datetime.now() < expiry
            if valid:
                return token["token"]
        return self.refresh_access_token()

    def refresh_access_token(self):
        self.cursor.execute("SELECT * from tokens WHERE TokenType='refresh'")
        tokens = self.cursor.fetchall()
        if not tokens:
            return self.generate_tokens()
        for token in tokens:
            dt = datetime.now()
            expiry = datetime.strptime(token["CreatedDt"], "%Y-%m-%d %H:%M:%S") + timedelta(seconds=token["Validfor"])
            valid = dt < expiry
            if valid:
                at = api.generate_access_token(token["token"])
                token = ("access", at["access"], at["access_expires"], dt.strftime("%Y-%m-%d %H:%M:%S"))
                self.cursor.execute(self.add_token_sql, token)
                self.con.commit()
                return at["access"]
        return self.generate_tokens()

    def generate_tokens(self,):
        at_rt = api.generate_access_refresh_token()
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        access_token = ("access", at_rt["access"], at_rt["access_expires"], dt)
        refresh_token = ("refresh", at_rt["refresh"], at_rt["refresh_expires"], dt)
        
        for token in [access_token, refresh_token]:
            self.cursor.execute(self.add_token_sql, token)
        self.con.commit()
        return access_token


class AccountsConnection(Db):
    def store_account_info(self, args):
        self.cursor.execute(
            "INSERT INTO accounts (UserId, BankId, EuaId, ReqId, ValidTil) VALUES (?,?,?,?,?)",
            args
            )
        self.con.commit()

    def retrieve_accounts(self, user_id):
        self.cursor.execute(
            "SELECT * FROM accounts WHERE UserId = ?", (user_id,)
        )
        return self.cursor.fetchall()
    
    def add_balance(self, acc_id, balance):
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "UPDATE accounts SET Balance = (?), BalanceDt = (?) WHERE AccId = (?)",
            (balance, dt, acc_id,)
        )
        self.con.commit()


class TransactionsConnection(Db):
    def add_transactions(self, transacitons, acc_id, user_id):
        trans = [
            (
                t["transactionId"],
                acc_id, 
                user_id, 
                t["transacitonAmount"]["amount"], 
                t["bookingDate"], 
                t.get("debtorName") or t.get("creditorName"),
                t["remittanceInformationUnstructured"],
            ) for t in transacitons
        ]
        self.cursor.executemany("INSERT INTO transactions (ID, AccountId, UserId , Amount, Date, Debtor, Description) VALUES (?,?,?,?,?,?,?)")
        self.con.commit()
    