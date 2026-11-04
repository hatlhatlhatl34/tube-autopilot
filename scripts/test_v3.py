#!/usr/bin/env python3
"""v3 regression suite — every port from the forever-factory, proven
locally before any GitHub push.

Covers: bank-only writing (4 channels), hook pattern rotation, the
humanize scrub/audit, the history .bak ladder + defer stamps +
verified stamps, the per-channel gate matrix, the oEmbed verify pass,
the quota-defer classification, and the local Kokoro voice ladder
(real synthesis, real word timings).
"""
import json
import random
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import history, hooks, humanize, scriptwriter, verify  # noqa: E402
from src.config import load_channel  # noqa: E402

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {detail}")


# ── 1. bank-only writing, all 4 channels ────────────────────────────
print("\n[1] bank-only writing (no-AI doctrine)")
for cid in ("mindset", "facts", "tech", "money"):
    cfg = load_channel(cid)
    rng = random.Random(42)
    topic = {"topic": None, "source": "offline", "headlines": []}
    script = scriptwriter.write_script(cfg, topic, rng)
    check(f"{cid}: source == bank", script["source"] == "bank")
    check(f"{cid}: hook pattern labeled",
          isinstance(script.get("hook_pattern"), str) and script["hook_pattern"])
    check(f"{cid}: ai-tells audited",
          isinstance(script.get("tells"), dict) and "total" in script["tells"])
    check(f"{cid}: scenes present", len(script["scenes"]) >= 3)
    check(f"{cid}: no gemini key read anywhere",
          "gemini" not in json.dumps(script).lower())

# ── 2. hook pattern rotation ────────────────────────────────────────
print("\n[2] hook pattern rotation")
labels = [hooks.classify(h) for h in (
    "Why does one small promise change everything?",      # question
    "Stop waiting for motivation.",                        # negation
    "Three habits researchers measured for years.",       # list+stat
    "If you have ever felt stuck, this is for you.",      # empathy
)]
check("question classified", labels[0] == "question", str(labels))
check("negation classified", labels[1] == "negation", str(labels))
check("empathy classified", labels[3] == "empathy", str(labels))

cfg = load_channel("mindset")
rng = random.Random(7)
h, p = hooks.rotate_hook(cfg, "Most people quit right before it works.",
                         rng, avoid="bold_claim")
check("rotation avoids previous pattern", p != "bold_claim" or h != "Most people quit right before it works.")
h2, p2 = hooks.rotate_hook(cfg, "One rule separates winners.",
                           rng, avoid=None)
check("rotation no-op without avoid", p2 in hooks.PATTERNS)

# ── 3. humanize scrub/audit ─────────────────────────────────────────
print("\n[3] humanize (ai-tells) layer")
raw = "In today's world, we delve into the tapestry of discipline."
scr = humanize.scrub(raw)
check("scrub swaps hollow vocab", "delve" not in scr and "tapestry" not in scr)
check("scrub strips era opener", not scr.lower().startswith("in today"))
check("scrub idempotent", humanize.scrub(scr) == scr)
audit = humanize.audit("Moreover, it's not X, it's Y. Utilize this!")
check("audit counts filler", audit["filler"] >= 1)
check("audit counts contrast reveal", audit["contrast_reveal"] >= 1)
check("audit counts banned vocab", audit["banned_vocab"] >= 1)

# ── 4. history: .bak ladder + defer + verified + patterns ─────────
print("\n[4] history hardening")
import datetime
tmp = tempfile.mkdtemp()
history.HISTORY_DIR = Path(tmp)
cid = "mindset"
history.record(cid, "topic-a", "Title A", "vidA1", slot=1, hook_pattern="question")
history.record(cid, "topic-b", "Title B", "vidB1", slot=1, hook_pattern="negation")
check("last_hook_pattern readback",
      history.last_hook_pattern(cid) == "negation")

# .bak ladder: corrupt the main file, load must fall back
main_f = Path(tmp) / "mindset.json"
bak_f = Path(tmp) / "mindset.json.bak"
check(".bak exists after 2 saves", bak_f.exists())
main_f.write_text("{corrupted json")
entries = history.recent_entries(cid, days=10)
check(".bak ladder survives corruption", len(entries) == 2, str(len(entries)))

# defer stamp lifecycle
until = time.time() + 3600
history.set_defer(cid, "quotaExceeded", until)
reason, active_until = history.get_defer(cid)
check("defer stamp readback", reason == "quotaExceeded" and active_until == until)
history.clear_defer(cid)
reason2, _ = history.get_defer(cid)
check("defer cleared", reason2 is None)

# expired stamp ignored
history.set_defer(cid, "uploadLimitExceeded", time.time() - 10)
r3, u3 = history.get_defer(cid)
check("expired stamp ignored", r3 is None and u3 == 0.0)

# verified stamp
history.mark_verified(cid, "vidA1")
entries = history.recent_entries(cid, days=10)
check("verified stamp readback", entries[0].get("verified") is True)

# ── 5. gate matrix ─────────────────────────────────────────────────
print("\n[5] per-channel gate")
sys.path.insert(0, str(ROOT / "tools"))
import gate  # noqa: E402

