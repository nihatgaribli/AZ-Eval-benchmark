"""Sürətli əl yoxlaması aləti — lokal brauzer interfeysi.

    python -m src.review data/raw/wikidata.jsonl

Niyə lazımdır: avtomatlaşdırma qaralama istehsal edir, amma brief-in mərkəzi
keyfiyyət qaydası hər nümunənin ƏL İLƏ yoxlanmasıdır. Yoxlamanın özü
avtomatlaşdırıla bilməz — avtomatlaşdırılsa, dataset sadəcə maşın məhsuluna
çevrilir və işin bütün elmi dəyəri itir.

Bu alət yoxlamanı əvəz etmir, SÜRƏTLƏNDİRİR. Sual, cavab, mənbə linki və
validator xəbərdarlıqları bir ekranda; təsdiq/rədd klaviaturadan. Nümunə başına
~5 dəqiqəlik iş ~15 saniyəyə enir. 300-500 nümunəlik yekun dataset yalnız bu
fərqlə real olur.

Niyə brauzer, terminal deyil: Windows konsolu Azərbaycan hərflərində problem
çıxarır, mətn redaktəsi isə terminalda əziyyətlidir. Server lokaldır, xarici
asılılıq yoxdur — yalnız Python standart kitabxanası.

Klaviatura:
    A  təsdiq (verified_by -> human)      R  rədd (-> rejected)
    S  atla                                ←/→  gəzinti
    Ctrl+Enter  redaktəni saxla
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import threading
import webbrowser
from collections.abc import Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from src.build_dataset import load_jsonl, validate_dataset
from src.morphology import aliases_for

__all__ = ["ReviewState", "main"]


class ReviewState:
    """Yoxlanılan faylın yaddaşdakı vəziyyəti; hər dəyişiklikdə diskə yazılır."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.records: list[dict[str, Any]] = [
            record for _, record in load_jsonl(path) if isinstance(record, dict)
        ]

    def warnings_by_index(self) -> dict[int, list[str]]:
        """Validator problemlərini sətir indeksinə görə qruplaşdırır."""
        report = validate_dataset(list(enumerate(self.records, start=1)))
        grouped: dict[int, list[str]] = {}
        for issue in report.issues:
            # `verified_by` xəbərdarlığı burada məlumat daşımır — yoxlama məhz
            # onu dəyişmək üçün açılıb.
            if issue.field == "verified_by":
                continue
            label = f"{issue.field or 'sətir'}: {issue.message}"
            grouped.setdefault(issue.line - 1, []).append(label)
        return grouped

    def snapshot(self) -> dict[str, Any]:
        warnings = self.warnings_by_index()
        return {
            "path": str(self.path),
            "items": [
                {"index": i, "record": r, "warnings": warnings.get(i, [])}
                for i, r in enumerate(self.records)
            ],
        }

    def update(self, index: int, record: dict[str, Any]) -> dict[str, Any]:
        """Bir sətri əvəz edib faylı atomik yazır."""
        with self._lock:
            if not 0 <= index < len(self.records):
                raise IndexError(index)
            self.records[index] = record
            self._write()
        return record

    def _write(self) -> None:
        """Müvəqqəti fayla yazıb yerinə qoyur — yarımçıq yazı faylı korlamasın."""
        directory = self.path.parent
        directory.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="\n", dir=directory, delete=False
        )
        try:
            with handle:
                for record in self.records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            os.replace(handle.name, self.path)
        except BaseException:
            Path(handle.name).unlink(missing_ok=True)
            raise


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


