import os
import json

from flask import Flask, jsonify, request, render_template

from adding_accounts import list_accounts, get_balances_and_transactions, generate_bank_list, create_requisition
from db import AccountsConnection, TransactionsConnection, RulesConnection, CategoryConnection, SubcategoryConnection
from classification import Rule, classify_transaction
import requests

CATEGORY_COLORS = [
    "#ef4444", "#f97316", "#f59e0b", "#eab308",
    "#22c55e", "#14b8a6", "#06b6d4", "#3b82f6",
    "#6366f1", "#8b5cf6", "#ec4899", "#f973ab",
]


app = Flask(__name__)


def row_to_dict(row):
    return {k: row[k] for k in row.keys()}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/rules")
def rules_page():
    return render_template("rules.html")


@app.route("/categories")
def categories_page():
    return render_template("categories.html")


@app.route("/transactions")
def transactions_page():
    return render_template("transactions.html")


@app.route("/accounts")
def accounts_page():
    return render_template("accounts.html")


@app.get("/api/rules")
def get_rules():
    rc = RulesConnection()
    rules = [row_to_dict(r) for r in rc.list_rules()]
    return jsonify(rules)


@app.post("/api/rules")
def create_rule():
    payload = request.json or {}
    rc = RulesConnection()
    category_id = payload.get("category_id")
    if not category_id:
        return jsonify({"error": "category_id required"}), 400
    subcategory_id = payload.get("subcategory_id")
    # Deduplicate: check for an existing rule with same patterns + category
    rc.cursor.execute(
        """
        SELECT id FROM rules
        WHERE category_id = ? AND COALESCE(merchant_pattern,'') = COALESCE(?, '')
          AND COALESCE(description_pattern,'') = COALESCE(?, '')
        LIMIT 1
        """,
        (category_id, payload.get("merchant_pattern"), payload.get("description_pattern")),
    )
    existing = rc.cursor.fetchone()
    if existing:
        return jsonify({"id": existing["id"], "deduped": True}), 200
    # detect conflicts on merchant/description patterns regardless of category
    conflict_row = None
    if payload.get("merchant_pattern") or payload.get("description_pattern"):
        rc.cursor.execute(
            """
            SELECT rules.*, categories.name AS category_name
            FROM rules
            LEFT JOIN categories ON categories.id = rules.category_id
            WHERE (? IS NOT NULL AND merchant_pattern = ?)
               OR (? IS NOT NULL AND description_pattern = ?)
            LIMIT 1
            """,
            (
                payload.get("merchant_pattern"),
                payload.get("merchant_pattern"),
                payload.get("description_pattern"),
                payload.get("description_pattern"),
            ),
        )
        conflict_row = rc.cursor.fetchone()
    if conflict_row and not payload.get("replace_existing"):
        return jsonify({"error": "conflict", "existing": row_to_dict(conflict_row)}), 409
    if conflict_row and payload.get("replace_existing"):
        rc.update_rule(
            rule_id=conflict_row["id"],
            name=payload.get("name") or payload.get("merchant_pattern") or "rule",
            merchant_pattern=payload.get("merchant_pattern"),
            description_pattern=payload.get("description_pattern"),
            category_id=int(category_id),
            subcategory_id=int(subcategory_id) if subcategory_id else None,
            fuzzy_threshold=float(payload.get("fuzzy_threshold", 0.75)),
            priority=int(payload.get("priority", 100)),
        )
        return jsonify({"id": conflict_row["id"], "replaced": True}), 200
    rule_id = rc.add_rule(
        name=payload.get("name") or payload.get("merchant_pattern") or "rule",
        merchant_pattern=payload.get("merchant_pattern"),
        description_pattern=payload.get("description_pattern"),
        category_id=int(category_id),
        subcategory_id=int(subcategory_id) if subcategory_id else None,
        fuzzy_threshold=float(payload.get("fuzzy_threshold", 0.75)),
        priority=int(payload.get("priority", 100)),
    )
    return jsonify({"id": rule_id}), 201


@app.put("/api/rules/<int:rule_id>")
@app.patch("/api/rules/<int:rule_id>")
def update_rule(rule_id: int):
    payload = request.json or {}
    rc = RulesConnection()
    category_id = payload.get("category_id")
    if not category_id:
        return jsonify({"error": "category_id required"}), 400
    subcategory_id = payload.get("subcategory_id")
    rc.update_rule(
        rule_id=rule_id,
        name=payload.get("name") or payload.get("merchant_pattern") or "rule",
        merchant_pattern=payload.get("merchant_pattern"),
        description_pattern=payload.get("description_pattern"),
        category_id=int(category_id),
        subcategory_id=int(subcategory_id) if subcategory_id else None,
        fuzzy_threshold=float(payload.get("fuzzy_threshold", 0.75)),
        priority=int(payload.get("priority", 100)),
    )
    return jsonify({"id": rule_id})


@app.delete("/api/rules/<int:rule_id>")
def delete_rule(rule_id: int):
    rc = RulesConnection()
    rc.delete_rule(rule_id)
    return jsonify({"id": rule_id})


