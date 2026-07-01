#!/usr/bin/env python3
"""
find_jobs_employers.py  --  targeted searches for specific local employers

WHY THIS EXISTS
---------------
The big Las Vegas employers (casinos, Switch, airlines) don't offer clean job
feeds -- they post through Workday, which isn't easily searchable. But Adzuna
DOES index their postings. So for each employer we:
  1. search Adzuna for the employer's name (near Las Vegas), then
  2. keep ONLY jobs whose company name really matches that employer
     (this throws out noise -- e.g. searching "Caesars" also returns
      "Little Caesars", which we drop), and
  3. keep only IT / networking / security roles (same relevance filter).

Matched jobs get tagged so the website and email can highlight them with a star.

TO ADD AN EMPLOYER: copy a line below. "search" is what we type into Adzuna;
"match" is the list of text that must appear in the company name to count.
"""

# We reuse the Adzuna search + filters we already wrote.
from find_jobs_adzuna import search, is_relevant, is_too_senior, in_southern_nevada

# name    = how it's shown to students
# search  = the phrase sent to Adzuna
# match   = company-name text that confirms it's really this employer
LOCAL_EMPLOYERS = [
    {"name": "MGM Resorts",       "search": "MGM Resorts",         "match": ["mgm resorts"]},
    {"name": "Caesars Entertainment", "search": "Caesars Entertainment", "match": ["caesars entertainment"]},
    {"name": "Boyd Gaming",       "search": "Boyd Gaming",         "match": ["boyd gaming"]},
    {"name": "Station Casinos",   "search": "Station Casinos",     "match": ["station casinos", "red rock resorts"]},
    {"name": "Light & Wonder",    "search": "Light and Wonder",    "match": ["light & wonder", "light and wonder"]},
    {"name": "Everi",             "search": "Everi Holdings",      "match": ["everi"]},
    {"name": "Aristocrat",        "search": "Aristocrat",          "match": ["aristocrat"]},
    {"name": "Allegiant Air",     "search": "Allegiant",           "match": ["allegiant"]},
    {"name": "Cox Communications","search": "Cox Communications",  "match": ["cox communications"]},
    {"name": "Switch",            "search": "Switch datacenter",   "match": ["switch, ltd", "switch inc", "switch data"]},
    {"name": "Zappos",            "search": "Zappos",              "match": ["zappos"]},
    {"name": "UNLV",              "search": "University of Nevada Las Vegas", "match": ["university of nevada"]},
    {"name": "Clark County",      "search": "Clark County Nevada", "match": ["clark county"]},
    {"name": "City of Henderson", "search": "City of Henderson",   "match": ["city of henderson"]},
    {"name": "State of Nevada",   "search": "State of Nevada",     "match": ["state of nevada"]},
]


def match_employer(company):
    """Return the canonical employer name if this company is on our list, else ''."""
    low = (company or "").lower()
    for emp in LOCAL_EMPLOYERS:
        if any(m in low for m in emp["match"]):
            return emp["name"]
    return ""


def collect_jobs():
    """Search each employer, keep genuine + relevant matches. Returns job dicts."""
    seen = set()
    kept = []

    for emp in LOCAL_EMPLOYERS:
        try:
            data = search(emp["search"], 1)   # one page per employer is plenty
        except Exception as e:
            print(f"  ! employer search '{emp['name']}' failed: {e}")
            continue

        for job in data.get("results", []):
            company = job.get("company", {}).get("display_name", "")
            # Must actually be this employer.
            if not any(m in company.lower() for m in emp["match"]):
                continue

            title = job.get("title", "")
            if not is_relevant(title) or is_too_senior(title):
                continue

            location = job.get("location", {}).get("display_name", "")
            if not in_southern_nevada(location):
                continue

            link = job.get("redirect_url", "")
            if link in seen:
                continue
            seen.add(link)

            kept.append({
                "title": title,
                "company": company,
                "location": location,
                "posted": job.get("created", "")[:10],
                "employer": emp["name"],
                "description": job.get("description", ""),
                "url": link,
            })

    return kept


if __name__ == "__main__":
    jobs = collect_jobs()
    print(f"Found {len(jobs)} jobs at watched local employers:\n")
    for j in jobs:
        print(f"- {j['title']} @ {j['company']} ({j['location']})  [{j['employer']}]")
