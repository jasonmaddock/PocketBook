import os
import json
import asyncio
import logging
import sys
import re

from flask import Flask, jsonify, request, render_template

from adding_accounts import activate_account, list_accounts, coordinate_sync, generate_bank_list, create_requisition, expired_account
from db import AccountsConnection, TransactionsConnection, RulesConnection, CategoryConnection, SubcategoryConnection
from classification import Rule, classify_transaction
import requests

from config import UNCATEGORISED_ID

CATEGORY_COLORS = [
    "rgb(239, 68, 68)", "rgb(249, 115, 22)", "rgb(245, 158, 11)", "rgb(234, 179, 8)",
    "rgb(34, 197, 94)", "rgb(20, 184, 166)", "rgb(6, 182, 212)", "rgb(59, 130, 246)",
    "rgb(99, 102, 241)", "rgb(139, 92, 246)", "rgb(236, 72, 153)", "rgb(249, 115, 171)",
]


app = Flask(__name__)

# Ensure INFO/DEBUG logs go to the terminal (Flask defaults to WARNING).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
app.logger.setLevel(logging.DEBUG)


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
    # How this should work:
    # 1. We don't want to duplicate a rule by merhcnat pattern or description pattern. for the relevant one to the rule, search the DB for the exisitng rule
    # for each one category agnostic. If all requested exist tell the user and return . Or else.
    # 2. Create the rules for those requested that do not already exist

    payload = request.json or {}
    rc = RulesConnection()
    category_id = payload.get("category_id")
    if not category_id:
        return jsonify({"error": "category_id required"}), 400
    subcategory_id = payload.get("subcategory_id")
    merchant_pattern = payload.get("merchant_pattern")
    description_pattern = payload.get("description_pattern")
    # Deduplicate: check for an existing rule with same patterns + category
    # rc.cursor.execute(
    #     """
    #     SELECT id FROM rules
    #     WHERE category_id = ? AND COALESCE(merchant_pattern,'') = COALESCE(?, '')
    #       AND COALESCE(description_pattern,'') = COALESCE(?, '')
    #     LIMIT 1
    #     """,
    #     (category_id, merchant_pattern, description_pattern),
    # )
    # existing = rc.cursor.fetchone()
    conflict = rc.conflict(merchant_pattern, description_pattern)
    if conflict:
        return jsonify({"id": conflict["id"], "deduped": True}), 200
    # detect conflicts on merchant/description patterns regardless of category
    # conflict_row = None
    # if merchant_pattern or description_pattern:
    #     rc.cursor.execute(
    #         """
    #         SELECT rules.*, categories.name AS category_name
    #         FROM rules
    #         LEFT JOIN categories ON categories.id = rules.category_id
    #         WHERE (? IS NOT NULL AND merchant_pattern = ?)
    #            OR (? IS NOT NULL AND description_pattern = ?)
    #         LIMIT 1
    #         """,
    #         (
    #             merchant_pattern,
    #             merchant_pattern,
    #             description_pattern,
    #             payload.get("description_pattern"),
    #         ),
    #     )
    #     conflict_row = rc.cursor.fetchone()
    if conflict and not payload.get("replace_existing"):
        return jsonify({"error": "conflict", "existing": row_to_dict(conflict)}), 409
    if conflict and payload.get("replace_existing"):
        rc.update_rule(
            rule_id=conflict["id"],
            name=payload.get("name") or merchant_pattern or "rule",
            merchant_pattern=merchant_pattern,
            description_pattern=description_pattern,
            category_id=int(category_id),
            subcategory_id=int(subcategory_id) if subcategory_id else None,
            fuzzy_threshold=float(payload.get("fuzzy_threshold", 0.75)),
            priority=int(payload.get("priority", 100)),
        )
        return jsonify({"id": conflict["id"], "replaced": True}), 200
    rule_id = rc.add_rule(
        name=payload.get("name") or merchant_pattern or "rule",
        merchant_pattern=merchant_pattern,
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
    rows = ac.retrieve_accounts(user_id)
    deduped = {}
    pending_counter = {}

    def score(row):
        has_bal = 1 if row["balance"] is not None else 0
        dt = row["balance_dt"] or ""
        return (has_bal, dt)

    for r in rows:
        pid = r["provider_account_id"]
        if pid:
            existing = deduped.get(pid)
            if not existing or score(r) > score(existing):
                deduped[pid] = r
        else:
            rid = r["req_id"] or "pending"
            pending_counter[rid] = pending_counter.get(rid, 0) + 1
            key = f"{rid}-{pending_counter[rid]}"
            deduped[key] = r

    return jsonify([row_to_dict(r) for r in deduped.values()])


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
    # Hide the Uncategorised category
    for cat in cats:
        if cat['id'] == 1:
            cats.remove(cat)
    # attach subcategories grouped
    subs_by_cat = {}
    for s in subs:
        subs_by_cat.setdefault(s["category_id"], []).append(s)
    for c in cats:
        c["subcategories"] = subs_by_cat.get(c["id"], [])
    return jsonify(cats)


@app.post("/api/categories")
def create_category():
    # How this should work.
    # Does a category with this name exist? if so return and warn user. Else
    # If the category doesn't have an assigned colour then assign the category a colour. 
    # create the category
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
    sc = SubcategoryConnection()
    tc = TransactionsConnection()
    rc = RulesConnection()
    subcategories = sc.list_subcategories(category_id)
    txs = tc.list_transactions(user_id=1, category_id=category_id)
    rules = rc.list_by_cat(category_id=category_id)
    for rule in rules:
        rc.delete_rule(rule['id'])
    for subcat in subcategories:
        sc.delete_subcategory(subcat['id'])
    for tx in txs:
        tc.update_category(tx_id=tx['id'], category_id=UNCATEGORISED_ID)
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
    colour = payload.get("color")
    if not (name and category_id):
        return jsonify({"error": "name and category_id required"}), 400
    if not colour:
        colour = subcategory_colour_gen(category_id)
    sc = SubcategoryConnection()
    sid = sc.add_subcategory(int(category_id), name, colour, float(payload.get("budget", 0) or 0))
    return jsonify({"id": sid}), 201

def subcategory_colour_gen(category_id):
    "We alternate between lightening and darkening subcategory colours. Hence the // and %."
    colour_diff = 0.15
    cc = CategoryConnection()
    sc = SubcategoryConnection()
    base_colour = cc.get_category_colour(category_id)
    count = len(sc.list_subcategories(category_id))
    prev = count // 2
    # we don't want to count from zero as then the first item would just be the base colour
    prev = prev + 1 
    lighten = count % 2
    rgb = re.findall(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", base_colour, flags=re.IGNORECASE)[0]
    new_rgb = []
    for c in rgb:
        sign = 1 if lighten else -1
        mod = int(c) * (prev * colour_diff) * sign 
        new_c = int(c) + int(mod)
        new_rgb.append(new_c)
    return f"rgb({new_rgb[0]},{new_rgb[1]},{new_rgb[2]})"


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
    rc = RulesConnection()
    rules = rc.list_by_cat(subcategory_id=subcategory_id)
    for rule in rules:
        if rule['category_id']:
            rc.delete_rule(rule_id=rule['id'])
    sc.delete_subcategory(subcategory_id)
    return jsonify({"id": subcategory_id})


@app.post("/api/reclassify")
def reclassify_transactions():
    user_id = int((request.json or {}).get("user_id", 1))
    rc = RulesConnection()
    tc = TransactionsConnection()
    cc = CategoryConnection()

    rules = [Rule.from_row(r) for r in rc.list_rules()]
    rows = tc.list_transactions(user_id)

    updated = 0
    for row in rows:
        tx = row_to_dict(row)
        if tx['id'] == 524:
            print("")
        raw = tx.get("raw_json")
        if isinstance(raw, str):
            try:
                tx["raw"] = json.loads(raw)
            except Exception:
                tx["raw"] = {}
        category_id, category_name, sub_cat_id, sub_cat_name, rule_id, _score = classify_transaction(tx, rules)
        if category_id and category_id != tx.get("category_id"):
            tc.update_category(tx["id"], category_id=category_id, rule_id=rule_id)
            updated += 1
        if sub_cat_id and sub_cat_id != tx.get("subcategory_id"):
            tc.update_category(tx["id"], category_id=category_id, subcategory_id=sub_cat_id, rule_id=rule_id)
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
        SELECT subcategories.id,
               subcategories.name,
               subcategories.budget,
               subcategories.category_id,
               subcategories.color,
               SUM(COALESCE(transactions.amount,0)) AS spend
        FROM subcategories
        LEFT JOIN transactions ON transactions.subcategory_id = subcategories.id AND transactions.user_id = ? {sub_join_filters}
        GROUP BY subcategories.id, subcategories.name, subcategories.budget, subcategories.category_id, subcategories.color
        """,
        tuple(sub_params),
    )
    subs = [dict(row) for row in cur.fetchall()]
    # count uncategorized transactions (all time to surface outstanding clean-up)
    # count uncategorized: either NULL/empty or explicitly set to the default "Uncategorised" category
    cur.execute(
        """
        SELECT COUNT(*) as cnt FROM transactions
        WHERE user_id = ? AND (category_id IS NULL OR category_id = '' OR category_id = ?)
        """,
        (user_id, UNCATEGORISED_ID),
    )
    unc_row = cur.fetchone()
    uncategorized_count = unc_row["cnt"] if unc_row else 0

    return jsonify({"total_balance": total_balance, "categories": cats, "subcategories": subs, "uncategorized_count": uncategorized_count})


@app.post("/api/sync")
def sync():
    user_id = int((request.json or {}).get("user_id", 1))
    account_id = (request.json or {}).get("provider_account_id", None)
    try:
        potential_accounts = list_accounts(user_id)
        if account_id:
            potential_accounts = [acc for acc in potential_accounts if acc['provider_account_id'] == account_id]
        accounts = []
        for account in potential_accounts:
            if account['status'] == "pending":
                activate_account(account)
            if expired_account(account):
                continue
            accounts.append(account)
        if accounts:
            result = asyncio.run(coordinate_sync(accounts, user_id=user_id))
            return jsonify(result)
        else:
            return jsonify({"error": "No valid accounts"}), 500
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