@app.get("/api/accounts")
def accounts():
    user_id = int(request.args.get("user_id", 1))
    ac = AccountsConnection()
    rows = ac.retrieve_accounts(user_id, include_pending=True)
    return jsonify([row_to_dict(r) for r in rows])


@app.delete("/api/accounts/<int:account_id>")
def delete_account(account_id: int):
    ac = AccountsConnection()
    ac.delete_account(account_id)
    return jsonify({"id": account_id})


@app.get("/api/transactions")
def transactions():
    user_id = int(request.args.get("user_id", 1))
    from_dt = request.args.get("from")
    to_dt = request.args.get("to")
    tc = TransactionsConnection()
    rows = tc.list_transactions(user_id, from_dt=from_dt, to_dt=to_dt)
    txs = [row_to_dict(r) for r in rows]
    total_balance = sum(float(tx.get("amount") or 0) for tx in txs)
    uncategorized = len([t for t in txs if not t.get("category_id")])
    return jsonify({"transactions": txs, "total_balance": total_balance, "uncategorized_count": uncategorized})


@app.patch("/api/transactions/<int:tx_id>")
def update_transaction_category(tx_id: int):
    payload = request.json or {}
    category_id = payload.get("category_id")
    subcategory_id = payload.get("subcategory_id")
    if not category_id:
        return jsonify({"error": "category_id required"}), 400
    rule_id = payload.get("rule_id")
    tc = TransactionsConnection()
    cat_id_val = int(category_id)
    subcat_val = int(subcategory_id) if subcategory_id not in (None, "", "null") else None
    tc.update_category(tx_id=tx_id, category_id=cat_id_val, subcategory_id=subcat_val, rule_id=rule_id)
    return jsonify({"id": tx_id, "category_id": cat_id_val, "subcategory_id": subcat_val, "rule_id": rule_id})


@app.get("/api/categories")
def categories():
    cc = CategoryConnection()
    sc = SubcategoryConnection()
    cats = [row_to_dict(r) for r in cc.list_categories()]
    subs = [row_to_dict(r) for r in sc.list_subcategories()]
    # attach subcategories grouped
    subs_by_cat = {}
    for s in subs:
        subs_by_cat.setdefault(s["category_id"], []).append(s)
    for c in cats:
        c["subcategories"] = subs_by_cat.get(c["id"], [])
    return jsonify(cats)


@app.post("/api/categories")
def create_category():
    payload = request.json or {}
    name = payload.get("name")
    if not name:
        return jsonify({"error": "name required"}), 400
    color = payload.get("color")
    budget = float(payload.get("budget", 0) or 0)
    cc = CategoryConnection()
    if not color:
        existing = {c["color"] for c in cc.list_categories() if c["color"]}
        for col in CATEGORY_COLORS:
            if col not in existing:
                color = col
                break
        if not color:
            color = CATEGORY_COLORS[0]
    cid = cc.add_category(name, color)
    cc.update_category(cid, name, color, budget)
    return jsonify({"id": cid}), 201


@app.put("/api/categories/<int:category_id>")
@app.patch("/api/categories/<int:category_id>")
def update_category(category_id: int):
    payload = request.json or {}
    name = payload.get("name")
    color = payload.get("color")
    budget = float(payload.get("budget", 0) or 0)
    if not name:
        return jsonify({"error": "name required"}), 400
    cc = CategoryConnection()
    cc.update_category(category_id, name, color, budget)
    return jsonify({"id": category_id})


@app.delete("/api/categories/<int:category_id>")
def delete_category(category_id: int):
    cc = CategoryConnection()
    cc.delete_category(category_id)
    return jsonify({"id": category_id})


@app.get("/api/subcategories")
def subcategories():
    category_id = request.args.get("category_id")
    sc = SubcategoryConnection()
    rows = sc.list_subcategories(int(category_id)) if category_id else sc.list_subcategories()
    return jsonify([row_to_dict(r) for r in rows])


@app.post("/api/subcategories")
def create_subcategory():
    payload = request.json or {}
    name = payload.get("name")
    category_id = payload.get("category_id")
    if not (name and category_id):
        return jsonify({"error": "name and category_id required"}), 400
    sc = SubcategoryConnection()
    sid = sc.add_subcategory(int(category_id), name, payload.get("color"), float(payload.get("budget", 0) or 0))
    return jsonify({"id": sid}), 201


@app.put("/api/subcategories/<int:subcategory_id>")
@app.patch("/api/subcategories/<int:subcategory_id>")
def update_subcategory(subcategory_id: int):
    payload = request.json or {}
    name = payload.get("name")
    if not name:
        return jsonify({"error": "name required"}), 400
    sc = SubcategoryConnection()
    sc.update_subcategory(subcategory_id, name, payload.get("color"), float(payload.get("budget", 0) or 0))
    return jsonify({"id": subcategory_id})


@app.delete("/api/subcategories/<int:subcategory_id>")
def delete_subcategory(subcategory_id: int):
    sc = SubcategoryConnection()
    sc.delete_subcategory(subcategory_id)
    return jsonify({"id": subcategory_id})


