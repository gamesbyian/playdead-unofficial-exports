#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path

A = Path("analysis")

SELECTED_RESOURCE_DOMAINS = {
    "github.com", "gist.github.com", "docs.google.com", "drive.google.com",
    "pastebin.com", "web.archive.org", "archive.org", "imgur.com", "i.imgur.com",
    "wiki.gamedetectives.net", "steamcommunity.com", "terminal41.link",
    "www.terminal41.link", "playdead.com", "www.playdead.com",
    "www.iam8bit.com", "store.iam8bit.com",
}

SERIAL_PATTERNS = [
    re.compile(r"(?i)\bsticker(?:\s*(?:#|no\.?|number|num\.?)?)?\s*[/•\-]?\s*(\d{3})\b"),
    re.compile(r"(?<!\w)([/•])\s*(\d{3})\b"),
]

REG_RE = re.compile(
    r"(?i)(?:"
    r"81\s*\+\s*27|"
    r"(?:9\s*[x×]\s*12|12\s*[x×]\s*9)|"
    r"(?:twelve|12)\s+(?:3\s*[x×]\s*3|3x3)|"
    r"(?:nine|9)\s+.*?(?:3\s*[x×]\s*3|3x3)|"
    r"margin|check[- ]?bits?|side pixels?|edge pixels?|"
    r"row order|column order|registration|register(?:ed|ing)?|"
    r"interlac(?:e|ed|ing)|rearrang(?:e|ed|ement|ing)|"
    r"transpose|phase zero|zero phase"
    r")"
)

def read_tsv(path):
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        yield from csv.DictReader(fh, delimiter="\t")

# Exact-ish sticker serial references.
serial_rows = []
seen = set()
for row in read_tsv(A / "keyword-hits.tsv"):
    text = row.get("text", "")
    context = row.get("context", "")
    combined = text + " " + context
    found = set()
    for pat in SERIAL_PATTERNS:
        for m in pat.finditer(combined):
            raw = m.groups()[-1]
            n = int(raw)
            if 50 <= n <= 699:
                found.add(n)
    if not found:
        continue
    for n in sorted(found):
        key = (row["file"], row["line"], n)
        if key in seen:
            continue
        seen.add(key)
        serial_rows.append({
            "serial": n,
            "file": row["file"],
            "line": row["line"],
            "groups": row["groups"],
            "text": text,
            "context": context,
        })

with (A / "sticker-serial-leads.tsv").open("w", encoding="utf-8", newline="") as fh:
    fields = ["serial","file","line","groups","text","context"]
    w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
    w.writeheader()
    w.writerows(sorted(serial_rows, key=lambda r: (int(r["serial"]), r["file"], int(r["line"]))))

# Registration / geometry passages.
reg_rows = []
seen = set()
for row in read_tsv(A / "keyword-hits.tsv"):
    combined = row.get("text","") + " " + row.get("context","")
    if not REG_RE.search(combined):
        continue
    key = (row["file"], row["line"])
    if key in seen:
        continue
    seen.add(key)
    reg_rows.append(row)

with (A / "registration-leads.tsv").open("w", encoding="utf-8", newline="") as fh:
    fields = ["file","line","groups","text","context"]
    w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
    w.writeheader()
    w.writerows(reg_rows)

# External resources: select research/document/code/archive domains from the full URL ledger.
resource_rows = []
for row in read_tsv(A / "url-inventory.tsv"):
    if row.get("domain","").lower() in SELECTED_RESOURCE_DOMAINS:
        resource_rows.append(row)

with (A / "external-resource-leads.tsv").open("w", encoding="utf-8", newline="") as fh:
    fields = ["count","domain","first_file","first_line","url"]
    w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
    w.writeheader()
    w.writerows(resource_rows)

summary = [
    "# Targeted extraction summary",
    "",
    f"- exact-ish sticker serial source rows: {len(serial_rows)}",
    f"- registration/geometry source rows: {len(reg_rows)}",
    f"- selected external research/resource URLs: {len(resource_rows)}",
    "",
    "These are discovery ledgers. Every promoted claim still needs source-level verification.",
]
(A / "targeted-leads.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
print("\n".join(summary))
