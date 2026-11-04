# 🚀 SETUP — the one-time "little hell" (about 40 minutes, then forever)

This is the ONLY manual work you will ever do. Google requires the account
owner (you) to click "Allow" 4 times — no person or bot can do that part,
not even your assistant. Everything else is already built, and the wizard
below verifies every connection instantly.

> **Golden rule:** you will NEVER type a password into this project, and you
> should never send passwords to anyone (including your assistant). You only
> click "Allow" inside Google's own official screens in your own browser.

---

## Your 4 channels (fill in your Gmails as you go)

| # | Gmail | YouTube channel name | Handle | Google Cloud project name | Niche |
|---|-------|----------------------|--------|---------------------------|-------|
| 1 | `<GMAIL-1>` | Zenith Mindset | @ZenithMindset | tube-zenith-mindset | Motivation |
| 2 | `<GMAIL-2>` | Fact Vault | @FactVaultHD | tube-fact-vault | Facts |
| 3 | `<GMAIL-3>` | AI Chronicle | @AIChronicleNow | tube-ai-chronicle | AI / tech |
| 4 | `<GMAIL-4>` | Wealth Signals | @WealthSignalsHQ | tube-wealth-signals | Money |

Each channel = its own Gmail + its own Google Cloud project + its own daily
API quota + its own posting clock. They never interfere with each other.

> If your download was personalized by your assistant, your 4 addresses
> are already filled in here, and the setup wizard shows the **exact Gmail
> to use** at every sign-in step (it reads the private file
> `data/my-gmails.json` — that file is ignored by git and never gets
> uploaded anywhere).

---

## Step 0 — Install Python (3 minutes, once)

1. Open **https://www.python.org/downloads/**
2. Download and run the installer.
   ⚠️ Windows: tick **"Add python.exe to PATH"** on the first screen.
3. That's it — nothing else to install.

---

## Step 1 — Create the 4 YouTube channels (8 minutes)

