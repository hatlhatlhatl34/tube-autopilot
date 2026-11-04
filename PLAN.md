# 🏭 The Forever Plan — tube-autopilot Master Schedule

> **v3 (2026-11-05):** the network now runs QUOTA-SAFE by default — 1
> video/day/channel (works even if all 4 share one GCP project). The
> scale-up below (3/day/channel on dedicated projects) is UNLOCKED:
> set `daily_uploads` per channel in `channels/<ch>.yaml` when that
> channel has its own project/quota. Writing is bank-only (no AI API)
> and the voice is local/offline — see RESTORE-NOTES.md.

> **One-time setup. Zero maintenance. Zero code changes. Ever.**
> Every channel runs its own Google Cloud project with its **own personal
> 10,000 daily quota units**, so each channel posts **3 Shorts a day** —
> 12 videos/day, 360/month across the network. This document is the plan
> the system follows forever; it tunes itself, you never touch code.

---

## 0. The Daily Clock (all automatic)

| UTC | New York | Channel | Video of the day | Slot logic |
|---|---|---|---|---|
| 09:30 | 04:30 | 🤖 AI Chronicle | Short #1 | early news |
| 10:30 | 05:30 | 🧠 Zenith Mindset | Short #1 | morning motivation |
| 12:30 | 07:30 | 🧪 Fact Vault | Short #1 | breakfast scroll |
| 13:30 | 08:30 | 🤖 AI Chronicle | Short #2 | commute news |
| 15:00 | 10:00 | 💰 Wealth Signals | Short #1 | market open |
| 16:30 | 11:30 | 🧠 Zenith Mindset | Short #2 | midday reset |
| 17:30 | 12:30 | 🧪 Fact Vault | Short #2 | lunch scroll |
| 19:00 | 14:00 | 💰 Wealth Signals | Short #2 | afternoon market |
| 21:30 | 16:30 | 🤖 AI Chronicle | Short #3 | evening recap |
| 23:30 | 18:30 | 💰 Wealth Signals | Short #3 | evening planning |
| 00:30 | 19:30 | 🧪 Fact Vault | Short #3 | prime time |
| 01:30 | 20:30 | 🧠 Zenith Mindset | Short #3 | night reflection |

Each trigger is slot-aware: the 2nd and 3rd runs pick **different topics**
(rotated trend headlines / themes), so a channel's 3 daily videos never
overlap. Every run: live trends → original script → neural voice →
word-synced captions → auto thumbnail (3 rotating layouts) → SEO title
(picked by a CTR-scoring engine) → rich description → upload → memory.
**Daily history commits keep the GitHub cron alive forever.**

## 1. The Weekly Brain (Monday 08:00 UTC)

Pulls live stats for all 4 channels → learns per channel: best title style,
hottest topics → writes `data/history/bias.json` → every future video is
biased toward proven winners. Opens the "📊 Weekly Empire Report" issue
(you get it by email). Compounding, weekly, forever — via a **data file
the system edits itself**, never code.

## 2. Guardrails (why you can forget it)

| Risk | Guard |
|---|---|
| Repeating topics | 120-topic anti-repeat memory + slot rotation |
| More uploads than planned | count-guard: channel stops at its `daily_uploads` |
| Quota overrun | local ledger per project (3/day = 4,950 of 10,000 — never hit) |
| A channel fails | GitHub issue → email; the other 3 channels unaffected |
| Cron pausing (60 idle days) | daily history commits = permanent activity |
| Gemini down | offline content banks — the video still ships |
| Trend feeds down | evergreen theme fallback |
| Demonetization risk | unique scripts, no invented stats, honest titles, varied visuals + thumbnail layouts |

---

# 🧭 Individual Forever Plans

## 🧠 Channel 1 — Zenith Mindset (`mindset`)

