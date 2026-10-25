"""生成 report.html 和 slides.html（单文件，截图以 base64 内嵌，双击就能打开）。

数字全部来自 output/evidence/（tokenomics.json、safety_results.json、real_summary.json）和 docs/owner_inputs.json。
用法：python scripts/build_docs.py
"""
from __future__ import annotations

import base64
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.catalog import CATALOG  # noqa: E402
from backend.config import EVIDENCE_DIR, ROOT_DIR  # noqa: E402

SHOTS = ROOT_DIR / "output" / "screenshots"
DOCS = ROOT_DIR / "docs"


def img(name: str) -> str:
    return "data:image/jpeg;base64," + base64.b64encode((SHOTS / name).read_bytes()).decode()


def load(name: str) -> dict | list:
    return json.loads((EVIDENCE_DIR / name).read_text(encoding="utf-8"))


DIAGRAM = """<svg class="diagram" viewBox="0 0 900 430" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, PingFang SC, sans-serif">
  <defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="#ff8cc6"/></marker></defs>
  <rect width="900" height="430" fill="#0f0d13"/>
  <text x="20" y="30" fill="#a9a3b3" font-size="13">ORDER ENTRY (staff)</text>
  <g font-size="13" fill="#f4f1f6">
    <rect x="20" y="45" width="130" height="58" rx="10" fill="#1d1d27" stroke="#2c2c3a"/>
    <text x="85" y="70" text-anchor="middle">WeChat / Excel /</text><text x="85" y="88" text-anchor="middle">sales report text</text>
    <rect x="180" y="45" width="110" height="58" rx="10" fill="#1d1d27" stroke="#2c2c3a"/>
    <text x="235" y="70" text-anchor="middle">Redaction</text><text x="235" y="88" text-anchor="middle" fill="#a9a3b3" font-size="11">names→codes</text>
    <rect x="320" y="45" width="150" height="58" rx="10" fill="#2a1020" stroke="#ff4fa3" stroke-width="2"/>
    <text x="395" y="68" text-anchor="middle" font-weight="700">Intake agent</text><text x="395" y="88" text-anchor="middle" fill="#ff8cc6" font-size="11">tool: lookup_product</text>
    <rect x="500" y="45" width="130" height="58" rx="10" fill="#1d1d27" stroke="#2c2c3a"/>
    <text x="565" y="68" text-anchor="middle">Code validation</text><text x="565" y="88" text-anchor="middle" fill="#a9a3b3" font-size="11">SKU · math · stock · injection</text>
    <rect x="660" y="45" width="100" height="58" rx="10" fill="#1d1d27" stroke="#2c2c3a"/>
    <text x="710" y="70" text-anchor="middle">Pending</text><text x="710" y="88" text-anchor="middle">queue</text>
    <rect x="785" y="45" width="100" height="58" rx="10" fill="#14231c" stroke="#4fd1a5" stroke-width="2"/>
    <text x="835" y="68" text-anchor="middle" font-weight="700">Owner</text><text x="835" y="88" text-anchor="middle" fill="#4fd1a5" font-size="11">approves</text>
  </g>
  <g stroke="#ff8cc6" stroke-width="2" marker-end="url(#a)">
    <line x1="150" y1="74" x2="178" y2="74"/><line x1="290" y1="74" x2="318" y2="74"/><line x1="470" y1="74" x2="498" y2="74"/>
    <line x1="630" y1="74" x2="658" y2="74"/><line x1="760" y1="74" x2="783" y2="74"/>
    <line x1="835" y1="103" x2="835" y2="170"/>
  </g>
  <rect x="610" y="172" width="275" height="90" rx="12" fill="#1d1d27" stroke="#ff4fa3"/>
  <text x="747" y="198" text-anchor="middle" fill="#f4f1f6" font-size="14" font-weight="700">SQLite (only code writes)</text>
  <text x="747" y="220" text-anchor="middle" fill="#a9a3b3" font-size="12">products · purchases · sales · stock_moves</text>
  <text x="747" y="240" text-anchor="middle" fill="#a9a3b3" font-size="12">pending_records · audit_log · llm_usage</text>
  <text x="20" y="200" fill="#a9a3b3" font-size="13">OWNER Q&amp;A</text>
  <g font-size="13" fill="#f4f1f6">
    <rect x="20" y="215" width="120" height="58" rx="10" fill="#1d1d27" stroke="#2c2c3a"/>
    <text x="80" y="240" text-anchor="middle">Owner question</text><text x="80" y="258" text-anchor="middle" fill="#a9a3b3" font-size="11">any language</text>
    <rect x="170" y="215" width="150" height="58" rx="10" fill="#2a1020" stroke="#ff4fa3" stroke-width="2"/>
    <text x="245" y="240" text-anchor="middle" font-weight="700">Orchestrator</text><text x="245" y="258" text-anchor="middle" fill="#ff8cc6" font-size="11">agents as tools</text>
    <rect x="360" y="180" width="200" height="58" rx="10" fill="#2a1020" stroke="#ff4fa3" stroke-width="2"/>
    <text x="460" y="203" text-anchor="middle" font-weight="700">Inventory agent</text><text x="460" y="222" text-anchor="middle" fill="#ff8cc6" font-size="11">reorder · stock · sales</text>
    <rect x="360" y="255" width="200" height="58" rx="10" fill="#2a1020" stroke="#ff4fa3" stroke-width="2"/>
    <text x="460" y="278" text-anchor="middle" font-weight="700">CRM agent</text><text x="460" y="297" text-anchor="middle" fill="#ff8cc6" font-size="11">dormant · history · message</text>
  </g>
  <g stroke="#ff8cc6" stroke-width="2" marker-end="url(#a)">
    <line x1="140" y1="244" x2="168" y2="244"/><line x1="320" y1="236" x2="358" y2="212"/><line x1="320" y1="252" x2="358" y2="282"/>
  </g>
  <g stroke="#4fd1a5" stroke-width="2" stroke-dasharray="5 4" marker-end="url(#a)">
    <line x1="560" y1="209" x2="608" y2="209"/><line x1="560" y1="284" x2="608" y2="240"/>
  </g>
  <text x="584" y="330" fill="#4fd1a5" font-size="12" text-anchor="middle">read-only deterministic analytics (SQL + Python)</text>
  <text x="20" y="372" fill="#f4f1f6" font-size="13">All agents: gpt-6-luna via Portkey · read-only tools · usage limits · token usage logged per agent.</text>
  <text x="20" y="394" fill="#a9a3b3" font-size="12">The LLM reads text and explains; code checks, computes, and writes only after the owner approves.</text>
</svg>"""


