#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(".")
OUT = Path("analysis")
OUT.mkdir(exist_ok=True)

CHANNEL_FILES = [
    p for p in ROOT.glob("*.txt")
    if p.name.startswith("Playdead Unofficial - ")
]

TEXT_ASSET_SUFFIXES = {".txt", ".html", ".htm", ".js", ".py", ".json", ".csv", ".md"}
TEXT_ASSET_MAX_BYTES = 12 * 1024 * 1024

KEYWORD_GROUPS = {
    "sticker_core": [
        r"sticker", r"collector'?s edition", r"collector edition", r"iam8bit",
        r"108", r"81\s*\+\s*27", r"12\s*[x×]\s*9", r"9\s*[x×]\s*12",
        r"3\s*[x×]\s*3", r"foreground", r"background",
    ],
    "registration_geometry": [
        r"align", r"alignment", r"register", r"registration", r"margin",
        r"row order", r"column order", r"rearrang", r"rotate", r"mirror",
        r"shift", r"transpose", r"interlac", r"edge pixel", r"side pixel",
        r"acorn", r"grid", r"matrix",
    ],
    "symbols_codes": [
        r"morse", r"braille", r"slash", r"dash", r"dot", r"binary",
        r"ternary", r"base ?3", r"one[- ]hot", r"barcode", r"qr",
    ],
    "external_consumers": [
        r"terminal ?41", r"gateway", r"printer", r"print/index\.php",
        r"fsd5t355gf", r"breach_contribution_reg", r"gate/81",
        r"endpoint", r"url", r"api", r"submit", r"input", r"auth",
    ],
    "physical_material": [
        r"cover", r"sleeve", r"poster", r"envelope", r"uv", r"blacklight",
        r"ultraviolet", r"packag", r"box", r"insert", r"label", r"print",
        r"sculpture", r"huddle",
    ],
    "period_prediction": [
        r"period", r"repeat", r"cycle", r"sequence", r"probab",
        r"prediction", r"predict", r"confidence", r"missing",
    ],
    "historical_paths": [
        r"534brn", r"transmission", r"shutdown", r"probe", r"planet",
        r"supersecret", r"rorschach", r"facility 89", r"schematic",
    ],
}

COMPILED = {
    group: [re.compile(pat, re.I) for pat in pats]
    for group, pats in KEYWORD_GROUPS.items()
}

