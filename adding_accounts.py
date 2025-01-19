import json
import requests

import secrets

BASE_API_URL = "https://bankaccountdata.gocardless.com/api/v2/"


def get_access_token():
    url = BASE_API_URL + "token/new/"
    headers = {
        "accept": "application/json",
        "ContentType": "application/json"
    }
    data = {
        "secret_id": secrets.GOCARDLESS_SECRET_ID,
        "secret_key": secrets.GOCARDLESS_SECRET_KEY,
        }
    r = requests.post(url=url, headers=headers, data=data)
    content = json.loads(r.content)
    return r

def get_refresh_token():
    url = BASE_API_URL + "token/refresh/"
    headers = {
        "accept": "application/json",
        "ContentType": "application/json"
    }
    data = {"refresh_token": ""}

def get_available_banks(country: str = "gb") -> list[dict[str, str]]:
    url = BASE_API_URL + f"institutions/?country={country}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {secrets.GOCARDLESS_SECRET_ID}"
    }
    r = requests.get(url=url,headers=headers)
    return r

get_access_token()

def main():
    