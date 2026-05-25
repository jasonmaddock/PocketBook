from adding_accounts import _normalize_transaction


def test_add_transactions(test_tx_db):
    tc = test_tx_db
    test_file = open('test_trans.json', 'r')
    test_trans = eval(test_file.readlines()[0])
    normalised_trans = [_normalize_transaction(tx) for tx in test_trans]
    trans = []
    dupe = []
    for i in normalised_trans:
        if i['provider_id'] not in trans:
            trans.append(i['provider_id'])
        else:
            dupe.append(i['provider_id'])
    trans_count = len(trans)
    tc.add_transactions(account_id=1, user_id=1, transactions=normalised_trans)
    stored_trans = len(tc.all_records())
    assert stored_trans == trans_count