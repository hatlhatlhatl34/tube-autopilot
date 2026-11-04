#!/usr/bin/env python3
"""One-time OAuth helper — generates a refresh token per channel account.

**Recommended: one Google Cloud PROJECT per channel** (each project gets its
own 10,000 daily API quota units). Run once per channel:

    pip install -r requirements.txt

    python tools/auth.py --channel mindset --client-secret client_secret_mindset.json
    python tools/auth.py --channel facts   --client-secret client_secret_facts.json
    python tools/auth.py --channel tech    --client-secret client_secret_tech.json
    python tools/auth.py --channel money   --client-secret client_secret_money.json

Log in with the Google account that OWNS that channel. The script prints the
three GitHub secrets for that channel:

    YT_CLIENT_ID_<CH>      (from the JSON you downloaded)
    YT_CLIENT_SECRET_<CH>  (from the JSON you downloaded)
    YT_REFRESH_TOKEN_<CH>  (generated here)

A shared single-project setup also works: use the same client_secret.json for
all channels and add the global YT_CLIENT_ID / YT_CLIENT_SECRET secrets.
"""
from __future__ import annotations

import argparse
import json
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True,
                    help="channel id: mindset | facts | tech | money")
    ap.add_argument("--client-secret", default="client_secret.json",
                    help="OAuth client JSON downloaded from that channel's Google Cloud project")
    args = ap.parse_args()

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("pip install -r requirements.txt first")
        return 1

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secret, SCOPES)
    print("\nA browser window opens → log in with the Google account that OWNS this channel.\n")
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    ch = args.channel.upper()
    try:
        client_config = json.load(open(args.client_secret))
        installed = client_config.get("installed") or client_config.get("web") or {}
        client_id = installed.get("client_id", "<see your client_secret JSON>")
        client_secret = installed.get("client_secret", "<see your client_secret JSON>")
    except Exception:
        client_id = client_secret = "<see your client_secret JSON>"

    print("\n" + "=" * 64)
    print(f"Add these 3 values to GitHub → repo → Settings → Secrets → Actions:")
    print(f"  YT_CLIENT_ID_{ch}        = {client_id[:24]}…")
    print(f"  YT_CLIENT_SECRET_{ch}    = {client_secret[:12]}…")
    print(f"  YT_REFRESH_TOKEN_{ch}    = {creds.refresh_token}")
    print("=" * 64)
    print("(full values hidden above for safety — the refresh token is shown as-is;")
    print(" copy client_id/client_secret directly from the JSON file you downloaded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
