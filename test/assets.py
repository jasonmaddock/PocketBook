from classification import Rule


token_gen_acc_tok = {'access': 'test-access-token', 'access_expires': 86400}
acc_ret_acc = {'id': '00000000-0000-4000-8000-000000000001', 'created': '2025-03-15T13:27:01.674118Z', 'redirect': 'http://www.yourwebpage.com', 'status': 'LN', 'institution_id': 'SANDBOX_BANK_GB', 'agreement': '00000000-0000-4000-8000-000000000002', 'reference': '00000000-0000-4000-8000-000000000001', 'accounts': ['00000000-0000-4000-8000-000000000003'], 'link': 'https://ob.gocardless.com/ob-psd2/start/00000000-0000-4000-8000-000000000004/SANDBOX_BANK_GB', 'ssn': None, 'account_selection': False, 'redirect_immediate': False}
trans_and_balances = {'balances': [{'balanceAmount': {'amount': '1799.41', 'currency': 'GBP'},
   'balanceType': 'interimAvailable',
   'referenceDate': '2025-04-06'},
  {'balanceAmount': {'amount': '1799.41', 'currency': 'GBP'},
   'balanceType': 'interimBooked',
   'referenceDate': '2025-04-06'}],
 'transactions': {'booked': [{'transactionId': 'transid',
    'bookingDate': '2025-04-07',
    'valueDate': '2025-04-06',
    'bookingDateTime': '2025-04-07T00:00:00Z',
    'valueDateTime': '2025-04-06T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'remittanceInformationUnstructured': 'Transfer from SAMPLE ACCOUNT 2025-04-06',
    'proprietaryBankTransactionCode': 'PaymentType: TW',
    'internalTransactionId': 'inttransid',
    'creditorAccount': 'InAnon'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-05',
    'valueDate': '2025-04-05',
    'bookingDateTime': '2025-04-05T00:00:00Z',
    'valueDateTime': '2025-04-05T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'SAMPLE PERSON A',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Payment to SAMPLE PERSON A',
    'proprietaryBankTransactionCode': 'PaymentType: WP',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-04',
    'valueDate': '2025-04-04',
    'bookingDateTime': '2025-04-04T00:00:00Z',
    'valueDateTime': '2025-04-04T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'debtorName': 'OutAnon',
    'debtorAccount': {},
    'remittanceInformationUnstructured': 'Bank credit SAMPLE EMPLOYER LTD',
    'proprietaryBankTransactionCode': 'PaymentType: LA',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-03',
    'valueDate': '2025-04-03',
    'bookingDateTime': '2025-04-03T00:00:00Z',
    'valueDateTime': '2025-04-03T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'PARKING CONTROL MANAGE',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Visa purchase PARKING CONTROL MANAGE',
    'proprietaryBankTransactionCode': 'PaymentType: VP',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-03',
    'valueDate': '2025-04-03',
    'bookingDateTime': '2025-04-03T00:00:00Z',
    'valueDateTime': '2025-04-03T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'LEEP NETWORKS',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Direct debit INTERNET PROVIDER',
    'proprietaryBankTransactionCode': 'PaymentType: D7',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-03',
    'valueDate': '2025-04-03',
    'bookingDateTime': '2025-04-03T00:00:00Z',
    'valueDateTime': '2025-04-03T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'HALIFAX',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Direct debit CREDIT PROVIDER',
    'proprietaryBankTransactionCode': 'PaymentType: D7',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-02',
    'valueDate': '2025-04-02',
    'bookingDateTime': '2025-04-02T00:00:00Z',
    'valueDateTime': '2025-04-02T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'Patreon* MembershipPatreo',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Visa purchase Patreon* MembershipPatreo 4472',
    'proprietaryBankTransactionCode': 'PaymentType: VP',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-02',
    'valueDate': '2025-04-02',
    'bookingDateTime': '2025-04-02T00:00:00Z',
    'valueDateTime': '2025-04-02T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'CAPITAL ONE',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Direct debit CARD PROVIDER',
    'proprietaryBankTransactionCode': 'PaymentType: D7',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-02',
    'valueDate': '2025-04-02',
    'bookingDateTime': '2025-04-02T00:00:00Z',
    'valueDateTime': '2025-04-02T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'SCOTTISHPOWER',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Direct debit ENERGY SUPPLIER',
    'proprietaryBankTransactionCode': 'PaymentType: D7',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-02',
    'valueDate': '2025-04-02',
    'bookingDateTime': '2025-04-02T00:00:00Z',
    'valueDateTime': '2025-04-02T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'SAMSUNGFINANCEGLOW',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Direct debit DEVICE FINANCE',
    'proprietaryBankTransactionCode': 'PaymentType: D7',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-01',
    'valueDate': '2025-04-01',
    'bookingDateTime': '2025-04-01T00:00:00Z',
    'valueDateTime': '2025-04-01T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'AJ BELL SECURITIES',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Direct debit INVESTMENT PLATFORM',
    'proprietaryBankTransactionCode': 'PaymentType: D7',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-01',
    'valueDate': '2025-04-01',
    'bookingDateTime': '2025-04-01T00:00:00Z',
    'valueDateTime': '2025-04-01T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'READING BOROUGH',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Direct debit LOCAL COUNCIL',
    'proprietaryBankTransactionCode': 'PaymentType: D7',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-04-01',
    'valueDate': '2025-04-01',
    'bookingDateTime': '2025-04-01T00:00:00Z',
    'valueDateTime': '2025-04-01T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'debtorName': 'OutAnon',
    'debtorAccount': {},
    'remittanceInformationUnstructured': 'Transfer from SAMPLE PERSON B',
    'proprietaryBankTransactionCode': 'PaymentType: TW',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-03-31',
    'valueDate': '2025-04-01',
    'bookingDateTime': '2025-03-31T00:00:00Z',
    'valueDateTime': '2025-04-01T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'remittanceInformationUnstructured': 'Interest added',
    'proprietaryBankTransactionCode': 'PaymentType: ZR',
    'internalTransactionId': 'inttransid',
    'creditorAccount': 'InAnon'},
   {'transactionId': 'transid',
    'bookingDate': '2025-03-31',
    'valueDate': '2025-03-31',
    'bookingDateTime': '2025-03-31T00:00:00Z',
    'valueDateTime': '2025-03-31T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'LIVINGWELL DD',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Direct debit GYM MEMBERSHIP',
    'proprietaryBankTransactionCode': 'PaymentType: D7',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-03-31',
    'valueDate': '2025-03-31',
    'bookingDateTime': '2025-03-31T00:00:00Z',
    'valueDateTime': '2025-03-31T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'SAMPLE PERSON C',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Standing order SAMPLE PERSON C',
    'proprietaryBankTransactionCode': 'PaymentType: WK',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'entryReference': 'HLAM Client Acc',
    'bookingDate': '2025-03-28',
    'valueDate': '2025-03-28',
    'bookingDateTime': '2025-03-28T00:00:00Z',
    'valueDateTime': '2025-03-28T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'debtorName': 'OutAnon',
    'debtorAccount': {},
    'remittanceInformationUnstructured': 'Bank credit INVESTMENT MANAGER',
    'additionalInformation': 'HLAM Client Acc',
    'proprietaryBankTransactionCode': 'PaymentType: LA',
    'internalTransactionId': 'inttransid'},
   {'transactionId': 'transid',
    'bookingDate': '2025-03-27',
    'valueDate': '2025-03-27',
    'bookingDateTime': '2025-03-27T00:00:00Z',
    'valueDateTime': '2025-03-27T00:00:00Z',
    'transactionAmount': {'amount': 100.51, 'currency': 'GBP'},
    'creditorName': 'SAMPLE PERSON A',
    'creditorAccount': 'InAnon',
    'remittanceInformationUnstructured': 'Payment to SAMPLE PERSON A',
    'proprietaryBankTransactionCode': 'PaymentType: WP',
    'internalTransactionId': 'inttransid'}]}}