A brand-new Gmail has no YouTube channel yet, so create one (name it EXACTLY
as in the table — the factory's branding depends on it):

1. Sign in to **https://youtube.com** with `<GMAIL-1>`
2. Click your **profile picture (top right) → "Create a channel"**
3. Channel name: **Zenith Mindset** → handle: **@ZenithMindset** → Create
4. Sign out, repeat with `<GMAIL-2>` → **Fact Vault** / **@FactVaultHD**,
   `<GMAIL-3>` → **AI Chronicle** / **@AIChronicleNow**,
   `<GMAIL-4>` → **Wealth Signals** / **@WealthSignalsHQ**

> Don't upload anything, don't customize anything — the factory does all of that.

---

## Step 2 — The 4 Google Cloud mini-projects (~6 minutes each)

One project per channel = one private 10,000-unit/day API quota per channel.
Do this 4 times — once while signed in with each Gmail.

**For channel 1 (mindset), signed in as `<GMAIL-1>`:**

1. Open **https://console.cloud.google.com**
   (if it asks about a country/terms → accept; if it offers a tour → skip)
2. Top bar → project picker → **New project** → name: `tube-zenith-mindset`
   → **Create** (make sure it's selected in the top bar afterwards)
   *(If Google ever asks about billing — you can safely skip it. The
   YouTube API free quota needs no billing.)*
3. **https://console.cloud.google.com/apis/library** → search
   **YouTube Data API v3** → **Enable**
4. **OAuth consent screen** — in the left menu under *APIs & Services*:
   - **Get started / Configure**: app name `Zenith Factory`,
     user support email = `<GMAIL-1>`
   - Audience: **External**
   - Contact email = `<GMAIL-1>` → Save
   - **Test users → + Add users** → add `<GMAIL-1>` (yourself)
   - Back on the summary page → **PUBLISH APP → Confirm**
   ⚠️ **This PUBLISH click is critical** — without it Google kills your
   connection token every 7 days. Published = permanent. The "unverified
   app" warning you'll see later is normal and harmless for personal apps.
5. **APIs & Services → Credentials → + Create credentials → OAuth client ID**
   - Application type: **Desktop app** → name: `factory` → **Create**
   - **Download JSON** (top right of the popup) → keep the file

**Repeat the same 5 moves with the other 3 Gmails:**

| While signed in as | Project name | App name | Test user | Save JSON as |
|--------------------|--------------|----------|------------|--------------|
| `<GMAIL-1>` | tube-zenith-mindset | Zenith Factory | `<GMAIL-1>` | client_secret_mindset.json |
| `<GMAIL-2>` | tube-fact-vault | Fact Factory | `<GMAIL-2>` | client_secret_facts.json |
| `<GMAIL-3>` | tube-ai-chronicle | AI Factory | `<GMAIL-3>` | client_secret_tech.json |
| `<GMAIL-4>` | tube-wealth-signals | Wealth Factory | `<GMAIL-4>` | client_secret_money.json |

(Renaming the downloaded file is optional — the wizard also accepts pasted
JSON content or any file path.)

---

## Step 3 — Run the wizard (10 minutes, guided, double-click)

1. Extract `tube-autopilot.zip` to your computer (Desktop is fine)
2. Double-click **START-HERE.bat** (Windows) or **START-HERE.command** (Mac)
3. For each of the 4 channels the wizard will:
   - ask for that channel's JSON (type its path, or paste its content)
   - open your browser → sign in with THAT channel's Gmail — the terminal
     shows the exact address to use (mindset = Gmail 1, facts = 2,
     tech = 3, money = 4)
   - you may see *"Google hasn't verified this app"* → click
     **Advanced → Go to tube-… (unsafe) → Continue** (it's YOUR own app)
   - click **Allow / Continue** on the permission page
   - the terminal instantly shows:
     `CONNECTED -> channel 'Zenith Mindset' (0 subscribers | 0 videos)`
4. At the end the wizard prints a block between two `CUT HERE` lines —
   that block is your **FACTORY_ENV**. It also gets saved to a private file
   `factory.env` in the same folder.

**Then (optional but recommended):** paste that block back to your assistant
in the chat — it gets pre-flight checked (all 4 tokens verified against the
live YouTube API) *before* you touch GitHub.

> The block contains keys that can upload to your channels — treat it like a
> password. Its only two safe homes: the chat with your assistant (for the
> pre-flight check) and the GitHub secret in Step 4. Never post it anywhere else.

---

## Step 4 — GitHub (2 routes — pick ONE)

### Option A — your assistant does ALL of it (recommended, ~3 min) — **CHOSEN (2026-11-05)**
1. Create a free account at **https://github.com/signup** (verify the email)
2. Profile picture (top right) → **Settings → Developer settings**
   (left menu, near the bottom) → **Personal access tokens →
   Tokens (classic) → Generate new token (classic)**:
   - Note: `tube-autopilot` · Expiration: **7 days**
   - ✓ tick **repo** · ✓ tick **workflow**
3. **Generate token** → copy the `ghp_…` code → send it to your assistant.
4. Done. The assistant then creates the public repo, pushes the v3 code
   (including the 115 MB vendored offline voice models — one-time push,
   a few minutes), enables permissions, sets your YouTube secrets,
   runs the smoke-test (offline render of all 4 channels) and the first
   real gated run, and confirms video #1 is live + verified public.
   Afterwards delete the token (same page) — the daily factory never
   needs it again.
   > The token is a key to your GitHub only — NOT your Google accounts.
   > Never paste it anywhere except your assistant chat.
   > v3 note: there is NO AI API key anymore anywhere in this setup —
   > writing is bank-only and the voice is local. The only secrets are
   > the YouTube OAuth ones from Step 2.

### Option B — do it yourself (5 min)
1. **https://github.com/new** → repository name: `tube-autopilot` →
   visibility: **Public** (required for free unlimited Actions minutes;
   the repo contains zero secrets) → **Create repository**
2. On the "Quick setup" page click **"uploading an existing file"**
   → drag in **everything inside the extracted tube-autopilot folder**
   (all files and folders) → **Commit changes**.
   ⚠️ Do NOT drag the `factory.env` file or `data/my-gmails.json` —
   those stay private on your computer (they hold your keys/addresses).
3. Repo → **Settings → Secrets and variables → Actions →
   New repository secret**:
   - Name: `FACTORY_ENV`
   - Secret: paste the whole block from the wizard (Step 3)
   > v3: there is NO Gemini/AI secret — writing is bank-only (owner
   > rule). The voice models live in the repo (no service to authenticate).
4. Repo → **Settings → Actions → General → Workflow permissions** →
   select **Read and write permissions** → Save
   (this lets the robot commit its topic memory + learned bias)

---

## Step 5 — First video (5 minutes)

> If your assistant set up the repo (Option A), a **smoke-test** has already
> run: all 4 channels rendered a full offline test video on GitHub's own
> servers, proving the machinery works. Re-run it any time from the Actions
> tab → **smoke-test** → Run workflow.

1. Repo → **Actions** tab (yellow bar: *"Workflows aren't being run on this
   repository*" → **"I understand my workflows, go ahead and enable them"**)
2. Left sidebar → **daily-mindset** → **Run workflow** → leave `dry_run`
   unchecked → **Run workflow**
3. Click the run → watch the log (about 5 minutes) —
   topic → script → voice → captions → render → **upload**
4. Open **https://youtube.com** with `<GMAIL-1>` → your first Short is live
   🎉 From this moment: 12 videos/day, every day, forever, hands-free.

---

## Step 6 — One form to keep uploads public (5 minutes, important)

YouTube sometimes locks API-uploaded videos to **private** on unverified
projects. Two options:

- **Recommended:** search Google for **"YouTube Data API Audit Form"**,
  submit it once (free, approval typically within days)
- **Meanwhile:** YouTube Studio → each video → Visibility → Public
  (or set `visibility: private` in `channels/mindset.yaml` and flip videos
  manually after you review them)

---

## When something looks wrong

| Symptom | Meaning / fix |
|---|---|
| Wizard says `no YouTube channel yet` | You skipped Step 1 — create the channel on youtube.com, then `python tools/setup_wizard.py --verify` |
| `Google hasn't verified this app` | Normal — Advanced → Go to … (unsafe) → Continue |
| Uploads stay private | The unverified-app lock — see Step 6 |
| `401 invalid_grant` later on | Token revoked (password change / you removed app access). Re-run the wizard `--redo <channel>`, update the FACTORY_ENV secret |
| Run failed in Actions | The repo auto-opens a GitHub issue with the exact log link — read it, or send it to your assistant |

Full deep reference: **README.md** · The forever money plan: **PLAN.md**
