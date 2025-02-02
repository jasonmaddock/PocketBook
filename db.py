from datetime import datetime, timedelta

import sqlite3

from api_connection import ApiConnection as api

BASE_API_URL = "https://bankaccountdata.gocardless.com/api/v2/"


class TokensConnection:
    def __init__(self):
        self.con = sqlite3.connect("pocket.db")
        self.con.row_factory = sqlite3.Row
        self.cursor = self.con.cursor()

    add_token_sql = f"""INSERT INTO tokens (TokenType,Token,ValidFor,CreatedDt)
                        VALUES(?,?,?,?)"""


    @property
    def access_token(self):
        self.cursor.execute("SELECT * from tokens WHERE TokenType='access'")
        tokens = self.cursor.fetchall()
        for token in tokens:
            expiry = datetime.strptime(token["CreatedDt"], "%Y-%m-%d %H:%M:%S") + timedelta(seconds=token["Validfor"])
            valid = datetime.now() < expiry
            if valid:
                return token["token"]
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
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            access_token = ("access", at_rt["access"], at_rt["access_expires"], dt)
            refresh_token = ("refresh", at_rt["refresh"], at_rt["refresh_expires"], dt)
            
            for token in [access_token, refresh_token]:
                self.cursor.execute(self.add_token_sql, token)
        self.con.commit()
        return access_token
            



        
    