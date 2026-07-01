#!/usr/bin/env python3
"""
find_jobs_adzuna.py  --  Local Vegas/Henderson cyber + networking jobs (Adzuna)

WHY ADZUNA?
-----------
Adzuna is a job-search aggregator with a FREE developer API. Unlike The Muse,
it's built for local searching: you can say "IT jobs within 25 km of Las Vegas,
sorted by newest, entry-level only." That's exactly what students need.

ONE-TIME SETUP (about 60 seconds, free)
---------------------------------------
1. Go to:  https://developer.adzuna.com/signup
2. Confirm your email, then open your dashboard to see two values:
       - Application ID   (app_id)
       - Application Key  (app_key)
3. Open the file  config.py  (in this folder) and paste them in.

Then run:
    python3 find_jobs_adzuna.py
"""

import csv
import json
import urllib.parse
import urllib.request

# We keep the secret keys in a separate config.py file so you never paste them
# into the main code (and so you don't accidentally share them).
try:
    from config import ADZUNA_APP_ID, ADZUNA_APP_KEY
except ImportError:
    ADZUNA_APP_ID = ADZUNA_APP_KEY = ""


# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------

COUNTRY = "us"
WHERE = "Las Vegas, Nevada"     # center point of the search
DISTANCE_KM = 160               # wide enough to cover all of Southern Nevada
                                # (Boulder City, Mesquite, Pahrump, Laughlin...).
                                # A location filter below keeps out AZ/CA towns.
RESULTS_PER_PAGE = 50
MAX_PAGES = 3

# Adzuna lets us search several phrases. We run one search per phrase and merge.
SEARCH_TERMS = [
    "cybersecurity",
    "network technician",
    "information security",
    "SOC analyst",
    "IT support",
    "help desk",
    "network administrator",
    # Internship-focused searches (surface student intern roles specifically).
    "cybersecurity intern",
    "IT intern",
    "network intern",
    "information technology intern",
    "help desk intern",
    # Entry-level / no-experience searches (school-only roles for students).
    "entry level IT support",
    "IT trainee",
    "junior network",
    "help desk no experience",
]

# A job counts as "Southern Nevada" only if its location text contains one of
# these. Adzuna labels locations as "City, County County", so matching on the
# four Southern Nevada COUNTY names is the reliable way to include every SN city
# while excluding Arizona/California border towns (e.g. "..., Mohave County" AZ
# or "..., San Bernardino County" CA). ", nv" / "nevada" are safety fallbacks.
SOUTHERN_NEVADA = [
    "clark county", "nye county", "lincoln county", "esmeralda county",
    ", nv", "nevada",
]

# Words that suggest a role needs no experience beyond school. Matched against
# the job title + description snippet. Used only to TAG jobs, not to drop them.
ENTRY_LEVEL_SIGNALS = [
    "no experience", "no prior experience", "no experience necessary",
    "no experience required", "entry level", "entry-level", "will train",
    "we will train", "training provided", "on-the-job training", "on the job training",
    "recent graduate", "recent grad", "new graduate", "new grad",
    "students welcome", "currently enrolled", "pursuing a degree",
    "0-1 year", "0 to 1 year", "junior", "trainee", "apprentice", "intern",
]

# Drop obviously-too-senior roles (same idea as the Muse script).
SENIORITY_BLOCKLIST = [
    "senior", "sr.", "sr ", "staff", "principal", "lead", "manager", "mgr",
    "director", "head of", "vp", "vice president", "architect", "iii", "supervisor",
]

# PHYSICAL-security / guard roles match the word "security" but are NOT the
# cyber jobs we want. Drop any title containing one of these.
PHYSICAL_SECURITY = [
    "security officer", "security guard", "surveillance", "loss prevention",
    "patrol", "armed security", "unarmed security", "security ambassador",
    "security agent", "gaming agent", "dispatcher", "security intelligence",
    "security dispatch", "security supervisor", "security host",
]