tokens_table = """
CREATE TABLE tokens (
TokenID INTEGER PRIMARY KEY AUTOINCREMENT,
TokenType CHAR(8),
Token VARCHAR(1000),
ValidFor INT(255),
CreatedDt DATETIME
);
"""

requisitions_table = """
CREATE TABLE accounts(
ID INTEGER PRIMARY KEY AUTOINCREMENT,
UserId TEXT,
BankId TEXT,
EuaId TEXT,
ReqId TEXT,
ValidTil DATETIME
);
"""

accounts_table = """
CREATE TABLE accounts(
AccountID INTEGER PRIMARY KEY AUTOINCREMENT,
UserId TEXT,
BankId TEXT,
EuaId TEXT,
ReqId TEXT,
ValidTil DATETIME
Balance DECIMAL(16,2),
BalanceDt = DATETIME
);
"""

transactions_table = """
CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id TEXT UNIQUE,
    account_id INTEGER,
    user_id INTEGER,
    amount REAL,
    currency TEXT,
    date TEXT,
    merchant TEXT,
    description TEXT,
    category_id INTEGER,
    subcategory_id INTEGER,
    rule_id INTEGER,
    raw_json TEXT
);
"""

mock_balance = {
  "balances": [
    {
      "balanceAmount": {
        "amount": "657.49",
        "currency": "string"
      },
      "balanceType": "string",
      "referenceDate": "2021-11-22"
    },
    {
      "balanceAmount": {
        "amount": "185.67",
        "currency": "string"
      },
      "balanceType": "string",
      "referenceDate": "2021-11-19"
    }
  ]
}

