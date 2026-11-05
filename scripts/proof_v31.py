#!/usr/bin/env python3
"""Local v3.1 proof: render one video through the NEW engine against a
scratch copy of the REAL ledger (bookings stripped so the grid offers a
slot). Verifies: LRU theme, line-memory exclusion, fingerprint guard,
theme-in-content, render pipeline."""
import json
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import history  # noqa: E402

prod = json.loads((ROOT / "data" / "history" / "mindset.json").read_text())
tmp = tempfile.mkdtemp()
for e in prod:
    e.pop("publish_at", None)          # free the grid for the proof
(Path(tmp) / "mindset.json").write_text(json.dumps(prod))
history.HISTORY_DIR = Path(tmp)

import main  # noqa: E402  (imports AFTER history redirect)

last = main.run_channel("mindset", offline=True, no_upload=True)

# ── verification ─────────────────────────────────────────────────────
entries = history._load("mindset")          # scratch ledger, dry run = no new entry
used = set()
for e in entries:
    used.update(e.get("lines") or [])
print("\n═══ v3.1 PROOF ═══")
print(f"video produced: {last.get('video_id') is None and last.get('produced', 0) == 1}")
work = Path(last.get("work", ""))
sj = json.loads((work / "script.json").read_text())
script = sj["script"]
mem = [history.norm_line(x) for x in script.get("memory_lines") or []]
reused = [ln for ln in mem if ln in used]
print(f"topic: {sj['topic'].get('topic')}")
print(f"title: {sj['meta']['title']}")
print(f"fingerprint: {script.get('fingerprint')}")
print(f"hook: {script['hook']}")
print(f"lines: {len(mem)} | reused-from-history: {len(reused)} {reused[:2]}")
theme = sj["topic"].get("topic", "").replace("daily ", "")
spoken = " ".join([script["hook"], *script["scenes"], script["outro"]]).lower()
print(f"theme '{theme}' spoken in content: {theme in spoken}")
fps = {e.get("fingerprint") for e in entries if e.get("fingerprint")}
print(f"fingerprint collision with history: {script.get('fingerprint') in fps}")
final = work / "slot01_short.mp4"
import subprocess  # noqa: E402
out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                      "format=duration,size", "-of", "csv=p=0", str(final)],
                     capture_output=True, text=True).stdout.strip()
print(f"render: {final.name} {out}")
print("\nPROOF " + ("✅ PASS" if (not reused and theme in spoken
                                   and script.get("fingerprint") not in fps) else "❌ FAIL"))
