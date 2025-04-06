from datetime import datetime, timedelta

from db import TokensConnection, AccountsConnection, TransactionsConnection
from api_connection import ApiConnection

def generate_bank_list(country_code="GB"):
    con = TokensConnection()
    access_token = con.access_token
    bank_list = ApiConnection.retrieve_bank_list(access_token, country_code)
    refined_list = []
    if country_code:
        for bank in bank_list:
            if country_code.upper() in bank["countries"]:
                refined_list.append(bank)
    return bank_list

def add_account(bank_id, user_id=1):
    con = TokensConnection()
    acc = AccountsConnection()
    access_token = con.access_token
    # eua = ApiConnection.create_eua(access_token, bank_id)
    # eua_id = eua["id"]
    # eua_ttl = eua["access_valid_for_days"]
    dt = datetime.now()
    valid_til = (dt + timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    req = ApiConnection.build_account_link(access_token, bank_id)
    input(f"""Follow the below link and hit enter here once you have completed the Authorisation.
{req["link"]}""")
    acc.store_account_info((user_id, bank_id, "None", req["id"], valid_til))
    return "Success"

def list_accounts(user_id=1):
    con = TokensConnection()
    acc = AccountsConnection()
    access_token = con.access_token
    account_list = []
    accounts = acc.retrieve_accounts(user_id)
    for account in accounts:
        account_list.append(ApiConnection.retrieve_accounts(account["ReqId"], access_token))    
    return account_list

def get_balances_and_transactions(account_list):
    con = TokensConnection()
    acc = AccountsConnection()
    tra = TransactionsConnection()
    access_token = con.access_token
    balances_and_transactions = {}
    for account in account_list:
        for account_id in account["accounts"]:
            b_n_t = ApiConnection.get_balance_and_transactions(account_id, access_token)
            balances_and_transactions[account_id] = {"balance": b_n_t["balances"][0]["balanceAmount"]["amount"], "transactions": b_n_t["transactions"]}
            acc.add_balance(account_id, balances_and_transactions[account_id]["balance"])
            tra.add_transactions(account_id, balances_and_transactions[account_id]["transactions"])
    return balances_and_transactions


if __name__ == "__main__":
    # generate_bank_list()
    # add_account("NATIONWIDE_NAIAGB21")
    list_accounts()




    