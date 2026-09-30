#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path

OUT = Path("analysis/clue-context.tsv")
OUT.parent.mkdir(exist_ok=True)

PATTERNS = {
    "supersecret": re.compile(r"super\s*secret|supersecret", re.I),
    "game2_6585": re.compile(r"Game2#6585|681347534", re.I),
    "secret_probe_flicker": re.compile(r"Secret\s*ProbeFlicker|ProbeFlicker", re.I),
    "image_audio": re.compile(r"\bimage\b.*(?:audio|wav|sound)|(?:audio|wav|sound).*\bimage\b", re.I),
    "input_22": re.compile(r"\binput\s*22\b", re.I),
    "morse_terminal": re.compile(r"morse\s+terminal|terminal\s+morse", re.I),
    "sticker_597": re.compile(r"(?:sticker\s*)?(?:[/•.\-]\s*)?597\b", re.I),
    "sticker_306": re.compile(r"(?:sticker\s*)?(?:[/•.\-]\s*)?306\b", re.I),
}

channel_files = sorted(
    p for p in Path(".").glob("*.txt")
    if p.name.startswith("Playdead Unofficial - ")
)

rows = []
for path in channel_files:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        matched = [name for name, pat in PATTERNS.items() if pat.search(line)]
        if not matched:
            continue
        lo=max(0,i-6); hi=min(len(lines),i+7)
        context=" | ".join(lines[lo:hi])
        rows.append({
            "file": path.name,
            "line": i+1,
            "patterns": ",".join(matched),
            "text": line[:2000],
            "context": context[:12000],
        })

with OUT.open("w", encoding="utf-8", newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["file","line","patterns","text","context"],delimiter="\t")
    w.writeheader()
    w.writerows(rows)

print(f"wrote {OUT} with {len(rows)} clue-context rows")