def token_table(t: dict) -> str:
    rows = []
    for k, label in (("intake", "Order entry (intake agent)"), ("ask", "Owner Q&amp;A (orchestrator + specialists)")):
        x = t["measured"][k]
        rows.append(f"<tr><td>{label}</td><td class='n'>{x['runs']}</td><td class='n'>{x['requests_per_run']}</td>"
                    f"<td class='n'>{x['input_tokens_per_run']:,}</td><td class='n'>{x['cached_tokens_per_run']:,}</td>"
                    f"<td class='n'>{x['output_tokens_per_run']:,}</td><td class='n'>${x['cost_per_run_mean']:.5f}</td>"
                    f"<td class='n'>${x['cost_per_run_without_cache']:.5f}</td></tr>")
    return ("<table><tr><th>Per run (mean)</th><th class='n'>Runs</th><th class='n'>Requests</th><th class='n'>Input</th>"
            "<th class='n'>Cached input</th><th class='n'>Output</th><th class='n'>Cost</th><th class='n'>Cost w/o cache</th></tr>"
            + "".join(rows) + "</table>")


def profile_table(t: dict) -> str:
    rows = []
    for p in t["profiles"].values():
        s = p["scale_usd_per_month"]
        rows.append(f"<tr><td>{html.escape(p['label'])}</td><td class='n'>{p['intakes_per_month']}</td>"
                    f"<td class='n'>{p['questions_per_month']}</td><td class='n'>${p['per_user_per_month_usd']:.3f}</td>"
                    f"<td class='n'>${s['100']:,.2f}</td><td class='n'>${s['10000']:,.0f}</td>"
                    f"<td class='n'>${p['scale_without_cache_usd_per_month']['10000']:,.0f}</td></tr>")
    return ("<table><tr><th>Usage profile (per user = one staff/owner seat)</th><th class='n'>Orders/mo</th>"
            "<th class='n'>Questions/mo</th><th class='n'>Per user/mo</th><th class='n'>100 users</th>"
            "<th class='n'>10,000 users</th><th class='n'>10,000 w/o cache</th></tr>" + "".join(rows) + "</table>")


def safety_table(rows: list[dict]) -> str:
    out = []
    for i, r in enumerate(rows, 1):
        detail = ""
        if r.get("blocking"):
            detail = html.escape(r["blocking"][0][:150])
        elif r.get("detail"):
            detail = html.escape(r["detail"][:150])
        elif r.get("error"):
            detail = html.escape(r["error"][:150])
        elif r.get("answer"):
            detail = "Answer: " + html.escape(r["answer"][:150])
        if r.get("provider_filtered"):
            detail = "Azure content filter rejected it (HTTP 400) → blocked record. " + detail
        tag = "<span class='pill ok'>stopped</span>" if r["blocked"] else "<span class='pill bad'>NOT stopped</span>"
        out.append(f"<tr><td>{i}</td><td>{html.escape(r['test'])}</td><td>{html.escape(r['expected'])}</td>"
                   f"<td>{tag}<br><span class='muted'>{detail}</span></td></tr>")
    return ("<table><tr><th>#</th><th>Attack / malfunction</th><th>Expected defense</th><th>Result</th></tr>"
            + "".join(out) + "</table>")


