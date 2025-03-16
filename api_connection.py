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
        data = {"refresh": f"{refresh_token}"}
        r = requests.post(url=url, headers=headers, data=data)
        content = json.loads(r.content)
        return content
    
    @classmethod
    def retrieve_bank_list(cls, access_token, country_code):
        url = BASE_API_URL + f"institutions/?country={country_code}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        r = requests.get(url=url, headers=headers)
        content = json.loads(r.content)
        return content
    
    @classmethod
    def create_eua(cls, access_token, bank_id):
        url = BASE_API_URL + "agreements/enduser/"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        # data = "{\"institution_id\": \"%s\"}", bank_id
        data = {"institution_id": f"{bank_id}",}
        r = requests.post(url=url, headers=headers, data=json.dumps(data))
        content = json.loads(r.content)
        return content
    
    @classmethod
    def build_account_link(cls, access_token, bank_id, redirect="http://www.yourwebpage.com"):
        url = BASE_API_URL + "requisitions/"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        data = {
            "redirect": f"{redirect}",
            "institution_id": f"{bank_id}",
            }
        r = requests.post(url=url, headers=headers, data=json.dumps(data))
        content = json.loads(r.content)
        return content
    
    @classmethod
    def retrieve_accounts(cls, requisition_id, access_token):
        url = BASE_API_URL + f"requisitions/{requisition_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        r = requests.get(url=url, headers=headers)
        content = json.loads(r.content)
        return content
    
    @classmethod
    def get_balance_and_transactions(cls, account_id, access_token):
        results = {"balances": None, "transactions": None}
        for k in results.keys():
            url = BASE_API_URL + f"accounts/{account_id}/{k}/"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            r = requests.get(url=url, headers=headers)
            results[k] = json.loads(r.content)[k]
        return results



    def retrieve_transactions(cls, access_token):
        pass
    
    