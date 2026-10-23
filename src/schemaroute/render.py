"""Static evidence renderers."""

from __future__ import annotations

import html
import json
from typing import Any


def render_audit_html(result: dict[str, Any]) -> str:
    rows = []
    for finding in result["findings"]:
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(finding['code'])}</code></td>"
            f"<td>{html.escape(finding['severity'])}</td>"
            f"<td>{html.escape(finding['profile'])}</td>"
            f"<td><code>{html.escape(finding['pointer'])}</code></td>"
            f"<td>{html.escape(finding['message'])}</td>"
            "</tr>"
        )
    body_rows = (
        "".join(rows) or '<tr><td colspan="5">No documented static conflicts found.</td></tr>'
    )
    metrics = "".join(
        f"<li><span>{html.escape(name.replace('_', ' '))}</span><strong>{value}</strong></li>"
        for name, value in result["metrics"].items()
    )
    data = json.dumps(result, sort_keys=True, separators=(",", ":"))
    data = data.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>SchemaRoute audit</title><style>
:root{{--ink:#16231d;--muted:#5f6e66;--paper:#f5f3ea;--card:#fffdf6;--line:#d9d6c8;--accent:#126b52;--warn:#9a5b00;--bad:#a83232}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1120px;margin:auto;padding:40px 22px}}h1{{font-size:clamp(2rem,6vw,4.4rem);line-height:.95;margin:.2em 0}}
.eyebrow{{color:var(--accent);font-weight:800;letter-spacing:.12em;text-transform:uppercase}}.lede{{max-width:760px;color:var(--muted)}}
.grid{{display:grid;grid-template-columns:1.2fr .8fr;gap:18px;margin:28px 0}}.card{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 12px 30px #16231d0b}}
.verdict{{font-size:1.65rem;font-weight:850}}ul{{list-style:none;margin:0;padding:0}}li{{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding:8px 0;gap:12px}}
.table{{overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:18px}}table{{border-collapse:collapse;width:100%;min-width:850px}}th,td{{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top}}th{{background:#e9eee8;position:sticky;top:0}}
code{{font:0.9em ui-monospace,monospace}}footer{{color:var(--muted);margin-top:20px}}@media(max-width:720px){{.grid{{grid-template-columns:1fr}}main{{padding:24px 14px}}}}
</style></head><body><main><p class="eyebrow">Dated provider contract receipt</p><h1>SchemaRoute</h1>
<p class="lede">Offline evidence for one schema across declared LLM structured-output routes. Passing is not live-provider proof.</p>
<section class="grid"><article class="card"><p>Route verdict</p><div class="verdict">{html.escape(result["verdict"])}</div><p><code>{html.escape(result["schema_sha256"])}</code></p></article>
<article class="card"><h2>Static metrics</h2><ul>{metrics}</ul></article></section>
<section class="table"><table><thead><tr><th>Code</th><th>Severity</th><th>Profile</th><th>Pointer</th><th>Evidence</th></tr></thead><tbody>{body_rows}</tbody></table></section>
<footer>{html.escape(result["interpretation"])}</footer><script type="application/json" id="receipt">{data}</script>
</main></body></html>"""


def render_benchmark_svg(result: dict[str, Any]) -> str:
    total = result["case_count"]
    tool = result["schemaroute_correct"]
    baseline = result["baseline_correct"]
    tool_width = 720 * (tool / total if total else 0)
    baseline_width = 720 * (baseline / total if total else 0)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="500" viewBox="0 0 1000 500" role="img" aria-labelledby="title desc">
<title id="title">SchemaRoute authored corpus comparison</title><desc id="desc">SchemaRoute scores {tool} of {total}; JSON parse baseline scores {baseline} of {total}.</desc>
<rect width="1000" height="500" fill="#f5f3ea"/><text x="70" y="86" font-family="system-ui" font-size="44" font-weight="800" fill="#16231d">Provider portability is not JSON syntax</text>
<text x="70" y="126" font-family="system-ui" font-size="20" fill="#5f6e66">Exact route verdicts on {total} original synthetic cases</text>
<text x="70" y="210" font-family="system-ui" font-size="24" font-weight="700" fill="#16231d">SchemaRoute</text><rect x="210" y="180" width="720" height="45" rx="10" fill="#d9d6c8"/><rect x="210" y="180" width="{tool_width:.2f}" height="45" rx="10" fill="#126b52"/><text x="940" y="212" text-anchor="end" font-family="ui-monospace" font-size="23" font-weight="700" fill="#16231d">{tool}/{total}</text>
<text x="70" y="300" font-family="system-ui" font-size="24" font-weight="700" fill="#16231d">Parse-only</text><rect x="210" y="270" width="720" height="45" rx="10" fill="#d9d6c8"/><rect x="210" y="270" width="{baseline_width:.2f}" height="45" rx="10" fill="#b76819"/><text x="940" y="302" text-anchor="end" font-family="ui-monospace" font-size="23" font-weight="700" fill="#16231d">{baseline}/{total}</text>
<line x1="70" y1="375" x2="930" y2="375" stroke="#d9d6c8"/><text x="70" y="420" font-family="system-ui" font-size="18" fill="#5f6e66">Profiles accessed 2026-10-22: OpenAI strict, Anthropic JSON outputs, Gemini JSON</text>
<text x="70" y="450" font-family="system-ui" font-size="18" fill="#5f6e66">Synthetic implementation-aligned evidence. No provider or model was called.</text></svg>"""
