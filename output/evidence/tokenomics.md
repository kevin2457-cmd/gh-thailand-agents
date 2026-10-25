| Run type | Runs measured | Requests/run | Input tokens/run | Cached/run | Output tokens/run | Cache hit | Cost/run | Cost/run without cache |
|---|---|---|---|---|---|---|---|---|
| Order entry (intake agent) | 43 | 2 | 6,174 | 5,607 | 561 | 91% | $0.00039 | $0.00090 |
| Owner Q&A (orchestrator + specialists) | 9 | 4.22 | 3,518 | 0 | 479 | 0% | $0.00059 | $0.00059 |

| Usage profile | Orders / month | Questions / month | Cost / user / month | 100 users | 10,000 users | 10,000 users without caching |
|---|---|---|---|---|---|---|
| GH Thailand today (owner: 2-3 orders/week) | 12 | 78 | $0.051 | $5.08 | $508.19 | $568.74 |
| Busy distributor seat (8 orders + 4 questions per workday) | 208 | 104 | $0.143 | $14.32 | $1,432.39 | $2,481.98 |