mock_trans = {
  "transactions": {
    "booked": [
      {
        "transactionId": "string",
        "debtorName": "string",
        "debtorAccount": {
          "iban": "string"
        },
        "transactionAmount": {
          "currency": "string",
          "amount": "328.18"
        },
        "bankTransactionCode": "string",
        "bookingDate": "date",
        "valueDate": "date",
        "remittanceInformationUnstructured": "string"
      },
      {
        "transactionId": "string",
        "transactionAmount": {
          "currency": "string",
          "amount": "947.26"
        },
        "bankTransactionCode": "string",
        "bookingDate": "date",
        "valueDate": "date",
        "remittanceInformationUnstructured": "string"
      }
    ],
    "pending": [
      {
        "transactionAmount": {
          "currency": "string",
          "amount": "99.20"
        },
        "valueDate": "date",
        "remittanceInformationUnstructured": "string"
      }
    ]
  },
  "last_updated": "ISO 8601 timestamp"
}

mock_get_accounts_and_trans = {
    'account_id': 'account-id', 'response': 
      {'balances': 
       [
          {'balanceAmount': 
            {'amount': '657.49', 'currency': 'string'}, 'balanceType': 'string', 'referenceDate': '2021-11-22'},
          {'balanceAmount': 
            {'amount': '185.67', 'currency': 'string'}, 'balanceType': 'string', 'referenceDate': '2021-11-19'}
        ], 
        'transactions':
          {'booked': 
           [
            {'transactionId': 'string', 'debtorName': 'string', 'debtorAccount': {'iban': 'string'}, 'transactionAmount': {'currency': 'string', 'amount': '328.18'}, 'bankTransactionCode': 'string', 'bookingDate': 'date', 'valueDate': 'date', 'remittanceInformationUnstructured': 'string'},
            {'transactionId': 'string', 'transactionAmount': {'currency': 'string', 'amount': '947.26'}, 'bankTransactionCode': 'string', 'bookingDate': 'date', 'valueDate': 'date', 'remittanceInformationUnstructured': 'string'}
            ],
            'pending': [
          {'transactionAmount': {'currency': 'string', 'amount': '99.20'}, 'valueDate': 'date', 'remittanceInformationUnstructured': 'string'}
          ]
          }
          }
  }

