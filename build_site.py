#!/usr/bin/env python3
"""
build_site.py  --  turns the job list into a filterable web page (index.html)

The page is ONE self-contained file: the job data is baked right into it, and
all the filtering happens in the visitor's browser. That means:
  - no server, no database, nothing to maintain
  - it can't take submissions or be hacked (it's just a static page)
  - you can host it anywhere (GitHub Pages, Netlify, a school server, etc.)

It reads all_jobs.csv (written by update_jobs.py) and writes index.html.
Run standalone with:   python3 build_site.py
Or it's called automatically at the end of update_jobs.py.
"""

import csv
import html
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ALL_CSV = os.path.join(HERE, "all_jobs.csv")
SITE_HTML = os.path.join(HERE, "index.html")

# Each job is sorted into ONE bucket for the "job type" filter, by scanning its
# title top-to-bottom. First match wins, so order matters (specific -> general).
CATEGORIES = [
    ("Cybersecurity", ["cyber", "infosec", "information security", "soc", "cmmc",
                        "isso", "penetration", "firewall", "security analyst",
                        "security specialist", "security officer", "security"]),
    ("Networking",    ["network", "noc"]),
    ("Help Desk / Support", ["help desk", "helpdesk", "desktop support", "support"]),
    ("Systems / SysAdmin",  ["system administrator", "systems administrator",
                             "sysadmin", "systems engineer", "systems"]),
    ("Cloud",         ["cloud"]),
    ("IT (General)",  ["it ", "information technology", "computer", "technician"]),
]


def categorize(title):
    low = title.lower()
    for name, words in CATEGORIES:
        if any(w in low for w in words):
            return name
    return "Other"


