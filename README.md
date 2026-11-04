# 📺 tube-autopilot v3

**A 100%-free, fully-automated YouTube Shorts empire.** Four themed channels, each an **independent workflow** on GitHub Actions — no hardware, no server, no cost, **no AI APIs** (scripts come from curated content banks; the voice is a local offline neural model vendored in this repo). You set it up once (~45 minutes), and every single day the system automatically:

1. 🔎 pulls **live trending topics** (Google News RSS — no API keys; fully offline mode also available)
2. ✍️ writes a fresh script from the **curated per-channel content banks** (v3 doctrine: **no Gemini, no LLM, no key-based AI anywhere**) — hook-pattern rotation + AI-tells audit built in
3. 🎙️ records a **neural voiceover with the local Kokoro engine** (offline, keyless, MIT — can never go dark) with edge-tts as fallback
4. 💬 burns **word-synced karaoke captions** (retention-optimized)
5. 🎨 renders a **1080×1920 Short** with Ken Burns motion + per-channel branding
6. 🎵 mixes a **synthesized, copyright-safe ambient track** (zero copyright strikes, ever)
7. 🖼️ generates a **branded thumbnail**
8. 🚀 uploads to YouTube with **SEO title / description / tags** built from the banks
9. 🗃️ logs the topic so it **never repeats itself** (history + .bak backup ladder)
10. 👁 **verifies every upload actually went public** (zero-quota oEmbed probe) and alerts if not
11. 📊 opens a **weekly analytics report** and **instant failure alerts** as GitHub issues
12. 🧠 **tunes itself every Monday** — learns which titles/topics earn views and
    biases future videos toward them (see [PLAN.md](PLAN.md))

> v3 = the original 4-channel machine merged with the forever-factory's
> operational hardening (gate, watchdog, defer-with-reasons, verify pass,
> pinned deps). See [RESTORE-NOTES.md](RESTORE-NOTES.md) for what was
> taken, what was unlocked, and how to change anything.

---

## The 4 channels (quota-safe default: 1 post/day each)

| Channel | Niche | Prime slot (UTC / Cairo evening) | Why it's here |
|---|---|---|---|
| **Fact Vault** | Mind-blowing facts | 15:05 / 17:05 | Highest viral ceiling, themed on daily trends |
| **Zenith Mindset** | Motivation quotes | 15:30 / 17:30 | Evergreen, viral sharing, fastest subscriber growth |
| **AI Chronicle** | AI/tech news | 16:15 / 18:15 | Today's headlines, highest CPM audience ($8–15) |
| **Wealth Signals** | Money rules | 16:45 / 18:45 | Highest RPM niche ($10–20) |

The default of **1 video/day/channel (4/day total)** fits even a single
SHARED GCP project (4 × 1,650 = 6,600 of the 10,000 daily quota units) —
the setting is UNLOCKED: raise `daily_uploads` per channel (up to 5 =
4 Shorts + 1 long-form) once that channel has its own GCP project.
Each channel: own workflow, own posting clock, own voice, own banks.
One channel failing never touches the others (and the watchdog heals
a missed slot same-day).
Full master plan: **[PLAN.md](PLAN.md)** (individual forever plan per channel).

## Cost: $0 / month, forever

| Component | Service | Cost |
|---|---|---|
| 4 daily runs (gate + render + upload) | GitHub Actions (public repo) | **free, unlimited minutes** |
| Script writing | content banks (in-repo) | free — no AI API by design |
| Voiceover | Kokoro-82M (local, vendored, MIT) | free, offline — edge-tts fallback also free |
| Trending topics | Google News RSS | free, no key (offline mode available) |
| Video render | ffmpeg (preinstalled on runners) | free |
| Music | synthesized by the pipeline itself | free + copyright-proof |
| Upload | YouTube Data API v3 (own OAuth per channel) | free quota — 1/day = 1,650 of 10,000 |

> You need internet only for the one-time setup and to review results. The daily
> runs happen entirely on GitHub's servers.

## ⚠️ Honest expectations (read once)

This machine maximizes your **odds** — it cannot print money on day one:

- **YouTube Partner Program** requires 1,000 subscribers **+** 4,000 public watch
  hours (or 10M Shorts views in 90 days). Typical timeline for successful faceless
  channels: **2–6 months** of daily posting. Most channels never get there; four
  diversified channels raise your chances but don't guarantee anything.