trans_and_balances_two = {'account_id': '00000000-0000-4000-8000-000000000010', 'response': {'balances': [{'balanceAmount': {'amount': '201.79', 'currency': 'GBP'}, 'balanceType': 'expected', 'referenceDate': '2026-06-01'}, {'balanceAmount': {'amount': '201.79', 'currency': 'GBP'}, 'balanceType': 'closingCleared', 'referenceDate': '2026-06-01'}, {'balanceAmount': {'amount': '201.79', 'currency': 'GBP'}, 'balanceType': 'interimAvailable', 'referenceDate': '2026-06-01'}], 'transactions': {'booked': [{'transactionId': 'b0601e4c-ebdd-4741-96ac-65d09c328fd0', 'bookingDate': '2026-05-29', 'valueDate': '2026-05-30', 'bookingDateTime': '2026-05-29T09:04:11Z', 'valueDateTime': '2026-05-30T00:35:07.335Z', 'transactionAmount': {'amount': '-200.00', 'currency': 'GBP'}, 'creditorName': 'Cash Machine', 'remittanceInformationUnstructured': 'CASH WITHDRAWAL', 'proprietaryBankTransactionCode': 'MASTER_CARD', 'internalTransactionId': 'f755134e167b69e656db65456614bcfc'}, {'transactionId': 'b0399684-1f77-4041-b232-bf19452e1998', 'bookingDate': '2026-05-29', 'valueDate': '2026-05-29', 'bookingDateTime': '2026-05-29T08:25:12.207Z', 'valueDateTime': '2026-05-29T08:25:12Z', 'transactionAmount': {'amount': '200.00', 'currency': 'GBP'}, 'debtorName': 'Sample User', 'remittanceInformationUnstructured': 'INTERNAL TRANSFER', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '9fa0a86e26d24885d3f8d0d98e46d100'}, {'transactionId': 'b03bc9dd-41a1-4014-b035-fdc2c474cab1', 'bookingDate': '2026-05-29', 'valueDate': '2026-05-29', 'bookingDateTime': '2026-05-29T08:27:13.453Z', 'valueDateTime': '2026-05-29T08:27:13Z', 'transactionAmount': {'amount': '1500.00', 'currency': 'GBP'}, 'debtorName': 'Sample User', 'remittanceInformationUnstructured': 'INTERNAL TRANSFER', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '03b9da20355d52d6c101ba6fd3a4a791'}, {'transactionId': 'b03b31aa-379d-45a9-bcd1-8651ef50330f', 'bookingDate': '2026-05-29', 'valueDate': '2026-05-29', 'bookingDateTime': '2026-05-29T08:27:46.538Z', 'valueDateTime': '2026-05-29T08:27:47.732Z', 'transactionAmount': {'amount': '-1400.00', 'currency': 'GBP'}, 'creditorName': 'Sample Savings Account', 'creditorAccount': {'bban': '00000000000001'}, 'remittanceInformationUnstructured': 'transfer', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_OUT', 'internalTransactionId': '9c483f344ec1caee9c3af1c44df4c987'}, {'transactionId': '78e56e4c-9a83-44e8-9dfc-d0260a186dc0', 'bookingDate': '2026-05-19', 'valueDate': '2026-05-19', 'bookingDateTime': '2026-05-19T12:21:38.339Z', 'valueDateTime': '2026-05-19T12:21:38Z', 'transactionAmount': {'amount': '100.00', 'currency': 'GBP'}, 'debtorName': 'Sample User', 'remittanceInformationUnstructured': 'INTERNAL TRANSFER', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': 'ce9b95177678f7d9adb754bb237e8696'}, {'transactionId': '78e56d1c-9edd-44c8-8cc3-1069ad6d28a6', 'bookingDate': '2026-05-19', 'valueDate': '2026-05-19', 'bookingDateTime': '2026-05-19T12:21:58.047Z', 'valueDateTime': '2026-05-19T12:21:59Z', 'transactionAmount': {'amount': '-82.22', 'currency': 'GBP'}, 'creditorName': 'Sample Recipient', 'creditorAccount': {'bban': '00000000000002'}, 'remittanceInformationUnstructured': 'Payment to friend', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_OUT', 'internalTransactionId': '8b7564220a6466f1d47b1c77b31b330b'}, {'transactionId': 'cf6becdf-7afe-460c-98f4-870fa93aeae2', 'bookingDate': '2026-04-19', 'valueDate': '2026-04-20', 'bookingDateTime': '2026-04-19T09:15:13Z', 'valueDateTime': '2026-04-20T05:19:39.033Z', 'transactionAmount': {'amount': '-89.99', 'currency': 'GBP'}, 'creditorName': 'Pet Store', 'remittanceInformationUnstructured': 'Pet supplies', 'proprietaryBankTransactionCode': 'MASTER_CARD', 'internalTransactionId': 'b3fc0200cb81613b6e2063a44f864891'}, {'transactionId': 'd66bf3bc-d767-4dc5-a282-fc0f3231ea0c', 'bookingDate': '2026-04-20', 'valueDate': '2026-04-20', 'bookingDateTime': '2026-04-20T15:07:42.849Z', 'valueDateTime': '2026-04-20T15:07:42Z', 'transactionAmount': {'amount': '74.00', 'currency': 'GBP'}, 'debtorName': 'Sample Colleague', 'remittanceInformationUnstructured': 'Meal split', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '1e621b0b2dea3c197a326f99746404ea'}, {'transactionId': 'cf6a1595-f7f5-4b96-930e-4030ea5969b2', 'bookingDate': '2026-04-19', 'valueDate': '2026-04-19', 'bookingDateTime': '2026-04-19T09:14:39.35Z', 'valueDateTime': '2026-04-19T09:14:39Z', 'transactionAmount': {'amount': '100.00', 'currency': 'GBP'}, 'debtorName': 'Sample User', 'remittanceInformationUnstructured': 'INTERNAL TRANSFER', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '690473d98de954b0bf54c1307c6b5908'}, {'transactionId': '8b8385f0-97bc-43f3-9c78-cb7a9c08b809', 'bookingDate': '2026-04-07', 'valueDate': '2026-04-07', 'bookingDateTime': '2026-04-07T07:31:33.96Z', 'valueDateTime': '2026-04-07T07:31:35.506Z', 'transactionAmount': {'amount': '-9001.60', 'currency': 'GBP'}, 'creditorName': 'Sample Investment Account', 'creditorAccount': {'bban': '00000000000003'}, 'remittanceInformationUnstructured': 'transfer', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_OUT', 'internalTransactionId': 'ff3bae0b3623ab1e0c7e2a8b9e572324'}, {'transactionId': '8b84fe49-c025-41d2-bd12-34da0ba63be6', 'bookingDate': '2026-04-07', 'valueDate': '2026-04-07', 'bookingDateTime': '2026-04-07T07:32:40.76Z', 'valueDateTime': '2026-04-07T07:32:40Z', 'transactionAmount': {'amount': '4000.00', 'currency': 'GBP'}, 'debtorName': 'Sample User', 'remittanceInformationUnstructured': 'INTERNAL TRANSFER', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '6a3b281c71010db80e0a92f3b8fc16cc'}, {'transactionId': '8b854d81-b2c1-46e2-9c2e-83919f310763', 'bookingDate': '2026-04-07', 'valueDate': '2026-04-07', 'bookingDateTime': '2026-04-07T07:33:19.663Z', 'valueDateTime': '2026-04-07T07:33:20.834Z', 'transactionAmount': {'amount': '-2000.00', 'currency': 'GBP'}, 'creditorName': 'Sample Savings Account', 'creditorAccount': {'bban': '00000000000001'}, 'remittanceInformationUnstructured': 'Payment to savings', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_OUT', 'internalTransactionId': 'cd250f99cbd168eb31ee83c3ee4ddb8f'}, {'transactionId': '8b85a528-3c65-47e5-b2ab-b6d8cbb64a46', 'bookingDate': '2026-04-07', 'valueDate': '2026-04-07', 'bookingDateTime': '2026-04-07T07:33:39.383Z', 'valueDateTime': '2026-04-07T07:33:40.316Z', 'transactionAmount': {'amount': '-2000.00', 'currency': 'GBP'}, 'creditorName': 'Sample Current Account', 'creditorAccount': {'bban': '00000000000004'}, 'remittanceInformationUnstructured': 'From sample user', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_OUT', 'internalTransactionId': 'cbfcae5b0d62129f937056618368313a'}, {'transactionId': '83a52985-2c7c-4eca-8e18-c6f62062a58d', 'bookingDate': '2026-04-05', 'valueDate': '2026-04-06', 'bookingDateTime': '2026-04-05T21:57:56Z', 'valueDateTime': '2026-04-06T04:53:52.528Z', 'transactionAmount': {'amount': '-1000.00', 'currency': 'GBP'}, 'creditorName': 'Broker Transfer', 'remittanceInformationUnstructured': 'WWW.EXAMPLE-BROKER.CO.UK', 'proprietaryBankTransactionCode': 'MASTER_CARD', 'internalTransactionId': 'befa87cdfb8896bf4a899a8512b6ec32'}, {'transactionId': '83a52985-2c7c-4eca-8e18-c6f62062a58d', 'bookingDate': '2026-04-05', 'valueDate': '2026-04-06', 'bookingDateTime': '2026-04-05T21:57:56Z', 'valueDateTime': '2026-04-06T04:53:52.528Z', 'transactionAmount': {'amount': '-1000.00', 'currency': 'GBP'}, 'creditorName': 'Broker Transfer', 'remittanceInformationUnstructured': 'WWW.EXAMPLE-BROKER.CO.UK', 'proprietaryBankTransactionCode': 'MASTER_CARD', 'internalTransactionId': '55cb4dbc5a444ff66d1c9664f91dbb7c'}, {'transactionId': '84d62515-d412-4299-9585-f01e0e365cac', 'bookingDate': '2026-04-06', 'valueDate': '2026-04-06', 'bookingDateTime': '2026-04-06T03:02:04.648Z', 'valueDateTime': '2026-04-06T03:02:04Z', 'transactionAmount': {'amount': '1.00', 'currency': 'GBP'}, 'debtorName': 'Broker Platform Ltd', 'remittanceInformationUnstructured': 'REF-000001', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': 'ac672bdb25c50b8a69a3b7e52086451a'}, {'transactionId': '865d1ea9-58a6-4d87-bdc3-8ec7f67a459b', 'bookingDate': '2026-04-06', 'valueDate': '2026-04-06', 'bookingDateTime': '2026-04-06T09:33:39.524Z', 'valueDateTime': '2026-04-06T09:33:39Z', 'transactionAmount': {'amount': '9000.00', 'currency': 'GBP'}, 'debtorName': 'Broker Platform Ltd', 'remittanceInformationUnstructured': 'REF-000001', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '422d9abaa433e37dd8c36dfce21821f8'}, {'transactionId': '83a5676a-7882-4fb3-a498-59e8aa08ee3e', 'bookingDate': '2026-04-05', 'valueDate': '2026-04-05', 'bookingDateTime': '2026-04-05T21:57:04.933Z', 'valueDateTime': '2026-04-05T21:57:04Z', 'transactionAmount': {'amount': '1000.00', 'currency': 'GBP'}, 'debtorName': 'Sample User', 'remittanceInformationUnstructured': 'INTERNAL TRANSFER', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '3d2514a800d4c0bb0407066578ef7658'}, {'transactionId': '83abd7fd-3b39-4101-9c39-1b1403154471', 'bookingDate': '2026-04-05', 'valueDate': '2026-04-05', 'bookingDateTime': '2026-04-05T22:03:31.625Z', 'valueDateTime': '2026-04-05T22:03:31Z', 'transactionAmount': {'amount': '8525.66', 'currency': 'GBP'}, 'debtorName': 'Sample User', 'remittanceInformationUnstructured': 'INTERNAL TRANSFER', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '9b98f9e4a6300a4498f1b003b1313741'}, {'transactionId': '83af1d45-6be8-4cdb-95ff-760e56b6ebfb', 'bookingDate': '2026-04-05', 'valueDate': '2026-04-05', 'bookingDateTime': '2026-04-05T22:07:35.384Z', 'valueDateTime': '2026-04-05T22:07:35Z', 'transactionAmount': {'amount': '2155.21', 'currency': 'GBP'}, 'debtorName': 'Sample User', 'remittanceInformationUnstructured': 'MAIN ACCOUNT', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': 'ae2a5164d1d9c9e484dfe21b762a3afc'}, {'transactionId': '83b22549-9993-4a02-afe2-cf95bb1da1ea', 'bookingDate': '2026-04-05', 'valueDate': '2026-04-05', 'bookingDateTime': '2026-04-05T22:10:15.151Z', 'valueDateTime': '2026-04-05T22:10:17.017Z', 'transactionAmount': {'amount': '-11177.00', 'currency': 'GBP'}, 'creditorName': 'Broker Platform', 'creditorAccount': {'bban': '00000000000005'}, 'remittanceInformationUnstructured': 'BROKER-FUNDING-REF', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_OUT', 'internalTransactionId': '2009505a1bb31b3c2d58e0904e4e0097'}, {'transactionId': 'ef815b69-727a-4cdc-9283-80dc45654de4', 'bookingDate': '2026-03-10', 'valueDate': '2026-03-10', 'bookingDateTime': '2026-03-10T13:53:44.417Z', 'valueDateTime': '2026-03-10T13:53:44Z', 'transactionAmount': {'amount': '63.00', 'currency': 'GBP'}, 'debtorName': 'Sample Colleague', 'remittanceInformationUnstructured': 'Meal split', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_IN', 'internalTransactionId': '5e008a0cddebac97ecd518ec194bd224'}, {'transactionId': 'e33c3da7-b7de-43f7-a2d2-0991372dd7e5', 'bookingDate': '2026-03-08', 'valueDate': '2026-03-08', 'bookingDateTime': '2026-03-08T09:32:44.309Z', 'valueDateTime': '2026-03-08T09:32:45.489Z', 'transactionAmount': {'amount': '-35.00', 'currency': 'GBP'}, 'creditorName': 'Sample Contact', 'creditorAccount': {'bban': '00000000000006'}, 'remittanceInformationUnstructured': 'social event', 'proprietaryBankTransactionCode': 'FASTER_PAYMENTS_OUT', 'internalTransactionId': '82edf85f34dc14b53772f7fbf708b04d'}], 'pending': []}}}



rules = [
Rule(id=56, name='STEAMGAMES.COM 4259522', merchant_pattern='STEAMGAMES.COM 4259522', description_pattern=None, category_id=41, category_name='Entertainment', subcategory_id=36, subcategory_name='Games', fuzzy_threshold=0.75, priority=100),
Rule(id=59, name='AMAZON.CO.UK', merchant_pattern='AMAZON.CO.UK', description_pattern=None, category_id=39, category_name='Amazon', subcategory_id=None, subcategory_name=None, fuzzy_threshold=0.75, priority=100),
Rule(id=61, name='WAITROSE', merchant_pattern='WAITROSE', description_pattern='', category_id=38, category_name='Food', subcategory_id=37, subcategory_name='Groceries', fuzzy_threshold=0.75, priority=100),
Rule(id=42, name='Ocado', merchant_pattern='Ocado', description_pattern='Ocado', category_id=38, category_name='Food', subcategory_id=37, subcategory_name='Groceries', fuzzy_threshold=0.75, priority=100),
Rule(id=43, name='OSBORNE BROS', merchant_pattern='OSBORNE BROS', description_pattern=None, category_id=38, category_name='Food', subcategory_id=33, subcategory_name='Eating Out', fuzzy_threshold=0.75, priority=100),
]
