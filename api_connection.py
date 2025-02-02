import json
import requests
import secrets

BASE_API_URL = "https://bankaccountdata.gocardless.com/api/v2/"
SECRET_ID = secrets.GOCARDLESS_SECRET_ID
SECRET_KEY = secrets.GOCARDLESS_SECRET_KEY

class ApiConnection:

    @classmethod
    def generate_access_refresh_token(cls):
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
        return content
    
    @classmethod
    def generate_access_token(cls, refresh_token):
        url = BASE_API_URL + "token/refresh/"
        headers = {
            "accept": "application/json",
            "ContentType": "application/json"
        }
        data = {"refresh_token": f"{refresh_token}"}
        r = requests.post(url=url, headers=headers, data=data)
        content = json.loads(r.content)
        return content
    
    @classmethod
    def retrieve_bank_list(cls, access_token, country_code="gb"):
        url = BASE_API_URL + f"institutions/?country={country_code}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        r = requests.get(url=url, headers=headers)
        content = json.loads(r.content)
        return content
    