- **Shorts RPM is low** ($0.05–0.30 per 1k views). The real money comes later by
  converting Shorts audiences into long-form viewers (see roadmap below).
- **YouTube's monetization policies** reject "inauthentic, mass-produced" content.
  This pipeline is built to stay on the right side of that line: unique daily
  scripts, trend-driven topics, varied visuals, no reused footage — but review
  your first uploads and keep quality high. Quantity alone gets demonetized.
- **New channel + API uploads:** videos uploaded through an unverified API
  project can be locked to **private** by YouTube. Fix: submit the (free)
  YouTube API audit form — see step 6 below.

---

## One-time setup (~40 minutes)

> **Fast path: open [SETUP.md](SETUP.md) and follow it top to bottom.** It uses
> the double-click **setup wizard** (`START-HERE.bat` / `START-HERE.command`)
> and **ONE GitHub secret** (`FACTORY_ENV`). The steps below are the same
> thing in compact form, plus an advanced legacy path at the end.

### Step 0 — Accounts you need
- A **GitHub account** (free)
- **4 Google accounts**, each with its own YouTube channel created (YouTube →
  profile icon → "Create a channel" — exact names/handles in SETUP.md). One
  channel per account, one account per channel — this is what makes 4
  independent brands.

### Step 1 — Gemini API key (free, 2 min, optional)
1. Open **https://aistudio.google.com/apikey** (log in with any Google account)
2. **Create API key** → copy it — the setup wizard can store it for you, so
   no extra GitHub secret is needed.

### Step 2 — Google Cloud OAuth projects (free, ~20 min — one project PER channel)
> **One project per channel = one private 10,000-unit quota per channel.**
> That's what allows 3 uploads/day/channel. Repeat these 5 sub-steps 4×
> (mindset, facts, tech, money):
1. Open **https://console.cloud.google.com** → create a project, e.g. `tube-mindset`
2. **APIs & Services → Library** → search **"YouTube Data API v3"** → **Enable**
3. **APIs & Services → OAuth consent screen**:
   - User type: **External** → Create
   - App name: `tube-autopilot`, your email as support/contact
   - **Test users**: add the email of THAT channel's Google account
   - Back on the summary page → **PUBLISH APP → confirm**
   ⚠️ **Do publish** — in Testing mode Google expires your refresh token after
   7 days and the factory would need re-auth every week. Published = permanent.
   (Billing is never needed for this API.)
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Desktop app** → Create
5. Download the JSON as `client_secret_<channel>.json`

<details><summary>Shortcut: one shared project instead (1 project, shared quota)</summary>
Do the steps once with one project and one client, use the same
`client_secret.json` for all 4 channels, and only add the global secrets
`YT_CLIENT_ID` + `YT_CLIENT_SECRET`. The local quota ledger will then keep
the whole network inside the single 10,000-unit pool (~5 uploads/day max).
Recommended: the per-channel setup above.
</details>

### Step 3 — Connect the channels (10 min, double-click wizard)
On your own computer (needs Python 3.8+ — nothing else, no pip installs):
1. Extract the repo zip
2. Double-click **`START-HERE.bat`** (Windows) or **`START-HERE.command`** (Mac)
3. For each channel the wizard takes the client JSON (type its path or paste
   the content), opens your browser, waits for your **Allow** click, exchanges
   the code for a permanent refresh token and **verifies it live** — it prints
   your channel name + subscriber count on the spot.
4. At the end it prints the **FACTORY_ENV block** (also saved to a private
   `factory.env` file you must never upload). That single block replaces ALL
   13 secrets of the old setup.

Command-line equivalent:

```bash
python tools/setup_wizard.py            # guide all 4 channels
python tools/setup_wizard.py --verify   # re-check saved connections
python tools/setup_wizard.py --redo money   # redo a single channel
```