**Mission:** become the daily discipline habit of 100k people.
**Cadence:** 3 Shorts/day (05:30 / 11:30 / 20:30 NY) — morning jolt, midday
reset, night reflection. Evergreen themes (discipline, focus, resilience…)
flavored with trending self-improvement news.
**Why it exists:** highest shareability ("send this to a friend who's
stuck"), fastest subscriber growth of the four — it's the network's
audience engine.

| Milestone | Target | What it unlocks |
|---|---|---|
| Day 30 | 300–800 subs, 30–90 videos live | first affiliate clicks |
| Day 90 | 1,500–5,000 subs | YPP-eligible territory |
| Day 180 | 5k–20k subs, 500+ video library | apply YPP → ads on |

**Money plan (pre-YPP → post-YPP):**
1. Affiliate: self-improvement books & journals (Atomic Habits, journaling
   tools) in `links:` of `channels/mindset.yaml` — motivation audiences buy
   these at high rates.
2. Ads: motivational Shorts RPM $2–6 — the second revenue pillar.
3. Long-term: a "morning routine" digital product is the classic upsell.
**Self-tuning focus:** the brain optimizes which theme (discipline vs
resilience vs…) and which title style earns most attention weekly.

## 🤖 Channel 2 — AI Chronicle (`tech`)

**Mission:** the 60-second AI news habit for busy people.
**Cadence:** 3 Shorts/day (04:30 / 08:30 / 16:30 NY) — built from live
Google News headlines, so content is always riding the day's search wave.
**Why it exists:** highest CPM audience of the network (tech advertisers
pay premium) + trend-driven topics attract search traffic long after
posting. This is the network's RPM king.

| Milestone | Target | What it unlocks |
|---|---|---|
| Day 30 | 400–1,200 subs | affiliate clicks (AI tools) |
| Day 90 | 2,000–6,000 subs | YPP-eligible territory |
| Day 180 | 8k–30k subs, trending-video streaks | ads at $8–15 RPM territory |

**Money plan:**
1. Affiliate: AI tool sign-ups (writing/image/automation tools) — SaaS
   affiliate programs pay recurring commissions, the best money in this niche.
2. Ads: highest RPM of the four channels once YPP hits.
3. Later: sponsor reads ("this video is powered by…") at 10k+ subs.
**Self-tuning focus:** which headline angle (product launches vs research
vs warnings) pulls most views.

## 💰 Channel 3 — Wealth Signals (`money`)

**Mission:** one money rule a day that compounds.
**Cadence:** 3 Shorts/day (10:00 / 14:00 / 18:30 NY) — synced to market
hours, when finance attention peaks.
**Why it exists:** the RPM ceiling of the entire network ($10–20 RPM is
common) + finance affiliate programs are the most lucrative. If one
channel "prints money," it's this one.

| Milestone | Target | What it unlocks |
|---|---|---|
| Day 30 | 300–1,000 subs | finance affiliate clicks begin |
| Day 90 | 1,500–5,000 subs | YPP-eligible territory |
| Day 180 | 6k–25k subs | premium finance ad RPM |

**Money plan:**
1. Affiliate: budgeting apps, broker sign-up bonuses, investing newsletters
   — finance affiliates pay $5–100+ per conversion. Add to
   `channels/money.yaml` → `links:` once you have accounts.
2. Ads: finance RPM is the network's ceiling.
3. Later: a simple budgeting PDF as a lead magnet.
**Self-tuning focus:** which rule framing (psychology vs mechanics vs
"rich people do X") the audience rewards.

## 🧪 Channel 4 — Fact Vault (`facts`)

**Mission:** the daily "wait, WHAT?" moment.
**Cadence:** 3 Shorts/day (07:30 / 12:30 / 19:30 NY) — themes drawn from
Google's daily trending searches, so the topic is what the world is
already curious about today.
**Why it exists:** pure volume play — highest viral ceiling of the four
(Shorts algorithm loves facts), 3 lottery tickets daily, and the
subscriber engine that feeds cross-promotion to the other three.

| Milestone | Target | What it unlocks |
|---|---|---|
| Day 30 | 500–2,000 subs | network cross-promo value |
| Day 90 | 3,000–10,000 subs | YPP-eligible territory |
| Day 180 | 15k–60k subs, a shot at a 1M-view Short | ads at scale |

**Money plan:**
1. Pre-YPP: this channel monetizes through the network (cross-promo in
   every description funnels its huge audience to the 3 money channels).
2. Ads: lower RPM, but volume × viral ceiling = serious total.
3. Later: fact compilations = ideal long-form material for watch-hours.
**Self-tuning focus:** which fact categories (space, history, biology,
psychology) go viral for THIS audience.

---

## 3. The Money Road (network view)

**Phase 0 (day 1):** affiliate links in descriptions — revenue before any
subscriber threshold. Highest-converting spots: money + tech channels.
**Phase 1 (months 1–3):** compounding — 12 videos/day, 360/month. The
Monday brain shifts each channel toward what its audience proves it wants.
**Phase 2 (months 3–6, per channel):** 1,000 subs + 10M Shorts views (90d)
or 4,000 watch-hours → apply to YPP per channel from YouTube Studio.
**Phase 3 (month 6+):** ads on 4 independent income streams + affiliate
income + (optional) cross-posting the same videos to TikTok/Reels for
free extra reach.

**Honest math:** Shorts RPM $0.05–0.30/1k generic, but finance/tech sit at
the top; 4 channels × 3 daily posts = 12 daily lottery tickets with
compounding libraries. You said ~6 months to first money — realistic.
The system's job is to maximize the odds every single day without you.

## 4. You vs the machine

**You (once, ~45 min):** 4 Google Cloud projects (one per channel = own
quota), 4 OAuth tokens, GitHub repo + 13 secrets — README.md walks you
through every click.

**You (optional, forever):** reply to comments sometimes; drop affiliate
links into the yaml `links:` block when you have them; read Monday's
email report.

**The machine (forever):** everything else.
