from datetime import datetime, timedelta
from typing import Dict, List
import requests

from db import (
    TokensConnection,
    AccountsConnection,
    TransactionsConnection,
    RulesConnection,
    CategoryConnection,
)
from api_connection import ApiConnection
from classification import apply_rules, Rule


def generate_bank_list(country_code: str = "GB"):
    con = TokensConnection()
    access_token = con.access_token
    bank_list = ApiConnection.retrieve_bank_list(access_token, country_code)
    if not country_code:
        return bank_list

    refined_list = []
    for bank in bank_list:
        if country_code.upper() in bank.get("countries", []):
            refined_list.append(bank)
    return refined_list


def add_account(bank_id, user_id=1, prompt=True):
    con = TokensConnection()
    acc = AccountsConnection()
    access_token = con.access_token

    dt = datetime.now()
    valid_til = (dt + timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    req = ApiConnection.build_account_link(access_token, bank_id)
    if prompt:
        input(
            f"""Follow the below link and hit enter here once you have completed the Authorisation.
{req["link"]}"""
        )
    acc.store_account_info(user_id, bank_id, req.get("agreement") or "None", req["id"], valid_til)
    return {"link": req["link"], "req_id": req["id"], "valid_til": valid_til}


def create_requisition(bank_id, user_id=1):
    # Wrapper used by the API/GUI; no blocking prompt, returns link for the user.
    return add_account(bank_id, user_id=user_id, prompt=False)


def list_accounts(user_id=1, pending_only: bool = False):
    acc = AccountsConnection()
    return acc.retrieve_accounts(user_id, pending_only=pending_only)

def activate_account(account):
    con = TokensConnection()
    acc = AccountsConnection()
    access_token = con.access_token
    api_account = ApiConnection.retrieve_accounts(account["req_id"], access_token)
    provider_account_ids = api_account['accounts']
    for id in provider_account_ids:
        acc.store_account_info(
            account['user_id'],
            account['bank_id'],
            account['eua_id'],
            account['req_id'], 
            account['valid_til'],
            id,
            "active"
            )
    acc.delete_account(account['account_id'])



def _normalize_transaction(raw: dict) -> Dict:
    amount_info = raw.get("transactionAmount") or raw.get("transacitonAmount") or {}
    amount = amount_info.get("amount", 0.0)
    currency = amount_info.get("currency", "")
    return {
        "provider_id": raw.get("transactionId") or raw.get("internalTransactionId"),
        "amount": amount,
        "currency": currency,
        "date": raw.get("bookingDate") or raw.get("valueDate"),
        "merchant": raw.get("creditorName") or raw.get("debtorName"),
        "description": raw.get("remittanceInformationUnstructured") or raw.get("additionalInformation"),
        "raw": raw,
    }


def get_balances_and_transactions(account_list, user_id=1):
    con = TokensConnection()
    acc = AccountsConnection()
    tra = TransactionsConnection()
    rules_con = RulesConnection()
    cat_con = CategoryConnection()
    subcat_con = None
    access_token = con.access_token

    # Convert DB rows to Rule objects for classification
    rules = [Rule.from_row(r) for r in rules_con.list_rules()]
    default_category_id = cat_con.default_category_id

    balances_and_transactions = {}
    errors: List[dict] = []
    for account in account_list:
        try:
            account_id = account['provider_account_id']
            # acc.upsert_provider_account(account["req_id"], account_id, bank_id=account.get("bank_id"), user_id=user_id)
            # acc.activate_account(account["req_id"], account_id)
            b_n_t = ApiConnection.get_balance_and_transactions(account_id, access_token)
            balance_amount = float(b_n_t["balances"][0]["balanceAmount"]["amount"])
            acc.add_balance(account_id, balance_amount)

            booked = b_n_t["transactions"].get("booked", [])
            pending = b_n_t["transactions"].get("pending", [])
            normalized = [_normalize_transaction(t) for t in booked + pending]
            classified = apply_rules(normalized, rules, default_category_id)
            tra.add_transactions(account_id, user_id, classified)
            balances_and_transactions[account_id] = {
                "balance": balance_amount,
                "transactions": classified,
            }
        except requests.exceptions.HTTPError as err:
            status = getattr(err.response, "status_code", None)
            errors.append(
                {"account_id": account_id, "req_id": account.get("req_id"), "status": status, "error": str(err)}
            )
            continue
        except Exception as exc:
            errors.append(
                {"account_id": account_id, "req_id": account.get("req_id"), "status": None, "error": str(exc)}
            )
            continue

    return {"accounts": balances_and_transactions, "errors": errors}


if __name__ == "__main__":
    list_accounts()