> Google shows a "This app isn't verified" warning — click
> *Advanced → Go to … (unsafe) → Continue* (it's your own app).

### Step 4 — GitHub repository + ONE secret (5 min)
1. GitHub → **New repository** → name `tube-autopilot`, visibility **Public**
   (public = unlimited free Actions minutes; the repo contains no secrets)
2. Upload this folder — easiest: on the repo page click
   **"uploading an existing file"** and drag everything in
   (⚠️ NOT the `factory.env` file — it stays on your computer) → Commit.
3. Repo → **Settings → Secrets and variables → Actions → New repository
   secret** → Name: `FACTORY_ENV` → paste the wizard's block.
   - Optional second secret: `GEMINI_API_KEY` (if you didn't give it to the
     wizard). One secret is enough otherwise.
4. Repo → **Settings → Actions → General → Workflow permissions** →
   **Read and write** → Save

How it works: every workflow writes the `FACTORY_ENV` secret into a local
`.env`, and `src/config.py` loads it at import time. Real env vars still win,
so the legacy per-secret style below keeps working if you prefer it.

<details><summary>ADVANCED: legacy style (13 secrets, git CLI, shared project)</summary>

| Secret name | Value |
|---|---|
| `GEMINI_API_KEY` | key from Step 1 |
| `YT_CLIENT_ID_<CH>` / `YT_CLIENT_SECRET_<CH>` / `YT_REFRESH_TOKEN_<CH>` | one triple per channel (`MINDSET`, `FACTS`, `TECH`, `MONEY`) — from each channel's client JSON + `tools/auth.py --channel <ch>` |

Shared-project shortcut: use one project + one `client_secret.json` for all
channels and only add the global `YT_CLIENT_ID` + `YT_CLIENT_SECRET` secrets —
every workflow falls back to them, and the local quota ledger keeps the
network inside the single 10,000-unit pool (~5 uploads/day max).

Pushing via git CLI instead of web upload:

```bash
cd tube-autopilot
git init -b main
git add .   # .gitignore already blocks factory.env / .env / client_secret*.json
git commit -m "autopilot online"
git remote add origin https://github.com/<you>/tube-autopilot.git
git push -u origin main
```
</details>

### Step 5 — Test run (5 min)
GitHub → **Actions** tab → enable workflows → pick any channel workflow
(e.g. **daily-mindset**) → **Run workflow** → leave `dry_run` unchecked for a
real run (check it for a no-upload rehearsal).
Watch the job (~5 minutes); it uploads the finished video + thumbnail + script
as an **artifact** you can download and review. Repeat per channel if you like.
Each dispatch ships the NEXT slot of the day; each channel stops by itself at
its `daily_uploads` target (3). The 12 daily crons take over automatically.

### Step 6 — The YouTube API audit (important, 5 min)
Unverified API projects (created after July 2020) often have their uploads
**locked to private** by YouTube. Two options:

- **Recommended:** search **"YouTube Data API Audit Form"** and submit it (free,
  approval usually within days). Until approved, uploads may stay private.
- Meanwhile, publish manually: YouTube Studio → your video → *Edit → Visibility
  → Public*. Or set `visibility: private` in the channel yaml and flip each
  video manually after review.

### Step 7 — Review mode (optional)
Want to approve videos before they go public? In `channels/*.yaml` set:
```yaml
visibility: private   # pipeline uploads as private; you publish in YouTube Studio
```
Flip back to `public` when you trust the machine (most people do after a week).

---

## Configuration reference

Everything lives in `channels/<id>.yaml`:

| Field | What it controls |
|---|---|
| `display_name` | Channel brand used in thumbnails/descriptions |
| `voice` / `voice_rate` | Edge-TTS voice (e.g. `en-US-AriaNeural`) and speed |
| `caption_font` / `caption_size` | Caption typography |
| `palette` | Background gradient + accent colors (hex) |
| `trends.mode` | `news` (headline-driven), `trends` (Google Trends), `theme` (evergreen) |
| `hashtags` | SEO hashtags appended to title/description |
| `daily_uploads` | Videos per channel per day (default 3; 1–5 sane on a personal quota) |
| `engagement_question` | Comment-bait question in every description (algorithm food) |
| `links` / `affiliate` | Affiliate/book links block + disclaimer in descriptions |
| `visibility` | `public` or `private` (review mode) |
| `music_mood` | `epic` / `curious` / `neon` / `wealth` chord progressions |
| `title_patterns` | Fallback title templates |

Run locally any time:
```bash
python main.py --channel tech            # full run
python main.py --channel all --dry-run   # render only, no upload
python main.py --channel facts --offline # no network: banks only
```

## How it works (file map)

```
main.py                     orchestrator (per channel)
src/trends.py               Google News + Google Trends RSS → daily topic
src/scriptwriter.py         Gemini JSON script + hard validation + bank fallback
src/content_bank.py         curated quotes/facts/rules (never runs dry)
src/tts.py                  Edge-TTS + word-level timing capture
src/captions.py             word-synced ASS subtitles + scene cut timing
src/visuals.py              gradient backgrounds, bokeh, thumbnails (PIL)
src/music.py                copyright-safe chord-pad synthesizer (numpy)
src/assemble.py             ffmpeg: zoompan scenes → concat → mux + burn subs
src/metadata.py             SEO title/description/tags assembly
src/youtube.py              resumable upload + thumbnail + stats
src/history.py              anti-repeat topic memory (data/history/*.json)
src/intelligence.py         🧠 self-tuning brain (bias.json — weekly learning)
.github/workflows/daily-mindset.yml  channel 1 — cron 10:30 UTC
.github/workflows/daily-tech.yml     channel 2 — cron 13:30 UTC
.github/workflows/daily-money.yml    channel 3 — cron 15:00 UTC
.github/workflows/daily-facts.yml    channel 4 — cron 16:30 UTC
.github/workflows/weekly-report.yml  Monday: analytics + brain update + issue
tools/setup_wizard.py       zero-install OAuth wizard (double-click START-HERE)
tools/auth.py               pip-installed OAuth variant (advanced)
tools/report.py             weekly stats + self-tuning update
SETUP.md                    click-by-click one-time setup guide
START-HERE.bat / .command   double-click launchers for the wizard
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `quotaExceeded` on upload | Per-channel projects each have 10,000 units/day (3 videos + thumbnails = 4,950). If you see it, you ran many manual tests on one project — wait for the daily reset (midnight PT). A local ledger also refuses uploads before the hard 403. |
| Factory does nothing in Actions (`missing secrets …`) | The `FACTORY_ENV` secret is empty/missing — re-copy the wizard's block, ALL lines between the CUT HERE markers. |
| Connection dies after ~7 days | You left the OAuth app in Testing mode — **PUBLISH APP** (Step 2), then `python tools/setup_wizard.py --redo <channel>` and update the secret. |
| Uploads stay **private** | The unverified-app lock — submit the API audit form (Step 6). |
| `401 invalid_grant` on upload | Refresh token revoked (password change / consent revoked). Re-run `python tools/setup_wizard.py --redo <channel>`, update the FACTORY_ENV secret. |
| Voice/TTS fails in Actions | Rare transient Microsoft endpoint error — the failure issue fires; next daily run succeeds. Nothing to fix. |
| Cron didn't run | GitHub delays scheduled runs at busy times (up to ~30 min). Also: workflows pause after 60 days of repo inactivity — the daily history commits keep the repo permanently active, so this should never happen. |
| History/bias push fails | Repo **Settings → Actions → General → Workflow permissions → Read and write** — the workflows already request `contents: write`; this toggle just allows it. |
| Captions look small/big | Tune `caption_size` in the channel yaml. |
| Want a new niche | Copy a yaml, edit palette/voice/trends/hashtags, add the id to `CHANNEL_IDS` in `src/config.py`, copy any `daily-*.yml` and point it at the new channel. |

## Scaling ideas (v2 roadmap)

- ✅ **Analytics-driven topics**: built — `src/intelligence.py` biases topics
  and titles toward proven winners every Monday.
- ✅ **Duplicate protection**: built — one upload per channel per day, enforced.
- **Long-form engine**: repurpose the daily script into an 8-minute "top 10"
  video — this is where real watch-hours and mid-roll revenue live.
- **Cross-posting**: auto-post the same Short to TikTok / Reels / Pinterest for free reach.
- **A/B title optimizer**: weekly workflow rewrites titles of videos with low CTR.
- **Comment auto-replies**: engagement boost with a polite template (use sparingly).

## Notes

- Fonts: Anton & Archivo Black (SIL Open Font License — bundled in `assets/fonts/`).
- Edge-TTS voices and Gemini free tiers are subject to their providers' terms;
  the pipeline degrades gracefully to offline banks if either disappears.
- You own the channels and are responsible for the content they publish.
