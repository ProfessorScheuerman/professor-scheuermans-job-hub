# Professor Scheuerman's Job Hub

A daily-updated listing of **networking & cybersecurity jobs for students** in the
Las Vegas / Henderson, NV area.

🌐 **Live site:** https://professorscheuerman.github.io/professor-scheuermans-job-hub/

## How it works

Every morning an automated script:

1. Pulls local IT / networking / cybersecurity jobs from **Adzuna** and **The Muse**
2. Runs targeted searches for specific local employers (casinos, Switch, Cox, UNLV,
   Clark County, City of Henderson, and more)
3. Filters to student-appropriate roles (drops senior and physical-security jobs)
4. Flags **internships** and **local employers**
5. Rebuilds this filterable web page and emails a digest of anything new

The website takes no submissions — it's a read-only listing students can filter by
job type, internships, or employer.

## Files

| File | Purpose |
|------|---------|
| `index.html` | The public, filterable job page (this is what GitHub Pages serves) |
| `update_jobs.py` | The daily runner that ties everything together |
| `find_jobs_adzuna.py` / `find_jobs.py` | Job sources |
| `find_jobs_employers.py` | Targeted local-employer searches |
| `build_site.py` | Generates `index.html` |
| `notify_email.py` | Emails the daily digest |
| `config.example.py` | Template for your own API keys (real `config.py` is private) |

## Setup

Copy `config.example.py` to `config.py`, add a free
[Adzuna API key](https://developer.adzuna.com/signup), and run:

```bash
python3 update_jobs.py
```