# A returned job is KEPT only if its title contains one of these. This is the
# key fix: Adzuna's search is loose and returns tangential jobs (nurses, sales),
# so we double-check the title is genuinely IT / networking / security.
RELEVANT_KEYWORDS = [
    "network", "cyber", "security", "infosec", "information security",
    "soc analyst", "it support", "help desk", "helpdesk", "sysadmin",
    "system administrator", "systems administrator", "network administrator",
    "network engineer", "network technician", "it technician", "it specialist",
    "desktop support", "penetration", "firewall", "cloud engineer",
    "information technology", "computer", "cmmc", "it analyst",
    "security analyst", "systems engineer", "noc",
]

OUTPUT_CSV = "jobs_adzuna.csv"


# ---------------------------------------------------------------------------
# THE CODE
# ---------------------------------------------------------------------------

def search(term, page):
    """Run one Adzuna search for a term + page, return the parsed JSON."""
    base = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": term,
        "where": WHERE,
        "distance": DISTANCE_KM,
        "results_per_page": RESULTS_PER_PAGE,
        "sort_by": "date",         # newest first
        "max_days_old": 30,        # only jobs posted in the last month
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "student-job-finder"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def is_too_senior(title):
    low = title.lower()
    return any(word in low for word in SENIORITY_BLOCKLIST)


def is_relevant(title):
    """True only if the title is genuinely IT / networking / security."""
    low = title.lower()
    if any(bad in low for bad in PHYSICAL_SECURITY):
        return False                       # it's a guard job, not a cyber job
    return any(kw in low for kw in RELEVANT_KEYWORDS)


def in_southern_nevada(location):
    """True if the location text looks like a Southern Nevada city/county."""
    low = (location or "").lower()
    return any(place in low for place in SOUTHERN_NEVADA)


def is_entry_level(title, description=""):
    """True if title/description suggest no experience beyond school is needed."""
    text = f"{title} {description}".lower()
    return any(sig in text for sig in ENTRY_LEVEL_SIGNALS)


def collect_jobs():
    seen = set()
    kept = []

    for term in SEARCH_TERMS:
        for page in range(1, MAX_PAGES + 1):
            try:
                data = search(term, page)
            except Exception as e:
                print(f"  ! search '{term}' page {page} failed: {e}")
                break

            results = data.get("results", [])
            if not results:
                break

            for job in results:
                title = job.get("title", "")
                if not is_relevant(title):
                    continue
                if is_too_senior(title):
                    continue

                location = job.get("location", {}).get("display_name", "")
                if not in_southern_nevada(location):
                    continue                       # skip AZ/CA border towns

                link = job.get("redirect_url", "")
                if link in seen:
                    continue
                seen.add(link)

                kept.append({
                    "title": title,
                    "company": job.get("company", {}).get("display_name", ""),
                    "location": location,
                    "posted": job.get("created", "")[:10],   # just the date part
                    "matched_search": term,
                    "description": job.get("description", ""),
                    "url": link,
                })

    # Newest first across everything.
    kept.sort(key=lambda j: j["posted"], reverse=True)
    return kept


def save_csv(jobs, path):
    fields = ["title", "company", "location", "posted", "matched_search", "url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(jobs)


def main():
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("!! No Adzuna keys found.\n")
        print("   1. Sign up (free): https://developer.adzuna.com/signup")
        print("   2. Put your app_id and app_key into config.py")
        print("   3. Run this again.")
        return

    print(f"Searching Adzuna for IT jobs within {DISTANCE_KM} km of {WHERE}...\n")
    jobs = collect_jobs()

    if not jobs:
        print("No matching jobs found. Try widening DISTANCE_KM or SEARCH_TERMS.")
        return

    save_csv(jobs, OUTPUT_CSV)
    print(f"Found {len(jobs)} jobs. Saved to {OUTPUT_CSV}\n")
    for j in jobs[:20]:
        print(f"- [{j['posted']}] {j['title']} @ {j['company']} ({j['location']})")
        print(f"    {j['url']}")
    if len(jobs) > 20:
        print(f"\n...and {len(jobs) - 20} more in {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
