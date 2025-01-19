from datetime import datetime, timedelta

import sqlite3

from api_connection import ApiConnection as api

BASE_API_URL = "https://bankaccountdata.gocardless.com/api/v2/"


class TokensConnection:
    con = sqlite3.connect("pocket.db")
    cursor = con.cursor()

    add_token_sql = """INSERT INTO tokens (TokenType,Token,ValidTil,CreatedDT)
                        VALUES(?,?,?,?)"""


    @property
    def access_token(self):
        self.cursor.execute("SELECT * from tokens")
        tokens = self.cursor.fetchall()
        for token in tokens:
            expiry = token["CreatedDT"] + timedelta(seconds=token["Validfor"])
            valid = datetime.now() < expiry
            if valid:
                return token
        return self.handle_tokens(tokens)

    def handle_tokens(self, tokens):
        rt = None
        for token in tokens:
            type = token["TokenType"]
            expiry = token["CreatedDT"] + timedelta(seconds=token["Validfor"])
            valid = datetime < expiry
            if valid:
                if type == "access_token":
                    return token
                elif type == "refresh_token":
                    rt = token["token"]
        if rt:
            at = api.generate_access_token(rt)
            self.cursor.execute(self.add_token_sql, at)
            access_token = at["token"]
        else:
            at_rt = api.generate_access_refresh_token()
            for token in at_rt:
                if token["TokenType"] == "access_token":
                    access_token = token["token"]
                self.cursor.execute(self.add_token_sql, token)
        return access_token
            



        
    