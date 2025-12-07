PocketBook — minimal GoCardless-backed personal finance dashboard with rule-based transaction categorisation.

## Setup
- Install deps: `pip install -r requirements.txt`.
- Export GoCardless sandbox creds: `export GOCARDLESS_SECRET_ID=...` and `export GOCARDLESS_SECRET_KEY=...`. If you prefer, drop them in `.env` (gitignored) and they’ll be auto-loaded on import:
  ```
  GOCARDLESS_SECRET_ID=your_id
  GOCARDLESS_SECRET_KEY=your_key
  ```
- DB defaults to `pocket.db` in the repo; override with `POCKETBOOK_DB=/path/to/db.sqlite`.

## Run
- API + UI: `python3 app.py` then open http://localhost:5000.
- CLI (legacy): `python3 cli.py -l GB` etc.
- Sync via UI button or POST `/api/sync` with `{ "user_id": 1 }` to pull balances/transactions for stored requisitions.

## Rules
- POST `/api/rules` with `merchant_pattern` and/or `description_pattern`, `category`, optional `priority`/`fuzzy_threshold`.
- Rules are evaluated in priority order (lower = earlier). Substring match wins; otherwise fuzzy ratio must meet `fuzzy_threshold`.
- Uncategorized transactions remain tagged as `"Uncategorized"` for later review.

## Notes
- Secrets are no longer hard-coded; ensure env vars are set before running.
- Schema is auto-created on startup (tokens, accounts, transactions, rules). Accounts store provider account IDs once synced.
- Tests: `python3 -m pytest`.
