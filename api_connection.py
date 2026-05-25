import json
import os
import requests
import config
from typing import Any, Dict

import aiohttp
import asyncio

BASE_API_URL = "https://bankaccountdata.gocardless.com/api/v2/"
SECRET_ID = config.GOCARDLESS_SECRET_ID
SECRET_KEY = config.GOCARDLESS_SECRET_KEY

class ApiConnection:

    @staticmethod
    def _parse_response(resp: requests.Response) -> Dict[str, Any]:
        resp.raise_for_status()
        return resp.json()

    @classmethod
    def generate_access_refresh_token(cls):
        url = BASE_API_URL + "token/new/"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        data = {
            "secret_id": config.GOCARDLESS_SECRET_ID,
            "secret_key": config.GOCARDLESS_SECRET_KEY,
            }
        r = requests.post(url=url, headers=headers, json=data, timeout=10)
        return cls._parse_response(r)
    
    @classmethod
    def generate_access_token(cls, refresh_token):
        url = BASE_API_URL + "token/refresh/"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        data = {"refresh": f"{refresh_token}"}
        r = requests.post(url=url, headers=headers, json=data, timeout=10)
        return cls._parse_response(r)
    
    @classmethod
    def retrieve_bank_list(cls, access_token, country_code):
        url = BASE_API_URL + f"institutions/?country={country_code}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        r = requests.get(url=url, headers=headers, timeout=10)
        return cls._parse_response(r)
    
    @classmethod
    def create_eua(cls, access_token, bank_id):
        url = BASE_API_URL + "agreements/enduser/"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        data = {"institution_id": f"{bank_id}"}
        r = requests.post(url=url, headers=headers, json=data, timeout=10)
        return cls._parse_response(r)
    
    @classmethod
    def build_account_link(cls, access_token, bank_id, redirect=None):
        url = BASE_API_URL + "requisitions/"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        redirect = redirect or os.getenv("POCKETBOOK_REDIRECT", "http://localhost:8000/linked")
        data = {
            "redirect": f"{redirect}",
            "institution_id": f"{bank_id}",
            }
        r = requests.post(url=url, headers=headers, json=data, timeout=10)
        return cls._parse_response(r)
    
    @classmethod
    def retrieve_accounts(cls, requisition_id, access_token):
        url = BASE_API_URL + f"requisitions/{requisition_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        r = requests.get(url=url, headers=headers, timeout=10)
        return cls._parse_response(r)
    
    @classmethod
    async def get_balance_and_transactions(cls, account_id, access_token):
        results = {"balances": None, "transactions": None}
        async with aiohttp.ClientSession() as session:
            for k in results.keys():
                url = BASE_API_URL + f"accounts/{account_id}/{k}/"
                headers = {
                    "accept": "application/json",
                    "Authorization": f"Bearer {access_token}",
                }
                async with session.get(url=url, headers=headers, ssl=False, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    r.raise_for_status()
                    data = await r.json()
                results[k] = data[k]
            return {"account_id": account_id, "response": results}
    
