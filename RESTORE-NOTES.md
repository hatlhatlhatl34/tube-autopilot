# RESTORE NOTES — tube-autopilot v3
*How this build was born: the 4-channel tube-autopilot merged with the
forever-factory backup (zip, 2026-11-02), with every locked setting
UNLOCKED by the owner's permission (2026-11-05) and re-aimed at the
4-channel ideas. Written so any future session (or the owner) knows
exactly what was taken, what was unlocked, and how to change anything.*

---

## Part 1 — What the zip contained (the whole 328 MB, examined)

| Path | Size | What it is / what we took |
|---|---|---|
| `ff-history.bundle` | 149 MB | COMPLETE git history (152 commits) of the forever-factory repo — incl. the vendored Kokoro voice models. **Taken: cloned; the voice models now vendored in `assets/voice_kokoro/`; the git history itself preserved at `upload/hub-zip/ff-repo/` for archaeology.** |
| `skills/` | ~183 MB | The 507-skill free library harvested from skills.sh (doctrine: free & readable only — no API keys, no paid services). **Taken: the doctrines that became code (hook patterns, ai-tells, verification-before-completion, thumbnail checklist). The library itself stays a reference catalog.** |
| `deliverables/` | 44 MB | rig_demo (articulated character rig), realism test variants A–D (parked decision), depth previews, the original blueprint PDF. **Taken: none into the render path (see Part 4).** |
| `forever-factory/` | 3.5 MB | The machine's readable copy: 24 src modules, 6 workflows, channel.yaml, RUNBOOK, BLUEPRINT, SKILLS.md. **Taken: the ports listed in Part 2.** |
| `sandbox-scripts/` | 928 KB | Every helper/test script from that chat. **Taken: patterns + lessons; the v3 test suite re-covers them for this architecture.** |
| `concept-catalog/` + `ancestors/` | ~3.9 MB | Episode concept bank + the machine's evolution (yt-machine ancestors). **Reference only.** |
| `worklog.md` | 64 KB | The other chat's full 25-task history. **Read fully; its incident ledger drives Part 3's locked-forever rules.** |

The other chat's production facts at backup time: **175 videos in 37
days**, 4 Shorts + 1 long/day on the Cairo grid, 44 episodes in the
no-repeat ledger, one niche pivot survived (bedtime → love psychology).

## Part 2 — What was PORTED into v3 (the merge)

| Port | From | Where it lives now |
|---|---|---|
| **Local Kokoro voice (offline, keyless)** | `src/tts.py` engine ladder + vendored `assets/voice_kokoro/` (115 MB, MIT) | `src/tts.py` — PRIMARY engine, per-channel personas: mindset `am_michael`, facts `af_bella`, tech `am_onyx`, money `bm_george`; edge-tts fallback (config-gated); per-video speed jitter; part-exact + proportional word timings for karaoke captions |
| **Post-publish verification** | `src/verify.py` (verification-before-completion skill) | `src/verify.py` — zero-quota oEmbed probe stamps `verified` on entries it SEES public; late-past-grace raises `VERIFY-ALERT` (workflow files an issue); fail-open; defer-aware |
| **Hook pattern rotation** | `src/hook_patterns.py` (hook-writer skill, 9 patterns) | `src/hooks.py` — classifies every hook, avoids repeating the previous video's pattern; pattern rides in history for future intelligence |
| **AI-tells humanization** | `src/ai_tells.py` (copywriting skill) | `src/humanize.py` — audit() counts machine-sounding patterns per script (log-only for hand-written banks); scrub()/hard() ready for any future imported text |
| **History .bak ladder** | `src/ledger.py` corruption resilience | `src/history.py` — `<channel>.json.bak` written with the FULL latest state before every save; corrupt main file falls back, nothing lost |
| **Defer-with-reasons** | `src/youtube.py` Oct-7 lesson | `src/youtube.py` — quota-family errors parse the MACHINE reason (quotaExceeded/dailyLimitExceeded → defer to Pacific midnight; uploadLimitExceeded → 2h; rateLimitExceeded → 90s retry); stamp `<channel>.defer.json`; `UploadDeferred` = healthy skip; a landing upload clears the stamp |
| **The per-channel gate** | `tools/gate.py` (15-second stdlib verdict) | `tools/gate.py` — SKIP if today's target shipped or a defer stamp is active; RUN otherwise; `--force` for humans |
| **Scheduling armor** | `daily-factory.yml` + `watchdog.yml` | every `daily-<channel>.yml` now: gate job + 4 staggered off-hour slots (prime + 2 backups + morning recovery) + gated dispatch input; NEW `watchdog.yml` heartbeats dispatch missing channels |
| **Pinned requirements** | the 5-year durability audit | `requirements.txt` — exact pins, no `>=` drift; google-genai REMOVED (the no-API rule) |
| **The lock catalog + unlock mapping** | `channel.yaml` locked settings | see Part 3 |

## Part 3 — The LOCKED settings: what they were, how they're UNLOCKED

The zip's `channel.yaml` + `RESTORE-GUIDE.md` Part 3 listed the
owner-locked surfaces of the psychology channel. The owner granted
unlock permission on 2026-11-05 with the instruction: *make them the
ideas and systems of the 4 channels.* Every lock and its new state:

