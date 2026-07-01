#!/usr/bin/env python3
"""
update_jobs.py  --  the DAILY runner

WHAT IT DOES (each time it runs)
--------------------------------
1. Pulls jobs from every source that's set up (The Muse always; Adzuna if you've
   added a key in config.py).
2. Compares them against a memory file (seen_jobs.json) of everything it has
   found before.
3. Writes three things:
       all_jobs.csv    -- the full current list, newest first
       new_jobs.csv    -- ONLY the jobs it had never seen before (today's news)
       update_log.txt  -- one line per run, so you can see the history
4. Remembers the new jobs so tomorrow they count as "old."

Run it by hand any time:
    python3 update_jobs.py

Or let it run automatically every morning (see setup_daily.sh).
"""

import csv
import json
import os
from datetime import datetime

# Reuse the two collectors we already wrote.
import find_jobs                 # The Muse
import find_jobs_adzuna          # Adzuna (only works if config.py has keys)
import find_jobs_employers       # targeted searches for specific local employers
import build_site                # rebuilds index.html (the filterable web page)
import notify_email              # emails a digest of new jobs (if configured)

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(HERE, "seen_jobs.json")
ALL_CSV = os.path.join(HERE, "all_jobs.csv")
NEW_CSV = os.path.join(HERE, "new_jobs.csv")
LOG_FILE = os.path.join(HERE, "update_log.txt")

FIELDS = ["first_seen", "title", "company", "location", "source",
          "posted", "employer", "internship", "url"]


def normalize(job, source):
    """Turn a source-specific job dict into our common shape, adding tags."""
    title = job.get("title", "")
    company = job.get("company", "")
    # "employer" is set if this is one of our watched local employers -- either
    # the employer source already tagged it, or the company name matches.
    employer = job.get("employer", "") or find_jobs_employers.match_employer(company)
    return {
        "title": title,
        "company": company,
        "location": job.get("location", ""),
        "source": source,
        "posted": job.get("posted", ""),       # Adzuna has a date; Muse doesn't
        "employer": employer,
        "internship": "yes" if "intern" in title.lower() else "",
        "url": job.get("url", ""),
    }


def gather_all():
    """Collect from every available source and return a list of normalized jobs."""
    jobs = []

    # --- The Muse (always available, no key) ---
    try:
        for j in find_jobs.collect_jobs():
            jobs.append(normalize(j, "TheMuse"))
    except Exception as e:
        print(f"  ! The Muse source failed: {e}")

    # --- Adzuna (only if keys are present) ---
    if find_jobs_adzuna.ADZUNA_APP_ID and find_jobs_adzuna.ADZUNA_APP_KEY:
        try:
            for j in find_jobs_adzuna.collect_jobs():
                jobs.append(normalize(j, "Adzuna"))
        except Exception as e:
            print(f"  ! Adzuna source failed: {e}")

        # --- Specific local employers (also via Adzuna) ---
        try:
            for j in find_jobs_employers.collect_jobs():
                jobs.append(normalize(j, "Employer"))
        except Exception as e:
            print(f"  ! Employer source failed: {e}")
    else:
        print("  (Adzuna skipped -- no key in config.py yet)")

    return jobs


def load_history():
    """Return the dict of {url: first_seen_date} we've saved before."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"=== Daily job update: {today} ===")

    history = load_history()
    jobs = gather_all()

    # Dedupe this run's jobs. The same posting can appear more than once (from
    # different search terms, or the same job under two Adzuna URLs), so we key
    # on title+company rather than URL to catch those near-duplicates.
    unique = {}
    for j in jobs:
        key = f"{j['title'].strip().lower()}|{j['company'].strip().lower()}"
        if key not in unique:
            unique[key] = j

    all_rows, new_rows = [], []
    for key, job in unique.items():
        if key in history:
            first_seen = history[key]          # seen on an earlier day
        else:
            first_seen = today                 # brand new today
            history[key] = today
            new_rows.append({**job, "first_seen": first_seen})
        all_rows.append({**job, "first_seen": first_seen})

    # Newest-posted first; jobs without a posted date sink to the bottom.
    all_rows.sort(key=lambda r: r.get("posted", ""), reverse=True)
    new_rows.sort(key=lambda r: r.get("posted", ""), reverse=True)

    write_csv(ALL_CSV, all_rows)
    write_csv(NEW_CSV, new_rows)
    save_history(history)

    # Rebuild the public web page from the full list.
    build_site.build(all_rows)

    # Email a digest of just the new jobs (does nothing if email isn't set up).
    try:
        notify_email.send(new_rows)
    except Exception as e:
        print(f"  ! email failed: {e}")

    # Append one line to the run log.
    line = f"{datetime.now():%Y-%m-%d %H:%M}  total={len(all_rows):3d}  new={len(new_rows):3d}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

    print(f"Total jobs on the list: {len(all_rows)}")
    print(f"NEW since last run:      {len(new_rows)}")
    if new_rows:
        print("\nToday's new postings:")
        for r in new_rows[:15]:
            print(f"  - {r['title']} @ {r['company']} ({r['location']}) [{r['source']}]")
            print(f"      {r['url']}")
    print(f"\nFull list -> {os.path.basename(ALL_CSV)}   New only -> {os.path.basename(NEW_CSV)}")


if __name__ == "__main__":
    main()
