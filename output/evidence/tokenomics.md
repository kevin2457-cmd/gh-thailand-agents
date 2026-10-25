| Run type | Runs measured | Requests/run | Input tokens/run | Cached/run | Output tokens/run | Cache hit | Cost/run | Cost/run without cache |
|---|---|---|---|---|---|---|---|---|
| Order entry (intake agent) | 41 | 2 | 6,175 | 5,605 | 540 | 91% | $0.00038 | $0.00089 |
| Owner Q&A (orchestrator + specialists) | 6 | 4 | 3,636 | 0 | 456 | 0% | $0.00059 | $0.00059 |

Per user per month (8 orders + 4 questions per day, 26 days): **$0.141** (without prompt caching $0.246)

| Users | LLM cost / month | Without caching |
|---|---|---|
| 1 | $0.14 | $0.25 |
| 3 | $0.42 | $0.74 |
| 100 | $14.12 | $24.61 |
| 10,000 | $1,412.20 | $2,461.49 |
