from classification import Rule, classify_transaction, apply_rules


def test_classify_transaction_matches_contains():
    rules = [
        Rule(
            id=1,
            name="coffee",
            merchant_pattern="coffee",
            description_pattern=None,
            category_id=2,
            category_name="Food",
            fuzzy_threshold=0.6,
            priority=10,
        )
    ]
    tx = {"merchant": "Starbucks Coffee", "description": "Flat white"}
    category_id, category_name, subcategory_id, subcategory_name, rule_id, score = classify_transaction(tx, rules)
    assert category_id == 2
    assert category_name == "Food"
    assert rule_id == 1
    assert score == 1.0


def test_apply_rules_marks_uncategorized():
    rules = []
    txs = [{"merchant": "Unknown shop", "description": "some thing"}]
    enriched = apply_rules(txs, rules)
    assert enriched[0]["category"] == "Uncategorised"
