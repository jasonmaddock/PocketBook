from adding_accounts import handle_balance_and_trans_response
from classification import Rule
from test.assets import trans_and_balances_two, rules
    
def test_handle_balance_and_trans_general():
    "Test we don't blow up with actual data"
    balances_and_transactions = {}
    normalised, classified = handle_balance_and_trans_response(trans_and_balances_two, rules)
    balances_and_transactions[normalised["account_id"]] = {
            "balance": normalised["balance"],
            "transactions": classified,
        }

def test_handle_balance_and_trans_known():
    response = {
        "account_id": "1",
        "response": {
            "balances": [
                {
                    'balanceAmount': {
                        'amount': '50',
                    }, 
                }
            ],
            'transactions': {
                'booked': [
                    {
                        'bookingDate': '2026-05-29',
                        'transactionAmount': {
                            'amount': '-200.00',
                            'currency': 'GBP'
                        },
                        'creditorName': 'Test Creditor',
                        'remittanceInformationUnstructured': 'Test Vendor',
                        'internalTransactionId': '15',
                    },
                ],
                'pending': [
                    {
                        'valueDate': '2026-05-30',
                        'transacitonAmount': {
                            'amount': '50000',
                            'currency': 'GBP'
                        },
                        'debtorName': 'TestDebtor',
                        'additionalInformation': 'Test Description',
                        'transactionId': '16',
                    },
                ]
            }
        }                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
    }  
    rules = [
        Rule(
            id=1,
            name='Test Rule',
            merchant_pattern='Test Creditor',
            description_pattern=None,
            category_id=3,
            category_name='Test_Merchant',
            subcategory_id=3,
            subcategory_name='Test_Merchant_sub',
            fuzzy_threshold=0.75,
            priority=100
        ),
        Rule(
            id=2,
            name='Test Rule2',
            merchant_pattern=None,
            description_pattern="Test Description",
            category_id=2,
            category_name='Test_Desc',
            subcategory_id=2,
            subcategory_name='Test_desc_sub',
            fuzzy_threshold=0.75,
            priority=100
        ),
    ]
    normalised, classified = handle_balance_and_trans_response(response, rules)
    assert normalised["account_id"] == "1"
    assert normalised["balance"] == 50.0
    t1, t2 = classified
    assert t1["amount"] == '-200.00'
    assert t1["category_id"] == 3
    assert t1["subcategory_id"] == 3
    assert t2["amount"] == '50000'
    assert t2["category_id"] == 2
    assert t2["subcategory_id"] == 2