def _make_handler(state: ReviewState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:  # sükut
            pass

        def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload: Any, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send(body, "application/json", status)

        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                self._send(PAGE.encode("utf-8"), "text/html")
            elif self.path == "/api/state":
                self._send_json(state.snapshot())
            else:
                self._send_json({"error": "tapılmadı"}, 404)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._send_json({"error": "yararsız JSON"}, 400)
                return

            if self.path == "/api/item":
                try:
                    record = state.update(int(payload["index"]), payload["record"])
                except (KeyError, ValueError, IndexError) as exc:
                    self._send_json({"error": str(exc)}, 400)
                    return
                self._send_json(
                    {
                        "record": record,
                        "warnings": state.warnings_by_index().get(
                            int(payload["index"]), []
                        ),
                    }
                )
            elif self.path == "/api/aliases":
                self._send_json({"aliases": aliases_for(payload.get("answer", ""))})
            else:
                self._send_json({"error": "tapılmadı"}, 404)

    return Handler


PAGE = """<!doctype html>
<html lang="az">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AZ-Eval — yoxlama</title>
<style>
  :root {
    --bg:#faf9f7; --card:#fff; --ink:#1c1b19; --muted:#6b6862; --line:#e3e0da;
    --ok:#1f7a4d; --no:#a63232; --warn:#8a6100; --warn-bg:#fff8e6; --accent:#2f5fd0;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg:#16151a; --card:#1f1e24; --ink:#eceaf2; --muted:#9d99a8; --line:#332f3c;
      --ok:#5fd39b; --no:#f08a8a; --warn:#e8bd63; --warn-bg:#3a2f18; --accent:#8fb0ff;
    }
  }
  * { box-sizing:border-box }
  body {
    margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
  }
  header {
    position:sticky; top:0; background:var(--bg); border-bottom:1px solid var(--line);
    padding:14px 22px; display:flex; gap:18px; align-items:center; flex-wrap:wrap; z-index:5;
  }
  h1 { font-size:15px; margin:0; font-weight:650; letter-spacing:-.01em }
  .counts { display:flex; gap:14px; font-size:13px; color:var(--muted); margin-left:auto }
  .counts b { color:var(--ink); font-variant-numeric:tabular-nums }
  .bar { height:3px; background:var(--line); border-radius:2px; width:100%; overflow:hidden }
  .bar i { display:block; height:100%; background:var(--ok); transition:width .2s }
  main { max-width:820px; margin:26px auto 90px; padding:0 22px }
  .card {
    background:var(--card); border:1px solid var(--line); border-radius:12px;
    padding:22px; box-shadow:0 1px 3px rgba(0,0,0,.05);
  }
  .meta { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:18px }
  .tag {
    font-size:11px; padding:3px 9px; border-radius:20px; border:1px solid var(--line);
    color:var(--muted); text-transform:uppercase; letter-spacing:.05em; font-weight:600;
  }
  .tag.status-human { color:var(--ok); border-color:var(--ok) }
  .tag.status-rejected { color:var(--no); border-color:var(--no) }
  label { display:block; font-size:11px; color:var(--muted); text-transform:uppercase;
          letter-spacing:.06em; font-weight:650; margin:16px 0 5px }
  input, textarea {
    width:100%; background:transparent; color:var(--ink); border:1px solid var(--line);
    border-radius:7px; padding:9px 11px; font:inherit; resize:vertical;
  }
  input:focus, textarea:focus { outline:2px solid var(--accent); outline-offset:-1px; border-color:transparent }
  .en { color:var(--muted) }
  .row { display:grid; grid-template-columns:1fr 1fr; gap:14px }
  .hint-inline { font-size:12px; color:var(--muted); margin-top:6px; line-height:1.5 }
  .hint-inline code { font-family:ui-monospace,monospace; font-size:11px;
                      background:var(--bg); padding:1px 4px; border-radius:3px }
  .warn {
    background:var(--warn-bg); border:1px solid var(--warn); color:var(--warn);
    border-radius:8px; padding:10px 13px; margin-top:16px; font-size:13px;
  }
  .warn ul { margin:5px 0 0; padding-left:18px }
  a { color:var(--accent) }
  footer {
    position:fixed; bottom:0; left:0; right:0; background:var(--card);
    border-top:1px solid var(--line); padding:12px 22px; display:flex; gap:10px;
    align-items:center; flex-wrap:wrap;
  }
  button {
    font:inherit; font-weight:600; padding:8px 16px; border-radius:8px;
    border:1px solid var(--line); background:transparent; color:var(--ink); cursor:pointer;
  }
  button:hover { border-color:var(--accent) }
  button.ok { color:var(--ok); border-color:var(--ok) }
  button.no { color:var(--no); border-color:var(--no) }
  kbd {
    font:600 11px ui-monospace,monospace; border:1px solid var(--line);
    border-bottom-width:2px; border-radius:4px; padding:1px 5px; color:var(--muted);
  }
  .hint { margin-left:auto; font-size:12px; color:var(--muted) }
  .done { text-align:center; padding:60px 20px; color:var(--muted) }
</style>
</head>
<body>
<header>
  <h1>AZ-Eval — əl yoxlaması</h1>
  <div class="counts">
    <span>baxılıb <b id="c-done">0</b>/<b id="c-all">0</b></span>
    <span style="color:var(--ok)">təsdiq <b id="c-ok">0</b></span>
    <span style="color:var(--no)">rədd <b id="c-no">0</b></span>
  </div>
  <div class="bar"><i id="bar" style="width:0"></i></div>
</header>

<main id="main"><div class="done">Yüklənir…</div></main>

<footer>
  <button class="ok" onclick="decide('human')">Təsdiq <kbd>A</kbd></button>
  <button class="no" onclick="decide('rejected')">Rədd <kbd>R</kbd></button>
  <button onclick="go(1)">Atla <kbd>S</kbd></button>
  <button onclick="save()">Saxla <kbd>Ctrl</kbd>+<kbd>Enter</kbd></button>
  <span class="hint"><kbd>&larr;</kbd> <kbd>&rarr;</kbd> gəzinti</span>
</footer>

<script>
const FIELDS = ["question_az","question_en","answer","answer_en","notes"];
// `answer_aliases` siyahıdır, ayrıca emal olunur (vergüllə ayrılmış mətn).
let items = [], cur = 0;

async function api(path, body) {
  const opt = body ? {method:"POST", headers:{"Content-Type":"application/json"},
                      body:JSON.stringify(body)} : {};
  return (await fetch(path, opt)).json();
}

function counts() {
  const ok = items.filter(i => i.record.verified_by === "human").length;
  const no = items.filter(i => i.record.verified_by === "rejected").length;
  document.getElementById("c-ok").textContent = ok;
  document.getElementById("c-no").textContent = no;
  document.getElementById("c-done").textContent = ok + no;
  document.getElementById("c-all").textContent = items.length;
  document.getElementById("bar").style.width =
    items.length ? (100 * (ok + no) / items.length) + "%" : "0";
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, c =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
}

function render() {
  const main = document.getElementById("main");
  if (!items.length) { main.innerHTML = '<div class="done">Sətir yoxdur.</div>'; return; }
  const it = items[cur], r = it.record;
  const aliases = (r.answer_aliases || []).map(a => `<span class="chip">${esc(a)}</span>`).join("");
  const warn = it.warnings.length
    ? `<div class="warn"><b>Diqqət</b><ul>${it.warnings.map(w => `<li>${esc(w)}</li>`).join("")}</ul></div>`
    : "";
  main.innerHTML = `
    <div class="card">
      <div class="meta">
        <span class="tag">${esc(r.id)}</span>
        <span class="tag">${esc(r.category)}</span>
        <span class="tag">${esc(r.provenance)}</span>
        <span class="tag status-${esc(r.verified_by)}">${esc(r.verified_by)}</span>
        <span class="tag">${cur + 1} / ${items.length}</span>
        ${r.source ? `<a href="${esc(r.source)}" target="_blank" rel="noopener">mənbə &nearr;</a>` : ""}
      </div>
      <label>Sual (AZ)</label>
      <textarea id="f-question_az" rows="2">${esc(r.question_az)}</textarea>
      <label>Sual (EN)</label>
      <textarea id="f-question_en" class="en" rows="2">${esc(r.question_en)}</textarea>
      <div class="row">
        <div><label>Cavab (AZ)</label><input id="f-answer" value="${esc(r.answer)}"></div>
        <div><label>Cavab (EN)</label><input id="f-answer_en" class="en" value="${esc(r.answer_en)}"></div>
      </div>
      <label>Qəbul edilən formalar — vergüllə ayır</label>
      <input id="f-answer_aliases" value="${esc((r.answer_aliases || []).join(", "))}">
      <div class="hint-inline">
        Hallanmış formalar avtomatik yaranır. Modelin işlədə biləcəyi
        <b>alternativ yazılışları əl ilə əlavə et</b> — məsələn
        <code>Tokio</code> üçün <code>Tokyo</code>, <code>Paris</code> üçün
        <code>Pariz</code>. Bunlar Wikidata-da yoxdur və yalnız sən bilirsən.
      </div>
      <label>Qeyd</label>
      <input id="f-notes" value="${esc(r.notes || "")}">
      ${warn}
    </div>`;
  counts();
}

function collect() {
  const r = {...items[cur].record};
  for (const f of FIELDS) {
    const el = document.getElementById("f-" + f);
    if (el) r[f] = el.value.trim();
  }
  const aliasEl = document.getElementById("f-answer_aliases");
  if (aliasEl) {
    r.answer_aliases = [...new Set(
      aliasEl.value.split(",").map(a => a.trim()).filter(Boolean)
    )];
  }
  return r;
}

async function push(record) {
  const res = await api("/api/item", {index: items[cur].index, record});
  items[cur].record = res.record;
  items[cur].warnings = res.warnings;
}

// Cavab dəyişibsə avtomatik formaları yenidən qurur, amma əl ilə əlavə edilmiş
// alternativ yazılışları İTİRMİR — onları bilən yeganə tərəf istifadəçidir.
async function withRegeneratedAliases(record) {
  if (record.answer === items[cur].record.answer) return record;
  const fresh = (await api("/api/aliases", {answer: record.answer})).aliases;
  record.answer_aliases = [...new Set([...(record.answer_aliases || []), ...fresh])];
  return record;
}

async function save() {
  const record = collect();
  await push(await withRegeneratedAliases(record));
  render();
}

async function decide(status) {
  const record = await withRegeneratedAliases(collect());
  record.verified_by = status;
  await push(record);
  go(1);
}

function go(step) {
  cur = Math.min(items.length - 1, Math.max(0, cur + step));
  render();
  window.scrollTo(0, 0);
}

document.addEventListener("keydown", e => {
  const typing = /^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName);
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); save(); return; }
  if (typing) return;                       // yazarkən qısayollar işləməsin
  if (e.key === "a" || e.key === "A") decide("human");
  else if (e.key === "r" || e.key === "R") decide("rejected");
  else if (e.key === "s" || e.key === "S") go(1);
  else if (e.key === "ArrowRight") go(1);
  else if (e.key === "ArrowLeft") go(-1);
});

(async () => {
  const state = await api("/api/state");
  items = state.items;
  // Yoxlanmamış ilk sətirdən başla — yarımçıq qalan iş davam etsin.
  const next = items.findIndex(i => i.record.verified_by === "pending");
  cur = next === -1 ? 0 : next;
  render();
})();
</script>
</body>
</html>
"""


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="review", description="AZ-Eval qaralamalarının sürətli əl yoxlaması"
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"Fayl tapılmadı: {args.path}", file=sys.stderr)
        return 1

    state = ReviewState(args.path)
    if not state.records:
        print(f"Faylda sətir yoxdur: {args.path}", file=sys.stderr)
        return 1

    pending = sum(1 for r in state.records if r.get("verified_by") == "pending")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), _make_handler(state))
    url = f"http://127.0.0.1:{args.port}/"

    print(f"{len(state.records)} sətir, {pending}-i yoxlanmayıb")
    print(f"Aç: {url}   (dayandırmaq üçün Ctrl+C)")
    if not args.no_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDayandırıldı. Bütün dəyişikliklər fayla yazılıb.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