def load_jobs():
    if not os.path.exists(ALL_CSV):
        return []
    with open(ALL_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["type"] = categorize(r.get("title", ""))
    return rows


def build(rows=None):
    """Build index.html from the given rows (or from all_jobs.csv if None)."""
    if rows is None:
        rows = load_jobs()
    else:
        # rows came from update_jobs.py -- add the type field.
        rows = [{**r, "type": categorize(r.get("title", ""))} for r in rows]

    today = datetime.now().strftime("%Y-%m-%d")
    types = sorted({r["type"] for r in rows})
    # Count how many jobs are new today (first_seen == today).
    new_count = sum(1 for r in rows if r.get("first_seen") == today)

    # The job data, embedded as JSON the page's JavaScript will read.
    data_json = json.dumps(rows, ensure_ascii=False)

    page = TEMPLATE.format(
        updated=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        total=len(rows),
        new_count=new_count,
        today=today,
        type_buttons="".join(
            f'<button class="chip" data-type="{html.escape(t)}">{html.escape(t)}</button>'
            for t in types
        ),
        data_json=data_json,
    )
    with open(SITE_HTML, "w", encoding="utf-8") as f:
        f.write(page)
    return SITE_HTML


# ---------------------------------------------------------------------------
# The HTML template. {curly} placeholders get filled in by build().
# JavaScript braces are doubled ({{ }}) so Python's .format() leaves them alone.
# ---------------------------------------------------------------------------
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Professor Scheuerman's Job Hub</title>
<style>
  :root {{ --bg:#0f172a; --card:#1e293b; --line:#334155; --text:#e2e8f0;
           --muted:#94a3b8; --accent:#38bdf8; --new:#22c55e; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,Segoe UI,Roboto,sans-serif;
          background:var(--bg); color:var(--text); }}
  header {{ padding:28px 20px 14px; text-align:center; }}
  h1 {{ margin:0 0 6px; font-size:1.6rem; }}
  .sub {{ color:var(--muted); font-size:.9rem; }}
  .wrap {{ max-width:900px; margin:0 auto; padding:0 16px 60px; }}
  .controls {{ position:sticky; top:0; background:var(--bg); padding:14px 0;
               border-bottom:1px solid var(--line); z-index:5; }}
  #search {{ width:100%; padding:11px 14px; font-size:1rem; border-radius:10px;
             border:1px solid var(--line); background:var(--card); color:var(--text); }}
  .chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
  .chip {{ padding:7px 13px; border-radius:999px; border:1px solid var(--line);
           background:var(--card); color:var(--text); cursor:pointer; font-size:.85rem; }}
  .chip.active {{ background:var(--accent); color:#08131f; border-color:var(--accent);
                  font-weight:600; }}
  .count {{ color:var(--muted); font-size:.85rem; margin:14px 2px 6px; }}
  .job {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
          padding:15px 17px; margin-bottom:11px; }}
  .job h3 {{ margin:0 0 5px; font-size:1.06rem; }}
  .job h3 a {{ color:var(--accent); text-decoration:none; }}
  .job h3 a:hover {{ text-decoration:underline; }}
  .meta {{ color:var(--muted); font-size:.88rem; }}
  .tag {{ display:inline-block; font-size:.72rem; padding:2px 8px; border-radius:6px;
          background:#0b2a3a; color:var(--accent); margin-right:6px; }}
  .badge-new {{ background:var(--new); color:#052e16; font-weight:700; }}
  .badge-emp {{ background:#3b2f0b; color:#fbbf24; font-weight:600; }}
  .badge-intern {{ background:#2e1065; color:#c4b5fd; font-weight:600; }}
  .badge-entry {{ background:#0b3b2f; color:#34d399; font-weight:600; }}
  .empty {{ text-align:center; color:var(--muted); padding:40px; }}
  footer {{ text-align:center; color:var(--muted); font-size:.8rem; padding:20px; }}
</style>
</head>
<body>
<header>
  <h1>Professor Scheuerman's Job Hub</h1>
  <div class="sub">Las Vegas / Henderson networking &amp; cybersecurity roles for students &middot;
    {total} openings &middot; {new_count} new today &middot; updated {updated}</div>
</header>
<div class="wrap">
  <div class="controls">
    <input id="search" type="search" placeholder="Search title, company, or location...">
    <div class="chips">
      <button class="chip active" data-type="All">All</button>
      <button class="chip" data-type="__NEW__">New today</button>
      <button class="chip" data-type="__INTERN__">Internships</button>
      <button class="chip" data-type="__ENTRY__">No experience needed</button>
      <button class="chip" data-type="__EMPLOYER__">&#9733; Local employers</button>
      {type_buttons}
    </div>
  </div>
  <div class="count" id="count"></div>
  <div id="list"></div>
</div>
<footer>Read-only listing &middot; auto-updated daily &middot; source: Adzuna &amp; The Muse</footer>

<script>
  const JOBS = {data_json};
  const TODAY = "{today}";
  let activeType = "All";

  const list = document.getElementById("list");
  const countEl = document.getElementById("count");
  const search = document.getElementById("search");

  function esc(s) {{
    return (s || "").replace(/[&<>"]/g, c =>
      ({{ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;" }}[c]));
  }}

  function render() {{
    const q = search.value.trim().toLowerCase();
    const shown = JOBS.filter(j => {{
      if (activeType === "__NEW__") {{ if (j.first_seen !== TODAY) return false; }}
      else if (activeType === "__INTERN__") {{ if (j.internship !== "yes") return false; }}
      else if (activeType === "__ENTRY__") {{ if (j.entry_level !== "yes") return false; }}
      else if (activeType === "__EMPLOYER__") {{ if (!j.employer) return false; }}
      else if (activeType !== "All") {{ if (j.type !== activeType) return false; }}
      if (q) {{
        const hay = (j.title + " " + j.company + " " + j.location).toLowerCase();
        if (!hay.includes(q)) return false;
      }}
      return true;
    }});

    countEl.textContent = shown.length + " job" + (shown.length === 1 ? "" : "s") + " shown";
    if (!shown.length) {{ list.innerHTML = '<div class="empty">No jobs match your filters.</div>'; return; }}

    list.innerHTML = shown.map(j => {{
      const isNew = j.first_seen === TODAY;
      const posted = j.posted ? " &middot; posted " + esc(j.posted) : "";
      return `<div class="job">
        <h3><a href="${{esc(j.url)}}" target="_blank" rel="noopener">${{esc(j.title)}}</a></h3>
        <div class="meta">
          <span class="tag">${{esc(j.type)}}</span>
          ${{isNew ? '<span class="tag badge-new">NEW</span>' : ''}}
          ${{j.employer ? '<span class="tag badge-emp">&#9733; ' + esc(j.employer) + '</span>' : ''}}
          ${{j.internship === "yes" ? '<span class="tag badge-intern">Internship</span>' : ''}}
          ${{j.entry_level === "yes" ? '<span class="tag badge-entry">No exp needed</span>' : ''}}
          ${{esc(j.company)}} &middot; ${{esc(j.location)}}${{posted}}
        </div>
      </div>`;
    }}).join("");
  }}

  document.querySelectorAll(".chip").forEach(chip => {{
    chip.addEventListener("click", () => {{
      document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      activeType = chip.dataset.type;
      render();
    }});
  }});
  search.addEventListener("input", render);
  render();
</script>
</body>
</html>"""


if __name__ == "__main__":
    path = build()
    print(f"Built {path}")