gate.HISTORY = Path(tmp)
gate.ROOT = ROOT
today = datetime.date.today().isoformat()
# fresh channel: RUN
v = gate.verdict("facts")
check("fresh channel → RUN", v.startswith("RUN"), v)
# shipped today: SKIP
history.record("facts", "topic-f", "Title F", "vidF1", slot=1)
v = gate.verdict("facts")
check("shipped today → SKIP", v.startswith("SKIP"), v)
# defer active: SKIP with reason
history.set_defer("facts", "quotaExceeded", time.time() + 3600)
v = gate.verdict("facts")
check("defer active → SKIP", v.startswith("SKIP") and "quotaExceeded" in v, v)
history.clear_defer("facts")
# force: RUN
v = gate.verdict("facts", force=True)
check("force → RUN", v.startswith("RUN"), v)
# daily target raised: RUN again (the unlock in action)
mf = Path(tmp) / "facts.json"
data = json.loads(mf.read_text())
data[-1]["video_id"] = None       # yesterday shipped, today not yet
mf.write_text(json.dumps(data))
v = gate.verdict("facts")
check("target unmet → RUN", v.startswith("RUN"), v)

# ── 6. verify pass (fake probe — zero network) ─────────────────────
print("\n[6] post-publish verification")
hist_facts = Path(tmp) / "facts.json"
entries = json.loads(hist_facts.read_text())
entries.append({"date": (datetime.date.today() - datetime.timedelta(days=4)).isoformat(),
                "slot": 1, "topic": "old", "title": "Old Late One",
                "video_id": "vidLATE", "verified": False})
entries.append({"date": (datetime.date.today() - datetime.timedelta(days=1)).isoformat(),
                "slot": 1, "topic": "yest", "title": "Yesterday OK",
                "video_id": "vidOK", "verified": False})
hist_facts.write_text(json.dumps(entries))

res = verify.run_channel("facts", probe=lambda vid: True)
check("probe True → confirmed", res["confirmed"] >= 2 and res["late"] == 0, str(res))
entries = json.loads(hist_facts.read_text())
check("verified stamped in history",
      all(e.get("verified") for e in entries if e["video_id"] in ("vidOK", "vidLATE")))

# a fresh UNVERIFIED entry + a blind probe → unknown, no alerts
entries.append({"date": datetime.date.today().isoformat(), "slot": 3,
                "topic": "blind", "title": "Probe Blind One",
                "video_id": "vidBLIND", "verified": False})
hist_facts.write_text(json.dumps(entries))
res = verify.run_channel("facts", probe=lambda vid: None)
check("probe blind → unknown, no alerts", res["unknown"] >= 1 and not res["alerts"], str(res))

# late + not public → VERIFY-ALERT (fresh unverified late entry)
entries.append({"date": (datetime.date.today() - datetime.timedelta(days=4)).isoformat(),
                "slot": 2, "topic": "late", "title": "Genuinely Late",
                "video_id": "vidLATE2", "verified": False})
hist_facts.write_text(json.dumps(entries))
res = verify.run_channel("facts", probe=lambda vid: False)
check("late not-public → VERIFY-ALERT",
      res["late"] >= 1 and any("vidLATE2" in a for a in res["alerts"]), str(res))
# defer active → suppressed
history.set_defer("facts", "quotaExceeded", time.time() + 3600)
res = verify.run_channel("facts", probe=lambda vid: False)
check("defer active → alerts suppressed", not res["alerts"], str(res))
history.clear_defer("facts")

# ── 7. quota-defer classification ──────────────────────────────────
print("\n[7] quota defer classification")


class _FakeResp:
    status = 403


class _FakeError(Exception):
    resp = _FakeResp()
    content = json.dumps({"error": {"errors": [
        {"reason": "uploadLimitExceeded"}]}}).encode()

    def __str__(self):
        return "uploadLimitExceeded"


from src import youtube  # noqa: E402

reason = youtube._reason_of(_FakeError())
check("machine reason parsed from body", reason == "uploadLimitExceeded", reason)
nm = youtube._next_pacific_midnight()
check("pacific midnight in the future", nm > time.time() and nm < time.time() + 26 * 3600)
d = youtube.UploadDeferred("quotaExceeded", nm)
check("deferred message carries reason + window", "quotaExceeded" in str(d))

# ── 8. Kokoro voice ladder (REAL synthesis) ─────────────────────────
print("\n[8] Kokoro local voice (offline)")
from src import tts  # noqa: E402

check("kokoro files vendored", tts.kokoro_available())
cfg = load_channel("facts")
work = Path(tempfile.mkdtemp())
script = {"hook": "This sounds fake, but it is completely true.",
          "scenes": ["Your brain builds memories while you dream.",
                     "Octopuses have three hearts and blue blood."],
          "outro": "Follow for a new fact every single day."}
