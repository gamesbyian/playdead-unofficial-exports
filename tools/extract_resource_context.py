#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("analysis/resource-context.tsv")
OUT.parent.mkdir(exist_ok=True)

TARGET_DOMAINS = {
    "docs.google.com", "drive.google.com", "github.com", "gist.github.com",
    "web.archive.org", "archive.org", "terminal41.link", "www.terminal41.link",
    "playdead.com", "www.playdead.com", "iam8bit.com", "www.iam8bit.com",
    "store.iam8bit.com", "wiki.gamedetectives.net", "steamcommunity.com",
    "imgur.com", "i.imgur.com", "pastebin.com",
}

URL_RE = re.compile(r"https?://[^\s<>\]\)\}\"']+")

channel_files = sorted(
    p for p in Path(".").glob("*.txt")
    if p.name.startswith("Playdead Unofficial - ")
)

rows = []
for path in channel_files:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        urls = []
        for raw in URL_RE.findall(line):
            url = raw.rstrip(".,;:!?")
            host = urlparse(url).netloc.lower()
            if host in TARGET_DOMAINS:
                urls.append((url, host))
        if not urls:
            continue
        before = lines[max(0, i-2):i]
        after = lines[i+1:i+3]
        context = " | ".join(before + [line] + after)
        for url, host in urls:
            rows.append({
                "file": path.name,
                "line": i + 1,
                "domain": host,
                "url": url,
                "context": context[:6000],
            })

with OUT.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(
        fh,
        fieldnames=["file", "line", "domain", "url", "context"],
        delimiter="\t",
    )
    w.writeheader()
    w.writerows(rows)

print(f"wrote {OUT} with {len(rows)} resource URL occurrences")
