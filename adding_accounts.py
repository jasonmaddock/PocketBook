from datetime import datetime, timedelta
from typing import Dict, List
import requests
import logging

import aiohttp
import asyncio

from db import (
    TokensConnection,
    AccountsConnection,
    TransactionsConnection,
    RulesConnection,
    CategoryConnection,
)
from api_connection import ApiConnection
from classification import apply_rules, Rule

logger = logging.getLogger(__name__)

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
    try:
        amount_info = raw.get("transactionAmount") or raw.get("transacitonAmount") or {}
        amount = amount_info.get("amount", 0.0)
        currency = amount_info.get("currency", "")
        if not raw.get("internalTransactionId") and not raw.get("transactionId"):
            print("test")
        return {
            "provider_id": raw.get("internalTransactionId") or raw.get("transactionId"),
            "amount": amount,
            "currency": currency,
            "date": raw.get("bookingDate") or raw.get("valueDate"),
            "merchant": raw.get("creditorName") or raw.get("debtorName"),
            "description": raw.get("remittanceInformationUnstructured") or raw.get("additionalInformation"),
            "raw": raw,
        }
    except:
        print("test")


async def get_balances_and_transactions(account_list, user_id=1):
    con = TokensConnection()
    access_token = con.access_token
    logger.info("Fetching balances and transactions")
    tasks = [ApiConnection.get_balance_and_transactions(a['provider_account_id'], access_token) for a in account_list]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    successful_responses = []
    for response in responses:
        if isinstance(response, Exception):
            logger.error(f"Failed to fetch balances and transactions: {response}")
            continue
        logger.info(f"Successful fetch for {response['account_id']}")
        successful_responses.append(response)
    return successful_responses

def unpack_balances_and_transactions(response):
    balance_amount = float(response['response']["balances"][0]["balanceAmount"]["amount"])
    booked = response["transactions"].get("booked", [])
    pending = response["transactions"].get("pending", [])
    normalised = [_normalize_transaction(t) for t in booked + pending]
    return {"account_id": response["account_id"], "balance": balance_amount, "transactions": normalised}

async def coordinate_sync(account_list, user_id=1):
    tra = TransactionsConnection()
    rules_con = RulesConnection()
    rules = [Rule.from_row(r) for r in rules_con.list_rules()]
    balances_and_transactions = {}
    responses = await get_balances_and_transactions(account_list, user_id=1)
    for r in responses:
        normalised = unpack_balances_and_transactions(r)
        classified = apply_rules(normalised["transactions"], rules)
        tra.add_transactions(r["account_id"], user_id, classified)
        balances_and_transactions[r["account_id"]] = {
            "balance": r["balance"],
            "transactions": classified,
        }
    return {"accounts": balances_and_transactions, "errors": []}

async def get_balances_and_transactions_old(account_list, user_id=1):
    # con = TokensConnection()
    acc = AccountsConnection()
    tra = TransactionsConnection()
    rules_con = RulesConnection()
    # access_token = con.access_token

    # Convert DB rows to Rule objects for classification
    rules = [Rule.from_row(r) for r in rules_con.list_rules()]

    balances_and_transactions = {}
    errors: List[dict] = []
    logger.info("Fetching balances and transactions")
    tasks = [ApiConnection.get_balance_and_transactions(a['provider_account_id'], access_token) for a in account_list]
    account_ids = [a['provider_account_id']for a in account_list]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for response, account_id in zip(responses, account_ids):
        # if str(response.code)[0] != 2:
        #     logger.error(f"Failed to fetch for {account_id}. {response.code} - {response.message}")
        #     continue
        try:
            # logger.info(f"Successful fetch for {account_id}")
            balance_amount = float(response["balances"][0]["balanceAmount"]["amount"])
            acc.add_balance(account_id, balance_amount)

            booked = response["transactions"].get("booked", [])
            pending = response["transactions"].get("pending", [])
            normalized = [_normalize_transaction(t) for t in booked + pending]
            classified = apply_rules(normalized, rules)
            tra.add_transactions(account_id, user_id, classified)
            balances_and_transactions[account_id] = {
                "balance": balance_amount,
                "transactions": classified,
            }
        except aiohttp.ClientResponseError as err:
            status = getattr(err.response, "status_code", None)
            errors.append(
                {"account_id": account_id, "status": status, "error": str(err)}
            )
            continue
        except Exception as exc:
            errors.append(
                {"account_id": account_id, "status": None, "error": str(exc)}
            )
            continue
    logger.info(f"Balances and transactions returned.")
    return {"accounts": balances_and_transactions, "errors": errors}


if __name__ == "__main__":
    list_accounts()
