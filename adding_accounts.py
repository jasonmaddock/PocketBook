from db import TokensConnection
from api_connection import ApiConnection

def bank_list():
    con = TokensConnection()
    access_token = con.access_token
    bank_list = ApiConnection.retrieve_bank_list(access_token=access_token)
    print(bank_list)

bank_list()
    