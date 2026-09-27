"""Regenerate curation/series.json and curation/review.html from the NYPL API.

Downloads the list of series in NYPL's "Cigarette cards" collection and every
capture in it (about 100,000; a few minutes), then writes a review page with
three sample fronts per series.

Usage:
    python curation/build_review.py [--cache DIR]

--cache keeps the raw API downloads so a re-run only rebuilds the page.
Requires NYPL_TOKEN in the environment or a .env file.
"""
import argparse
import collections
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

API = "https://api.repo.nypl.org/api/v2"
PARENT = "b50ab6f0-c52b-012f-5986-58d385a7bc34"  # NYPL "Cigarette cards" collection
HERE = Path(__file__).resolve().parent
FRONT = "0000000001"


def get(session, url, params, tries=5):
    for attempt in range(tries):
        try:
            r = session.get(url, params=params, timeout=120)
            r.raise_for_status()
            return r.json()["nyplAPI"]
        except requests.RequestException as e:
            wait = 3 * (attempt + 1)
            print(f"  {e}; retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"gave up on {url} {params}")


def fetch_series(session):
    """All child series of the parent collection, with title, count and sequence order."""
    out, page = [], 1
    while True:
        res = get(session, f"{API}/collections/{PARENT}", {"per_page": 100, "page": page})["response"]
        coll = res.get("collection") or []
        if isinstance(coll, dict):
            coll = [coll]
        if not coll:
            break
        for c in coll:
            ti = c.get("mods", {}).get("titleInfo", {})
            if isinstance(ti, list):
                ti = ti[0]
            out.append({"uuid": c["uuid"], "title": ti.get("title", ""),
                        "numItems": int(c.get("numItems", 0)), "order": int(c.get("orderInSequence", 0))})
        print(f"series page {page}: {len(out)} so far", flush=True)
        if len(coll) < 100:
            break
        page += 1
        time.sleep(1)
    return out


def fetch_captures(session):
    """Every capture in the parent collection (fronts, backs and any extra sides)."""
    caps, page = [], 1
    while True:
        j = get(session, f"{API}/items/{PARENT}", {"per_page": 500, "page": page})
        items = j["response"].get("capture") or []
        if isinstance(items, dict):
            items = [items]
        caps.extend(items)
        total = int(j["request"].get("totalPages", 1))
        if page % 10 == 0 or page >= total:
            print(f"captures page {page}/{total}: {len(caps)}", flush=True)
        if page >= total or not items:
            return caps
        page += 1
        time.sleep(0.5)


def cached(path, fetch):
    if path and path.exists():
        print(f"using cached {path}")
        return json.loads(path.read_text())
    data = fetch()
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    return data


def build_rows(series, captures, current):
    by_series = collections.defaultdict(list)
    for c in captures:
        seg = (c.get("sortString") or "").split("|")
        if len(seg) == 4 and c.get("imageID"):
            by_series[int(seg[1])].append((seg, c))
    rows = []
    for s in series:
        entries = sorted(by_series.get(s["order"], []), key=lambda e: e[0])
        fronts = [c for seg, c in entries if seg[3] == FRONT]
        backs = [c for seg, c in entries if seg[3] == "0000000002"]
        rows.append({
            "uuid": s["uuid"], "order": s["order"], "title": s["title"], "numItems": s["numItems"],
            "fronts": len(fronts), "backs": len(backs), "other": len(entries) - len(fronts) - len(backs),
            "samples": [c["imageID"] for c in fronts[:3]], "current": s["uuid"] in current,
        })
    return rows


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Series review</title>
<style>
:root{--bg:#f5f0e6;--card:#fff9ef;--text:#2a2522;--muted:#5d534c;--border:#e5d9c8;--primary:#7c3c21;--sel:#2e7d32}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 -apple-system,system-ui,sans-serif;background:var(--bg);color:var(--text)}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--border);padding:10px 16px;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center}
header h1{font-size:16px;margin:0 12px 0 0;color:var(--primary)}
header input[type=search]{padding:6px 10px;border:1px solid var(--border);border-radius:6px;min-width:240px}
header select,header button{padding:6px 10px;border:1px solid var(--border);border-radius:6px;background:#fff;cursor:pointer;font:inherit}
.stats{color:var(--muted);margin-left:auto;white-space:nowrap}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;padding:12px 16px 80px}
.s{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;display:flex;flex-direction:column;gap:6px;cursor:pointer;transition:box-shadow .15s}
.s:hover{box-shadow:0 2px 10px rgba(0,0,0,.08)}
.s.on{border-color:var(--sel);box-shadow:0 0 0 2px rgba(46,125,50,.25)}
.s.cur .badge{display:inline}
.top{display:flex;gap:8px;align-items:flex-start}
.top input{margin:3px 0 0;transform:scale(1.2)}
.t{font-weight:600;flex:1}
.m{color:var(--muted);font-size:12px}
.badge{display:none;font-size:11px;background:#e8d9c2;color:var(--primary);border-radius:4px;padding:1px 6px;margin-left:6px}
.imgs{display:flex;gap:6px}
.imgs img{height:150px;max-width:33%;object-fit:contain;background:#f9f2e6;border:1px solid var(--border);border-radius:4px}
.none{color:#b00;font-size:12px}
#io{display:none;position:fixed;inset:auto 16px 16px 16px;background:#fff;border:1px solid var(--border);border-radius:8px;padding:12px;box-shadow:0 4px 20px rgba(0,0,0,.15);z-index:6}
#io textarea{width:100%;height:120px;font:12px monospace}
</style></head><body>
<header>
<h1>Series review</h1>
<input type="search" id="q" placeholder="Search titles…">
<select id="show"><option value="all">All</option><option value="on">Selected</option><option value="off">Unselected</option><option value="cur">Currently used</option></select>
<select id="sort"><option value="order">Order</option><option value="title">Title</option><option value="fronts">Card count</option></select>
<button id="selVis">Select visible</button><button id="clrVis">Clear visible</button>
<button id="export">Export…</button>
<span class="stats" id="stats"></span>
</header>
<main id="grid"></main>
<div id="io"><div style="display:flex;gap:8px;align-items:center;margin-bottom:6px"><b>Selected series</b> <button id="copy">Copy JSON</button> <button id="dl">Download selected_series.json</button> <button id="imp">Import from box</button> <button id="close" style="margin-left:auto">Close</button></div><textarea id="box"></textarea></div>
<script>
const DATA = __DATA__;
const KEY='series-review-selection';
let sel=new Set();
try{const s=localStorage.getItem(KEY); if(s) sel=new Set(JSON.parse(s)); else DATA.filter(d=>d.current).forEach(d=>sel.add(d.uuid));}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify([...sel]))}catch(e){}}
const grid=document.getElementById('grid'),q=document.getElementById('q'),show=document.getElementById('show'),sort=document.getElementById('sort'),stats=document.getElementById('stats');
function visible(){
  const t=q.value.trim().toLowerCase(), mode=show.value;
  let rows=DATA.filter(d=>(!t||d.title.toLowerCase().includes(t)) && (mode==='all'||(mode==='on'&&sel.has(d.uuid))||(mode==='off'&&!sel.has(d.uuid))||(mode==='cur'&&d.current)));
  const k=sort.value; rows=rows.slice().sort((a,b)=>k==='title'?a.title.localeCompare(b.title):k==='fronts'?b.fronts-a.fronts:a.order-b.order);
  return rows;
}
function updateStats(){const n=sel.size, cards=DATA.filter(d=>sel.has(d.uuid)).reduce((a,d)=>a+d.fronts,0); stats.textContent=`${visible().length} shown · ${n} selected · ${cards.toLocaleString()} cards`;}
function render(){
  grid.innerHTML=visible().map(d=>`<div class="s ${sel.has(d.uuid)?'on':''} ${d.current?'cur':''}" data-u="${d.uuid}">
    <div class="top"><input type="checkbox" ${sel.has(d.uuid)?'checked':''}><div><div class="t">${esc(d.title)}<span class="badge">in use</span></div>
    <div class="m">#${d.order} · ${d.fronts} fronts · ${d.backs} backs${d.other?` · ${d.other} other`:''}</div></div></div>
    <div class="imgs">${d.samples.length?d.samples.map(i=>`<img loading="lazy" src="https://images.nypl.org/index.php?id=${i}&t=r" alt="">`).join(''):'<span class="none">no front captures found</span>'}</div></div>`).join('');
  updateStats();
}
function esc(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
grid.addEventListener('click',e=>{const el=e.target.closest('.s'); if(!el) return; const u=el.dataset.u; if(sel.has(u)) sel.delete(u); else sel.add(u); save();
  el.classList.toggle('on'); el.querySelector('input').checked=sel.has(u); if(show.value!=='all') render(); else updateStats();});
[q,show,sort].forEach(el=>el.addEventListener('input',render));
document.getElementById('selVis').onclick=()=>{visible().forEach(d=>sel.add(d.uuid)); save(); render();};
document.getElementById('clrVis').onclick=()=>{visible().forEach(d=>sel.delete(d.uuid)); save(); render();};
const io=document.getElementById('io'),box=document.getElementById('box');
function payload(){return JSON.stringify(DATA.filter(d=>sel.has(d.uuid)).map(d=>({uuid:d.uuid,title:d.title,fronts:d.fronts})),null,1)}
document.getElementById('export').onclick=()=>{box.value=payload(); io.style.display='block';};
document.getElementById('close').onclick=()=>io.style.display='none';
document.getElementById('copy').onclick=()=>navigator.clipboard.writeText(box.value);
document.getElementById('dl').onclick=()=>{const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([box.value],{type:'application/json'})); a.download='selected_series.json'; a.click();};
document.getElementById('imp').onclick=()=>{try{const arr=JSON.parse(box.value); sel=new Set(arr.map(x=>typeof x==='string'?x:x.uuid)); save(); render();}catch(e){box.value='Could not parse JSON: '+e.message}};
render();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", type=Path, help="directory for raw API downloads (reused on re-runs)")
    ap.add_argument("--selection", type=Path, default=HERE / "selected_series.json",
                    help="series to mark as currently in use")
    args = ap.parse_args()

    load_dotenv()
    token = os.getenv("NYPL_TOKEN")
    if not token:
        sys.exit("NYPL_TOKEN is not set. Put it in .env or the environment.")
    session = requests.Session()
    session.headers["Authorization"] = f'Token token="{token}"'

    series = cached(args.cache / "series_raw.json" if args.cache else None, lambda: fetch_series(session))
    captures = cached(args.cache / "captures_raw.json" if args.cache else None, lambda: fetch_captures(session))

    current = set()
    if args.selection.exists():
        current = {s["uuid"] if isinstance(s, dict) else s for s in json.loads(args.selection.read_text())}

    rows = build_rows(series, captures, current)
    (HERE / "series.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    (HERE / "review.html").write_text(PAGE.replace("__DATA__", json.dumps(rows, separators=(",", ":"))))
    print(f"{len(rows)} series, {sum(r['fronts'] for r in rows)} cards; wrote series.json and review.html")


if __name__ == "__main__":
    main()
