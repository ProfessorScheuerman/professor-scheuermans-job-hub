#!/usr/bin/env python3
"""
find_jobs.py  --  Las Vegas / Henderson cyber + networking job finder (starter)

WHAT THIS DOES
--------------
Pulls IT jobs from The Muse's FREE public API (no API key, no signup needed),
keeps only the ones that look like networking / cybersecurity roles in the
Las Vegas / Henderson area, and saves them to a CSV file you can open in Excel.

HOW TO RUN
----------
    python3 find_jobs.py

That's it. No installs required -- it only uses Python's built-in libraries.

WHY THE MUSE FIRST?
-------------------
Big boards (Indeed, LinkedIn) block scrapers and forbid it in their terms.
The Muse gives away its data through an official API, so this is 100% allowed
and won't get you blocked. Once this works, we'll add more sources.
"""

import csv
import json
import time
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# SETTINGS -- tweak these to change what we search for
# ---------------------------------------------------------------------------

# Cities to accept. The Muse tags jobs with "City, ST" strings.
LOCATIONS = ["Las Vegas, NV", "Henderson, NV"]

# Keywords that mark a job as networking / cybersecurity related.
# A job is kept if ANY of these appear in its title.
KEYWORDS = [
    "network", "cyber", "security", "soc", "information security",
    "infosec", "it support", "help desk", "helpdesk", "systems",
    "cloud", "penetration", "pen test", "firewall", "analyst",
]

# Job categories to ask The Muse for (their API groups jobs by category).
CATEGORIES = ["Computer and IT", "Cybersecurity", "Data and Analytics"]

# Words in a job title that mean "too senior for a student" -- we drop these.
SENIORITY_BLOCKLIST = [
    "senior", "sr.", "sr ", "staff", "principal", "lead", "manager",
    "director", "head of", "vp", "vice president", "architect", "iii", " iv",
]

# The API tags remote jobs with this location string -- we don't want those.
REMOTE_TAGS = ["flexible / remote", "remote"]

OUTPUT_CSV = "jobs.csv"       # where results get written
MAX_PAGES = 5                 # how many pages of results to pull per category


# ---------------------------------------------------------------------------
# THE CODE
# ---------------------------------------------------------------------------

def fetch_page(category, page):
    """Ask The Muse API for one page of jobs in a given category + our cities."""
    params = [("category", category), ("page", str(page))]
    for loc in LOCATIONS:
        params.append(("location", loc))
    url = "https://www.themuse.com/api/public/jobs?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={"User-Agent": "student-job-finder"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def title_matches(title):
    """True if the job title contains any of our keywords (case-insensitive)."""
    low = title.lower()
    return any(kw in low for kw in KEYWORDS)


def is_too_senior(title):
    """True if the title looks like a senior/management role students should skip."""
    low = title.lower()
    return any(word in low for word in SENIORITY_BLOCKLIST)


def is_really_local(job_locations):
    """
    True only if the job is ACTUALLY in one of our cities.
    The API's location filter is loose, so we double-check here and reject
    remote-only postings and jobs that merely list our city among many.
    """
    names = [loc.get("name", "").lower() for loc in job_locations]

    # Reject if the ONLY location tag is remote.
    real_places = [n for n in names if n not in REMOTE_TAGS]
    if not real_places:
        return False

    # Keep only if one of our target cities is explicitly listed.
    wanted = [c.lower() for c in LOCATIONS]
    return any(n in wanted for n in names)


def collect_jobs():
    """Loop over categories + pages, keep the jobs that match our filters."""
    seen_urls = set()   # used to skip duplicates
    kept = []

    for category in CATEGORIES:
        for page in range(MAX_PAGES):
            try:
                data = fetch_page(category, page)
            except Exception as e:
                print(f"  ! skipped {category} page {page}: {e}")
                break

            results = data.get("results", [])
            if not results:
                break  # no more pages in this category

            for job in results:
                title = job.get("name", "")
                if not title_matches(title):
                    continue
                if is_too_senior(title):
                    continue
                if not is_really_local(job.get("locations", [])):
                    continue

                # Build a readable location string from the API's list.
                locs = ", ".join(loc.get("name", "") for loc in job.get("locations", []))
                company = job.get("company", {}).get("name", "")
                link = job.get("refs", {}).get("landing_page", "")

                if link in seen_urls:
                    continue
                seen_urls.add(link)

                kept.append({
                    "title": title,
                    "company": company,
                    "location": locs,
                    "category": category,
                    "url": link,
                })

            time.sleep(0.5)  # be polite -- don't hammer the API

    return kept


def save_csv(jobs, path):
    """Write the jobs to a CSV file."""
    fields = ["title", "company", "location", "category", "url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(jobs)


def main():
    print("Searching The Muse for Las Vegas / Henderson IT jobs...\n")
    jobs = collect_jobs()

    if not jobs:
        print("No matching jobs found right now. Try loosening KEYWORDS or LOCATIONS.")
        return

    save_csv(jobs, OUTPUT_CSV)
    print(f"Found {len(jobs)} matching jobs. Saved to {OUTPUT_CSV}\n")

    # Print a quick preview to the screen.
    for j in jobs[:15]:
        print(f"- {j['title']}  @ {j['company']}  ({j['location']})")
        print(f"    {j['url']}")
    if len(jobs) > 15:
        print(f"\n...and {len(jobs) - 15} more in {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