URL_RE = re.compile(r"https?://[^\s<>\]\)\}\"']+")
STICKER_NUM_RE = re.compile(
    r"(?i)(?:sticker\s*(?:#|no\.?\s*)?|[#№]|[•/\-]\s*)(\d{1,3})\b"
)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_lines(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            yield n, line.rstrip("\n")

hit_rows = []
url_rows = []
sticker_refs = Counter()
channel_stats = {}
domain_counts = Counter()
group_counts = Counter()
asset_names = []
asset_content_hits = []

for path in sorted(CHANNEL_FILES):
    line_count = 0
    matched_lines = 0
    local_groups = Counter()
    prev = []
    for n, line in read_lines(path):
        line_count = n
        groups = []
        for group, patterns in COMPILED.items():
            if any(p.search(line) for p in patterns):
                groups.append(group)
                local_groups[group] += 1
                group_counts[group] += 1
        if groups:
            matched_lines += 1
            context = " | ".join((prev[-2:] + [line])[-3:])
            hit_rows.append({
                "file": path.name,
                "line": n,
                "groups": ",".join(groups),
                "text": line[:1000],
                "context": context[:2400],
            })
        for url in URL_RE.findall(line):
            url = url.rstrip(".,;:!?")
            host = urlparse(url).netloc.lower()
            domain_counts[host] += 1
            url_rows.append({
                "file": path.name,
                "line": n,
                "domain": host,
                "url": url[:2000],
            })
        for m in STICKER_NUM_RE.finditer(line):
            num = int(m.group(1))
            if 0 <= num <= 999:
                sticker_refs[num] += 1
        prev.append(line[:1200])
        if len(prev) > 2:
            prev.pop(0)
    channel_stats[path.name] = {
        "bytes": path.stat().st_size,
        "lines": line_count,
        "matched_lines": matched_lines,
        "group_counts": dict(local_groups),
        "sha256": sha256(path),
    }

for p in sorted(Path("assets").rglob("*")):
    if not p.is_file():
        continue
    name = p.name.lower()
    matched = []
    for group, patterns in COMPILED.items():
        if any(pt.search(name) for pt in patterns):
            matched.append(group)
    if matched:
        asset_names.append({
            "path": str(p),
            "bytes": p.stat().st_size,
            "groups": ",".join(matched),
            "sha256": sha256(p),
        })

    if p.suffix.lower() in TEXT_ASSET_SUFFIXES and p.stat().st_size <= TEXT_ASSET_MAX_BYTES:
        prev = []
        for n, line in read_lines(p):
            groups = []
            for group, patterns in COMPILED.items():
                if any(pt.search(line) for pt in patterns):
                    groups.append(group)
            if groups:
                context = " | ".join((prev[-2:] + [line])[-3:])
                asset_content_hits.append({
                    "path": str(p),
                    "line": n,
                    "groups": ",".join(groups),
                    "text": line[:1000],
                    "context": context[:2400],
                })
            for url in URL_RE.findall(line):
                url = url.rstrip(".,;:!?")
                host = urlparse(url).netloc.lower()
                domain_counts[host] += 1
                url_rows.append({
                    "file": str(p),
                    "line": n,
                    "domain": host,
                    "url": url[:2000],
                })
            prev.append(line[:1200])
            if len(prev) > 2:
                prev.pop(0)

url_counter = Counter(r["url"] for r in url_rows)
first_url = {}
for r in url_rows:
    first_url.setdefault(r["url"], r)

with (OUT / "keyword-hits.tsv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["file","line","groups","text","context"], delimiter="\t")
    w.writeheader()
    w.writerows(hit_rows)

with (OUT / "url-inventory.tsv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(["count","domain","first_file","first_line","url"])
    for url, count in url_counter.most_common():
        r = first_url[url]
        w.writerow([count, r["domain"], r["file"], r["line"], url])

with (OUT / "asset-inventory.tsv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["path","bytes","groups","sha256"], delimiter="\t")
    w.writeheader()
    w.writerows(asset_names)

with (OUT / "asset-content-hits.tsv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["path","line","groups","text","context"], delimiter="\t")
    w.writeheader()
    w.writerows(asset_content_hits)

summary = {
    "schema_version": 1,
    "channel_stats": channel_stats,
    "keyword_group_counts": dict(group_counts),
    "top_domains": domain_counts.most_common(100),
    "sticker_number_reference_counts": sticker_refs.most_common(),
    "keyword_hit_rows": len(hit_rows),
    "unique_urls": len(url_counter),
    "interesting_assets": len(asset_names),
    "asset_content_hit_rows": len(asset_content_hits),
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

md = [
    "# Playdead Unofficial export mining summary",
    "",
    "Generated reproducibly by tools/mine_exports.py.",
    "",
    "## Channel corpus",
    "",
]
for name, stats in channel_stats.items():
    md.append(
        f"- {name}: {stats['bytes']:,} bytes, {stats['lines']:,} lines, "
        f"{stats['matched_lines']:,} keyword-hit lines."
    )
md += ["", "## Keyword groups", ""]
for group, count in group_counts.most_common():
    md.append(f"- {group}: {count:,} matching lines")
md += ["", "## Most-referenced sticker numbers", ""]
for num, count in sticker_refs.most_common(60):
    md.append(f"- {num}: {count} references")
md += ["", "## Top URL domains", ""]
for host, count in domain_counts.most_common(40):
    md.append(f"- {host or '(none)'}: {count}")
md += [
    "",
    "## Generated indexes",
    "",
    "- keyword-hits.tsv preserves matched line text plus up to two preceding lines as compact context.",
    "- url-inventory.tsv deduplicates URLs while preserving the first source location and occurrence count.",
    "- asset-inventory.tsv inventories clue-relevant asset filenames with SHA-256 hashes.",
    "- asset-content-hits.tsv searches the contents of text-like archived assets (HTML/TXT/JS/PY/JSON/CSV/MD) up to 12 MiB each.",
    "- summary.json contains machine-readable counts.",
    "",
    "These files are discovery indexes, not evidence conclusions. Re-check any promoted claim against its source export/asset.",
]
(OUT / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