| Lock (as shipped in the zip) | Now (v3) | Where to change it |
|---|---|---|
| Publish grid: Shorts 00/06/12/18 + long 20:00 Cairo, "do not move" | Per-channel staggered slots, quota-safe: **facts 15:05, mindset 15:30, tech 16:15, money 16:45 UTC** (Cairo evening), each with 2 backup slots + morning recovery | `.github/workflows/daily-<ch>.yml` cron lines |
| Daily grid: 1 long + 4 Shorts, fixed | `daily_uploads: 1` per channel (fits even ONE shared GCP project: 4×1,650 = 6,600 of 10,000 units) — raise to 5 per channel when it has its own GCP project | `channels/<ch>.yaml` `daily_uploads` |
| Short title: "Subscribe for more tips like this #psychology #relationship #love #relationshipgoals" (locked funnel) | Per-channel dynamic SEO titles from `title_patterns` + channel `hashtags` (already unique per video — the #epN duplicate-title fix is built in by construction) | `channels/<ch>.yaml` |
| Channel identity: "Psychology of Love", love-psychology niche, playlist, keywords | The 4 channels: **Zenith Mindset** (motivation, People & Blogs), **Fact Vault** (facts, Education), **AI Chronicle** (tech, Science & Tech), **Wealth Signals** (money, Education) — each with own palette, voice, hashtags, CTA | `channels/*.yaml` |
| Voice: Kokoro `af_heart` (warm female) | Per-channel Kokoro personas (am_michael / af_bella / am_onyx / bm_george) + edge-tts fallback personas (Guy/Aria/Christopher/Andrew) | `channels/<ch>.yaml` `voice` block |
| Visual identity: the LOCKED couple (2.5D depth build) | Per-channel Ken Burns gradients + palettes (proven on all 4 channels). The couple/depth engine stays available in the backup for a future "face" channel | `src/visuals.py` |
| Category: Entertainment (24) | Per-channel: 22 / 27 / 27 / 28 | `channels/<ch>.yaml` `category_id` |
| The muse LLM layer (OpenRouter) + Gemini writing | **REMOVED — bank-only writing** (owner rule: only YouTube credentials + GitHub token) | `src/scriptwriter.py` |
| Comments/monetization policy notes | General-audience content, `made_for_kids: false`, AI disclosure stays honest | `src/youtube.py` upload body |

**Locked FOREVER (universal laws, deliberately kept):** quota
discipline (never spend YouTube quota on diagnostics), fail-open
everywhere (a subsystem failing degrades, never silences the day),
the no-fabrication rule (no invented statistics), free-and-readable
only (no key-based services), and honest reporting (deferrals say
why; verify stamps say what's actually public).

## Part 4 — Deliberately NOT taken (and how to enable later)

1. **The articulated couple + depth engine** (`art_engine.py`,
   `anim.py`, `depth.py`, 1353+454+330 lines): the psychology
   channel's visual identity. Powerful but single-niche; the 4
   channels' Ken Burns pipeline is proven and per-channel-branded.
   Enable path: port `art_engine` + `depth` per channel palette when
   a channel wants "characters" — `deliverables/rig_demo/` proves the
   rig, `realism_test/` variants A–D are the parked upgrade decision.
2. **The story grammar engine** (4.97-quadrillion combos): our
   content banks + intelligence loop serve the same no-repeat goal
   with hand-written quality. Enable path: `story_engine.py` in the
   backup is self-contained.
3. **cron-job.org external pinger + noon-report platform cron**: the
   watchdog heartbeats + multi-slot armor cover starvation on the new
   account; add the external pinger only if a young repo still shows
   starved slots (RUNBOOK Part 6 of the backup has the 5-min recipe).
4. **The 507-skill library**: stays in the zip as the doctrine
   catalog (its best doctrines are already code — Part 2).

## Part 5 — The rebuild runbook (Option A: assistant does everything)

The owner chose **Option A** (SETUP.md): the assistant does ALL the
GitHub work via a temporary PAT — repo creation, code push (incl. the
115 MB voice models), secrets, smoke-test, first real run — token
deleted afterwards. Sequence once the owner sends credentials:

1. New GitHub token (scopes: repo + workflow) → assistant creates the
   new repo, pushes v3 (code + `assets/voice_kokoro/`).
2. New Gmails: for each channel, GCP project → enable YouTube Data
   API v3 → OAuth consent (External, test user) → Desktop client
   JSON → assistant generates the consent URL → owner Allow → code
   back → refresh token. One project PER channel if available (full
   quota); the hub fallback (one shared client, `daily_uploads: 1`)
   also works — see the quota note in Part 3.
3. Secrets: per channel `YT_CLIENT_ID_<CH>` /
   `YT_CLIENT_SECRET_<CH>` / `YT_REFRESH_TOKEN_<CH>` (or one
   `FACTORY_ENV` blob).
4. Smoke-test dispatch (offline render of all 4 channels on Actions)
   → then gated daily dispatch → first real videos.
5. Cosmetic, later: channel renames, GSC verify if a domain is
   added, `daily_uploads` raise when quotas are dedicated.

**The anti-ban lessons are baked in:** staggered slots (no 3-identical-apps-at-once pattern), one consent URL per channel owner account, bank-only writing (no Google AI surface involved), zero diagnostics quota, and the verify pass proving every public claim.
