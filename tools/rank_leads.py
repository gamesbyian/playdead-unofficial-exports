#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import re
from pathlib import Path

ROOT = Path("analysis")
OUT = ROOT / "ranked-leads.md"

RARE = {
    "stickers-solving": 10,
    "sticker-hunting": 8,
    "collector's edition": 5,
    "collector edition": 5,
    "81+27": 9,
    "81 + 27": 9,
    "3x3": 5,
    "3 x 3": 5,
    "9x12": 6,
    "12x9": 6,
    "108": 3,
    "margin": 6,
    "check-bit": 8,
    "check bit": 8,
    "side pixel": 8,
    "edge pixel": 8,
    "reversible": 5,
    "hidden clue": 8,
    "534brn9653f9j8mmd": 9,
    "fsd5t355gf": 9,
    "gate/81": 9,
    "print/index.php": 10,
    "gateway auth": 9,
    "ford cipher": 6,
    "life detected": 5,
    "lifedetected": 5,
    "acorn": 4,
    "sticker solution": 7,
    "period": 2,
    "repeat": 2,
    "prediction": 3,
    "predict": 3,
    "confidence": 3,
    "unboxing": 4,
    "iam8bit": 3,
    "envelope": 4,
    "black wrapping": 6,
    "relief": 5,
    "emboss": 5,
    "uv": 3,
    "blacklight": 4,
    "registration": 5,
    "rearrang": 4,
    "transpose": 4,
    "row order": 7,
    "column order": 7,
    "phase": 3,
    "sticker 597": 9,
    "sticker 630": 9,
    "sticker 648": 9,
    "•427": 9,
    "•369": 9,
}

HIGH_NUM_RE = re.compile(r"\b(?:sticker\s*)?[#№]?\s*(\d{3})\b", re.I)

def score(row: dict[str, str]) -> int:
    text = (row.get("text","") + " " + row.get("context","")).lower()
    groups = {g for g in row.get("groups","").split(",") if g}
    s = max(0, len(groups) - 1) * 4
    if "sticker_core" in groups and "registration_geometry" in groups:
        s += 8
    if "sticker_core" in groups and "physical_material" in groups:
        s += 6
    if "sticker_core" in groups and "external_consumers" in groups:
        s += 7
    if "registration_geometry" in groups and "symbols_codes" in groups:
        s += 5
    if "external_consumers" in groups and "historical_paths" in groups:
        s += 5
    for term, weight in RARE.items():
        if term in text:
            s += weight
    for m in HIGH_NUM_RE.finditer(text):
        n = int(m.group(1))
        if 100 <= n <= 699:
            s += 2
    return s

def read_tsv(path: Path, kind: str):
    rows = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            row["_kind"] = kind
            row["_score"] = score(row)
            rows.append(row)
    return rows

rows = []
rows += read_tsv(ROOT / "keyword-hits.tsv", "chat")
rows += read_tsv(ROOT / "asset-content-hits.tsv", "asset")
rows.sort(key=lambda r: (-r["_score"], r.get("file", r.get("path","")), int(r.get("line") or 0)))

selected = []
seen = set()
per_source = {}
for row in rows:
    if row["_score"] < 10:
        continue
    text = re.sub(r"\s+", " ", row.get("text","")).strip()
    key = re.sub(r"\d{5,}", "<N>", text.lower())[:500]
    if key in seen:
        continue
    src = row.get("file") or row.get("path") or "?"
    if per_source.get(src, 0) >= 120:
        continue
    seen.add(key)
    per_source[src] = per_source.get(src, 0) + 1
    selected.append(row)
    if len(selected) >= 600:
        break

def esc(s: str) -> str:
    return html.escape(re.sub(r"\s+", " ", s).strip())

lines = [
    "# Ranked ARG export leads",
    "",
    "Generated from the full Discord-export mining indexes. Scores are triage only, not evidentiary weights.",
    "",
    f"Selected {len(selected)} high-signal rows from {len(rows)} indexed chat/asset hits.",
    "",
]

for i, row in enumerate(selected, 1):
    src = row.get("file") or row.get("path") or "?"
    line = row.get("line") or "?"
    lines += [
        f"## {i}. score {row['_score']} · {row['_kind']} · {src}:{line}",
        "",
        f"Groups: {row.get('groups','')}",
        "",
        esc(row.get("text",""))[:1800],
        "",
    ]
    context = esc(row.get("context",""))
    if context and context != esc(row.get("text","")):
        lines += ["Context:", "", context[:3200], ""]

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {OUT} with {len(selected)} rows")
