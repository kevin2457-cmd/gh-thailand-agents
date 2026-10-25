# GH Thailand Inventory + CRM Agents

A multi-agent app for a real fertilizer distributor: the sole official General Hydroponics distributor in Thailand. Staff paste orders from WeChat or Excel, agents turn them into draft records, the owner approves them before anything is written, and deterministic code computes reorder alerts and flags dormant customers.

Pages: Q&A (orchestrator → inventory / CRM agents) · order entry (intake agent) · approval queue (owner only) · inventory & reorder · customers · token usage & audit log.

## Run it (Windows / macOS / Linux, Python 3.11+)

1. **Key.** Copy `.env.example` to `.env` and set `PORTKEY_API_KEY`. The app looks for `.env` in this repo folder first, then in the folder one level up, so you can also put it one level up.
2. **Install.**
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   pip install -r requirements.txt
   ```
3. **Build the database** from the bundled sample data:
   ```
   python scripts/init_db.py
   ```
4. **Run the app.**
   ```
   python app.py
   ```
   Open http://127.0.0.1:8050. Use the role switch (top right) to act as the owner (approves) or a staff member (enters orders).
   The order-entry page has three example orders: a normal one, one with an arithmetic error, and one with a prompt-injection attack.
5. **Check it (optional).**
   ```
   python -m pytest -q
   ```

## Data: sample vs. real

| Dataset | Folder | In git? | What it is |
|---|---|---|---|
| Sample (default) | `data/sample/` | Yes | Real GH product SKUs; synthetic customers, orders, prices and stock (one year, 40 customers) |
| Real | `data/real/` | **No** (gitignored) | The owner's anonymized business exports; stays on the owner's computer |

To switch datasets, rebuild the database:

```
python scripts/init_db.py --source sample   # default
python scripts/init_db.py --source real     # needs CSVs in data/real/ with the same columns as data/sample/
```

The real CSVs are built on the owner's computer from raw files in `data/real/raw/` (container Excel sheets, a Word stocktake):

```
python scripts/import_real_purchases.py   # container Excel -> products, purchases (checked against each sheet's totals)
python scripts/import_real_stocktake.py   # last stocktake -> opening stock; stock is counted from this date onward
```

Every product spelling and Chinese nickname maps to one standard SKU in `backend/catalog.py`. An unknown or ambiguous name stops the import instead of being guessed.

`python scripts/make_sample_data.py` regenerates the sample CSVs (fixed seed, same output each run).

## Privacy

- Customer names, phone numbers and addresses stay in the local database. Agents see only the customer code (for example `CUST-017`).
- Real data and `.env` are gitignored and never committed.

## Layout

```
backend/        config.py (paths, .env, model), db.py (connect, build DB), schema.sql
scripts/        init_db.py, make_sample_data.py
data/sample/    synthetic dataset (committed)
data/real/      real dataset (local only)
tests/          smoke tests
output/evidence screenshots, token logs, test results for the report
```

Model: `gpt-6-luna` via Portkey (course key).