def values() -> dict[str, str]:
    t = load("tokenomics.json")
    safety = load("safety_results.json")
    real = load("real_summary.json")
    owner = json.loads((DOCS / "owner_inputs.json").read_text(encoding="utf-8"))
    qa = load("qa_runs.json") if (EVIDENCE_DIR / "qa_runs.json").exists() else []
    smoke = load("step3_smoke_sample.json")["intake"]["usage"]["total"]
    mi, ma = t["measured"]["intake"], t["measured"]["ask"]
    prof = t["profiles"]
    fc = real["finding_counts"]
    errors = fc.get("line_math_mismatch", 0) + fc.get("total_mismatch", 0) + fc.get("below_floor_price", 0)
    b = owner["baseline"]
    quote = owner.get("user_quote", "").strip()
    user_quote = (f"<p class='quote'>“{html.escape(quote)}”<br><span class='muted'>— {html.escape(owner['user_quote_source'])}</span></p>"
                  if quote else "<p class='note'>Owner feedback after real use: <i>to be added after the real-use session.</i></p>")
    return {
        "REPO_URL": owner["repo_url"],
        "REAL_ORDERS": str(real["orders_parsed"]),
        "REAL_CLEAN": str(real["orders_clean"]), "REAL_WARN": str(real["orders_with_warnings"]),
        "REAL_BLOCKED": str(real["orders_blocked"]),
        "REAL_ERRORS": str(errors), "BELOW_FLOOR": str(fc.get("below_floor_price", 0)),
        "IMPORT_COST": f"{real['import_cost_usd']:.3f}",
        "INTAKE_COST": f"{mi['cost_per_run_mean']:.5f}", "INTAKE_COST_NC": f"{mi['cost_per_run_without_cache']:.5f}",
        "CACHE_SAVING": f"{1 - mi['cost_per_run_mean'] / mi['cost_per_run_without_cache']:.0%}",
        "INTAKE_CACHE_HIT": f"{mi['cache_hit_rate']:.0%}", "INTAKE_RUNS": str(mi["runs"]), "ASK_RUNS": str(ma["runs"]),
        "ASK_COST": f"{ma['cost_per_run_mean']:.5f}", "ASK_REQ": f"{ma['requests_per_run']:.1f}",
        "PROFILE_THIS": f"{prof['this_business']['per_user_per_month_usd']:.2f}",
        "PROFILE_HEAVY": f"{prof['heavy']['per_user_per_month_usd']:.2f}",
        "HEAVY_10K": f"{prof['heavy']['scale_usd_per_month']['10000']:,.0f}",
        "TRACE_IN": f"{smoke['input_tokens']:,}", "TRACE_CACHED": f"{smoke['cached_tokens']:,}",
        "TRACE_COST": f"{smoke['cost_usd']:.5f}",
        "SAFETY_STOPPED": str(sum(r["blocked"] for r in safety)), "SAFETY_TOTAL": str(len(safety)),
        "CATALOG_SIZE": str(len(CATALOG)),
        "B_MIN_PER_ORDER": b["min_per_order"], "B_HOURS_WEEK": b["hours_per_week"], "B_ORDERS_WEEK": b["orders_per_week"],
        "B_LOOKUP": b["lookup"], "B_STOCKOUTS": b["stockouts"], "B_LOST_CUSTOMERS": b["lost_customers"],
        "USER_QUOTE": user_quote, "QUOTE_TEXT": html.escape(quote) if quote else "",
        "B_STOCKOUTS_SHORT": owner.get("stockouts_short", "$30k"),
        "SLIDE_QUOTE": (f"<p class='quote' style='margin-top:24px'>“{html.escape(quote)}”<br><small>— the owner, after "
                        f"using it with the real database</small></p>") if quote else "",
        "DIAGRAM": DIAGRAM, "TOKEN_TABLE": token_table(t), "PROFILE_TABLE": profile_table(t),
        "SAFETY_TABLE": safety_table(safety), "QA_N": str(len(qa)),
        **{f"IMG_{n:02d}": img(f) for n, f in enumerate(sorted(p.name for p in SHOTS.glob("*.jpg")), 1)},
    }


def render(template: Path, out: Path, v: dict[str, str]) -> None:
    s = template.read_text(encoding="utf-8")
    for k, val in v.items():
        s = s.replace("{{" + k + "}}", val)
    missing = sorted({m for m in __import__("re").findall(r"\{\{([A-Z0-9_]+)\}\}", s)})
    if missing:
        raise SystemExit(f"{template.name}: 没有填的占位符 {missing}")
    out.write_text(s, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    v = values()
    render(DOCS / "report_template.html", ROOT_DIR / "report.html", v)
    if (DOCS / "slides_template.html").exists():
        render(DOCS / "slides_template.html", ROOT_DIR / "slides.html", v)