@app.post("/api/reclassify")
def reclassify_transactions():
    user_id = int((request.json or {}).get("user_id", 1))
    rc = RulesConnection()
    tc = TransactionsConnection()
    cc = CategoryConnection()

    rules = [Rule.from_row(r) for r in rc.list_rules()]
    default_category_id = cc.default_category_id
    rows = tc.list_transactions(user_id)

    updated = 0
    for row in rows:
        tx = row_to_dict(row)
        raw = tx.get("raw_json")
        if isinstance(raw, str):
            try:
                tx["raw"] = json.loads(raw)
            except Exception:
                tx["raw"] = {}
        category_id, category_name, sub_cat_id, sub_cat_name, rule_id, _score = classify_transaction(tx, rules, default_category_id)
        if category_id and category_id != tx.get("category_id"):
            tc.update_category(tx["id"], category_id=category_id, rule_id=rule_id)
            updated += 1
        if sub_cat_id and sub_cat_id != tx.get("subcategory_id"):
            tc.update_category(tx["id"], subcategory_id=category_id, rule_id=rule_id)
            updated += 1

    return jsonify({"updated": updated})

@app.get("/api/summary")
def summary():
    user_id = int(request.args.get("user_id", 1))
    from_dt = request.args.get("from")
    to_dt = request.args.get("to")
    ac = AccountsConnection()
    tc = TransactionsConnection()
    cc = CategoryConnection()
    sc = SubcategoryConnection()

    # Balances
    accounts = ac.retrieve_accounts(user_id)
    total_balance = sum(float(a["balance"] or 0) for a in accounts)

    # Spend per category
    cur = tc.cursor
    cat_params = [user_id]
    cat_conditions = []
    if from_dt:
        cat_conditions.append("transactions.date >= ?")
        cat_params.append(from_dt)
    if to_dt:
        cat_conditions.append("transactions.date <= ?")
        cat_params.append(to_dt)
    cat_join_filters = ""
    if cat_conditions:
        cat_join_filters = " AND " + " AND ".join(cat_conditions)
    cur.execute(
        f"""
        SELECT categories.id, categories.name, categories.budget, categories.color, SUM(COALESCE(transactions.amount,0)) AS spend
        FROM categories
        LEFT JOIN transactions ON transactions.category_id = categories.id AND transactions.user_id = ? {cat_join_filters}
        GROUP BY categories.id, categories.name, categories.budget, categories.color
        """,
        tuple(cat_params),
    )
    cats = [dict(row) for row in cur.fetchall()]
    # subcategories aggregated
    sub_params = [user_id]
    sub_conditions = []
    if from_dt:
        sub_conditions.append("transactions.date >= ?")
        sub_params.append(from_dt)
    if to_dt:
        sub_conditions.append("transactions.date <= ?")
        sub_params.append(to_dt)
    sub_join_filters = ""
    if sub_conditions:
        sub_join_filters = " AND " + " AND ".join(sub_conditions)
    cur.execute(
        f"""
        SELECT subcategories.id, subcategories.name, subcategories.budget, subcategories.category_id,
               SUM(COALESCE(transactions.amount,0)) AS spend
        FROM subcategories
        LEFT JOIN transactions ON transactions.subcategory_id = subcategories.id AND transactions.user_id = ? {sub_join_filters}
        GROUP BY subcategories.id, subcategories.name, subcategories.budget, subcategories.category_id
        """,
        tuple(sub_params),
    )
    subs = [dict(row) for row in cur.fetchall()]
    # count uncategorized transactions (all time to surface outstanding clean-up)
    # count uncategorized: either NULL/empty or explicitly set to the default "Uncategorized" category
    default_uncat_id = cc.default_category_id
    cur.execute(
        """
        SELECT COUNT(*) as cnt FROM transactions
        WHERE user_id = ? AND (category_id IS NULL OR category_id = '' OR category_id = ?)
        """,
        (user_id, default_uncat_id),
    )
    unc_row = cur.fetchone()
    uncategorized_count = unc_row["cnt"] if unc_row else 0

    return jsonify({"total_balance": total_balance, "categories": cats, "subcategories": subs, "uncategorized_count": uncategorized_count})


@app.post("/api/sync")
def sync():
    user_id = int((request.json or {}).get("user_id", 1))
    try:
        accounts = list_accounts(user_id, include_pending=True)
        result = get_balances_and_transactions(accounts, user_id=user_id)
        return jsonify(result)
    except requests.exceptions.HTTPError as http_err:
        status = getattr(http_err.response, "status_code", 500) or 500
        return jsonify({"error": str(http_err)}), status
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/linked")
def linked():
    return render_template("linked.html")


@app.get("/api/banks")
def banks():
    country = request.args.get("country", "GB")
    return jsonify(generate_bank_list(country))


@app.post("/api/requisitions")
def create_req():
    payload = request.json or {}
    bank_id = payload.get("bank_id")
    if not bank_id:
        return jsonify({"error": "bank_id required"}), 400
    user_id = int(payload.get("user_id", 1))
    req = create_requisition(bank_id, user_id=user_id)
    return jsonify(req)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True)
