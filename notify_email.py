#!/usr/bin/env python3
"""
notify_email.py  --  emails a digest of NEW jobs via Gmail

It only sends when there are new jobs, so you won't get empty emails.

ONE-TIME GMAIL SETUP (needed because Gmail blocks plain-password logins)
------------------------------------------------------------------------
1. Turn on 2-Step Verification for your Google account (if it isn't already):
       https://myaccount.google.com/security
2. Create an "App Password" (a 16-character code just for this script):
       https://myaccount.google.com/apppasswords
   Name it something like "Job Scraper". Google shows you 16 characters.
3. Open config.py and fill in:
       EMAIL_FROM          = "you@gmail.com"
       EMAIL_APP_PASSWORD  = "the 16-char app password"   (spaces are fine)
       EMAIL_TO            = "where to send it"  (can be the same address)
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from config import EMAIL_FROM, EMAIL_APP_PASSWORD, EMAIL_TO
except ImportError:
    EMAIL_FROM = EMAIL_APP_PASSWORD = EMAIL_TO = ""


def is_configured():
    return bool(EMAIL_FROM and EMAIL_APP_PASSWORD and EMAIL_TO)


def build_html(new_jobs):
    rows = ""
    for j in new_jobs:
        posted = f" &middot; {j.get('posted','')}" if j.get("posted") else ""
        rows += (
            f'<tr><td style="padding:10px 0;border-bottom:1px solid #eee;">'
            f'<a href="{j.get("url","")}" style="font-size:15px;font-weight:600;'
            f'color:#0b74c4;text-decoration:none;">{j.get("title","")}</a><br>'
            f'<span style="color:#555;font-size:13px;">{j.get("company","")} '
            f'&middot; {j.get("location","")}{posted}</span></td></tr>'
        )
    return (
        f'<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">'
        f'<h2 style="color:#0f172a;">{len(new_jobs)} new Las Vegas tech job'
        f'{"" if len(new_jobs)==1 else "s"} today</h2>'
        f'<p style="color:#555;font-size:13px;">Networking &amp; cybersecurity roles '
        f'for students, in and around Las Vegas / Henderson.</p>'
        f'<table style="width:100%;border-collapse:collapse;">{rows}</table>'
        f'<p style="color:#999;font-size:12px;margin-top:20px;">'
        f'Sent automatically by your job scraper.</p></div>'
    )


def send(new_jobs):
    """Send the digest. Returns True if an email went out."""
    if not is_configured():
        print("  (email skipped -- fill in EMAIL_* values in config.py)")
        return False
    if not new_jobs:
        print("  (no new jobs -- no email sent)")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{len(new_jobs)} new Las Vegas tech job" \
                     f"{'' if len(new_jobs)==1 else 's'} today"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(build_html(new_jobs), "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        # App passwords are shown with spaces; Gmail ignores them, so strip.
        server.login(EMAIL_FROM, EMAIL_APP_PASSWORD.replace(" ", ""))
        server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
    print(f"  emailed {len(new_jobs)} new job(s) to {EMAIL_TO}")
    return True


if __name__ == "__main__":
    # Quick test using whatever is in new_jobs.csv.
    import csv, os
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "new_jobs.csv")
    jobs = list(csv.DictReader(open(path, encoding="utf-8"))) if os.path.exists(path) else []
    send(jobs)
