#!/bin/bash
# publish.sh -- pushes the freshly-built index.html to GitHub so the live site
# updates. Called at the end of update_jobs.py.
#
# Uses FULL PATHS on purpose: the daily scheduler (launchd) runs with a minimal
# PATH that doesn't include git's usual location, so we spell everything out.

cd /Users/lorischeuerman/JobScraper || exit 1
GIT=/usr/bin/git

$GIT add index.html
# If nothing changed, don't make an empty commit.
if $GIT diff --cached --quiet; then
    echo "  (site unchanged -- nothing to publish)"
    exit 0
fi

$GIT commit -q -m "Update jobs $(/bin/date +%Y-%m-%d)"
if $GIT push -q origin main; then
    echo "  published updated site to GitHub Pages"
else
    echo "  ! git push failed (check network / token)"
    exit 1
fi
