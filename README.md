# GH Thailand Inventory + CRM Agents

A multi-agent app for a real fertilizer distributor: the sole official General Hydroponics distributor in Thailand (>US$1M/yr).
Staff paste orders straight from WeChat, Excel or the owner's sales notes. An intake agent turns each one into a draft, code checks it, and the owner approves it before anything is written. Deterministic code then computes reorder dates and flags dormant customers. The owner asks questions in any language, and an orchestrator agent routes them to the inventory and CRM agents.

- **Report:** [`report.html`](report.html) · **Slides:** [`slides.html`](slides.html) (open by double-clicking; arrow keys, F for fullscreen)
- **Model:** `gpt-6-luna` via Portkey (course key `PORTKEY_API_KEY`)

## Run it (Windows / macOS / Linux, Python 3.11+, about 3 minutes)

1. **Key.** Copy `.env.example` to `.env` and set `PORTKEY_API_KEY`. The app reads `.env` from this repo folder first, then from the folder one level up, so you can put it one level up instead.
2. **Install.**
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   pip install -r requirements.txt
   ```
3. **Run the app.** It builds the sample database on first start.
   ```
   python app.py
   ```
   Open http://127.0.0.1:8050. The interface is in English by default; for Chinese, click 中文 in the header or open http://127.0.0.1:8050/?lang=zh.
4. **Try it.**
   - **Sales:** orders and revenue for this year, month, week and today, in Thai Baht and US dollars, split by payment method.
   - **问答 (Q&A):** click an example question, for example 哪些产品需要马上补货？ The answer shows the tools used and the token cost.
   - **录单 (order entry):** switch the role (top right) to 员工 (staff) and click one of the three examples: a normal order, an order with an arithmetic error, or an order containing a prompt-injection attack. Then click 解析并提交审批.
   - **审批队列 (approvals):** switch to 老板 (owner) to approve or reject. Blocking issues disable the approve button, and staff can never approve.
   - **库存与补货 / 客户 / 用量与审计:** reorder plan, dormant customers with follow-up messages, measured token usage and the audit log.
5. **Tests (optional, no API key needed):** `python -m pytest -q`

If port 8050 is busy, use `PORT=8051 python app.py` on macOS/Linux, or `$env:PORT=8051; python app.py` in PowerShell.

## Data: sample vs. real

| Dataset | Where | In git? | What it is |
|---|---|---|---|
| Sample (default) | `data/sample/` → `data/app.db` | Yes (CSVs) | The real 43-SKU product catalog; synthetic customers, orders, prices and stock (one year, 40 customers) |
| Real | `data/real/` → `data/real.db` | **No** (gitignored) | The owner's container sheets, stocktake and orders; stays on the owner's computer |

Switching datasets:

```
python scripts/init_db.py                  # rebuild the sample database (data/app.db)
python app.py                              # run on sample data (default)

python scripts/init_db.py --source real    # build data/real.db from data/real/*.csv
python app.py --data real                  # run on real data
```

The owner builds the real CSVs from the raw files in `data/real/raw/`:

```
python scripts/import_real_purchases.py   # container Excel -> products, purchases (checked against each sheet's own totals)
python scripts/import_real_stocktake.py   # Word stocktake -> opening stock (stock is counted from the stocktake date)
python scripts/init_db.py --source real
python scripts/import_real_sales.py       # every historical order through the intake agent into the approval queue
```

Every product spelling and Chinese nickname maps to one standard SKU in `backend/catalog.py`. An unknown or ambiguous name stops instead of being guessed.

## Evidence scripts (numbers used in the report)

| Script | What it measures | Output |
|---|---|---|
| `scripts/safety_tests.py` | 9 attacks and malfunctions against a copy of the sample database | `output/evidence/safety_results.*` |
| `scripts/measure_qa.py` | token usage of typical owner questions | `output/evidence/qa_runs.json` |
| `scripts/tokenomics.py` | cost per run, per user per month, and at 100 and 10,000 users, from the `llm_usage` table | `output/evidence/tokenomics.*` |
| `scripts/build_docs.py` | rebuilds `report.html` and `slides.html` with embedded screenshots | `report.html`, `slides.html` |

## Privacy and safety

- Customer names, phone numbers and addresses stay in the local database. Agents see only codes like `CUST-017`, and names are swapped back in only on the owner's screen.
- Order text is redacted before it reaches the model (phones, addresses, links, bank accounts).
- No agent has a write tool. Only `orders.approve()` writes, and only for the owner role. Every step goes into `audit_log`.
- Payment screenshots attached to orders are saved in `data/payments/` (gitignored) and are never sent to the model. A cash order needs the owner's "Confirm cash received" before it can be approved.
- Real data, `data/*.db` and `.env` are gitignored.

## Layout

```
app.py                Dash UI (6 pages, staff/owner role switch)
backend/agents.py     intake, orchestrator, inventory and CRM agents (PydanticAI) + read-only tools
backend/orders.py     redaction, validation, pending queue, owner approval, audit log
backend/analytics.py  deterministic reorder, dormant customers, history, sales
backend/catalog.py    43 standard SKUs with spellings and Chinese nicknames
backend/llm.py        gpt-6-luna via Portkey; token usage per request and agent
prompts/              agent instructions
scripts/              data import, sample data, evidence and docs builders
tests/                25 tests (no API key needed)
output/               screenshots and evidence for the report
AI_prompts.md         every prompt I gave the coding assistant
```