out_path, words, full = tts.synthesize(cfg, script, work)
check("voice file written", out_path.exists() and out_path.stat().st_size > 50_000)
check("word timings produced", len(words) >= 15, str(len(words)))
offs = [w["offset_ms"] for w in words]
check("offsets monotonic", all(a < b for a, b in zip(offs, offs[1:])))
import wave  # noqa: E402
with wave.open(str(out_path)) as w:
    dur = w.getnframes() / w.getframerate()
check(f"duration sane ({dur:.1f}s)", 3.0 < dur < 25.0)
last_end = (words[-1]["offset_ms"] + words[-1]["duration_ms"]) / 1000
check("timings span the audio", 0.5 < last_end <= dur + 0.4,
      f"last_end={last_end:.1f} dur={dur:.1f}")

# ── 9. GROWTH MODE: the publishAt grid (owner's Cairo contract) ────
print("\n[9] growth-mode publishAt grid")
from zoneinfo import ZoneInfo  # noqa: E402
_tz = ZoneInfo("Africa/Cairo")
gcfg = {"id": "mindset",
        "schedule": {"timezone": "Africa/Cairo",
                     "short_slots": ["00:00", "06:00", "12:00", "18:00"],
                     "long_slots": ["20:00"]}}
_now = datetime.datetime(2026, 11, 5, 1, 10, tzinfo=_tz)
nxt = youtube.next_publish_slot(gcfg, used=set(), now=_now)
check("grid books the soonest future slot",
      nxt == ("2026-11-05T06:00:00+02:00", "short"), str(nxt))
nxt = youtube.next_publish_slot(gcfg, used={"2026-11-05T06:00:00+02:00"}, now=_now)
check("grid skips a booked slot",
      nxt[0].startswith("2026-11-05T12:00:00"), str(nxt))
_now2 = datetime.datetime(2026, 11, 5, 5, 45, tzinfo=_tz)
nxt = youtube.next_publish_slot(gcfg, used=set(), now=_now2)
check("grid honors the 25-min margin (06:00 too close at 05:45)",
      nxt[0].startswith("2026-11-05T12:00:00"), str(nxt))
_now3 = datetime.datetime(2026, 11, 5, 21, 30, tzinfo=_tz)
nxt = youtube.next_publish_slot(gcfg, used=set(), now=_now3)
check("evening cycle books tomorrow's 00:00",
      nxt == ("2026-11-06T00:00:00+02:00", "short"), str(nxt))
used4 = {f"2026-11-06T{hh}:00:00+02:00" for hh in ("00", "06", "12", "18")}
nxt = youtube.next_publish_slot(gcfg, used=used4, now=_now3)
check("20:00 slot is the long-form kind",
      nxt == ("2026-11-06T20:00:00+02:00", "long"), str(nxt))
nxt = youtube.next_publish_slot({"id": "facts"}, used=set(), now=_now)
check("no schedule block -> no grid (classic mode)", nxt is None, str(nxt))

# history booking marks + readback
hist_mind = Path(tmp) / "mindset.json"
entries_m = json.loads(hist_mind.read_text())
entries_m.append({"date": datetime.date.today().isoformat(), "slot": 9,
                   "topic": "gridtest", "title": "Grid Test", "video_id": "vidGRID",
                   "verified": False, "publish_at": "2026-11-05T06:00:00+02:00"})
hist_mind.write_text(json.dumps(entries_m))
check("booked_slots readback from history",
      "2026-11-05T06:00:00+02:00" in history.booked_slots("mindset"),
      str(history.booked_slots("mindset")))

# gate: grid channel with a free horizon -> RUN
v = gate.verdict("mindset")
check("grid channel, free horizon -> RUN", v.startswith("RUN"), v)
# ... and fully booked -> SKIP
_nowg = datetime.datetime.now(_tz)
data_m = json.loads(hist_mind.read_text())
for d_off in (0, 1, 2):
    base = (_nowg + datetime.timedelta(days=d_off)).date()
    for hhmm in ("00:00", "06:00", "12:00", "18:00", "20:00"):
        hh, mm = map(int, hhmm.split(":"))
        s = datetime.datetime(base.year, base.month, base.day, hh, mm, tzinfo=_tz)
        data_m.append({"date": _nowg.date().isoformat(), "slot": 9, "topic": "grid",
                       "title": "booked", "video_id": "vidB", "verified": False,
                       "publish_at": s.isoformat()})
hist_mind.write_text(json.dumps(data_m))
v = gate.verdict("mindset")
check("grid fully booked -> SKIP", v.startswith("SKIP"), v)

# verify: a future-publishAt entry is PENDING — never probed, never late
hist_f = Path(tmp) / "facts.json"
entries_f = json.loads(hist_f.read_text())
entries_f.append({"date": datetime.date.today().isoformat(), "slot": 4,
                   "topic": "sched", "title": "Scheduled Tomorrow",
                   "video_id": "vidSCHED", "verified": False,
                   "publish_at": (_nowg + datetime.timedelta(hours=12)).isoformat()})
hist_f.write_text(json.dumps(entries_f))
res = verify.run_channel("facts", probe=lambda vid: None)
check("scheduled entry counted pending, not unknown/late",
      res["pending"] >= 1 and not res["alerts"], str(res))

print(f"\n{'=' * 48}\nRESULT: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
