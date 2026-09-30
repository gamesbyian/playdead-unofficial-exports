#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path

terms=[
    "super_secret","super_secret_stop","2591595269","913695112",
    "681347534","image.wav","superSecret","Game2#6585"
]
suffixes={".txt",".xml",".json",".cs",".js",".py",".html",".htm",".md",".csv"}
roots=[Path("."),Path("assets")]
records=[]
seen=set()
for root in roots:
    paths=(root.rglob("*") if root!=Path(".") else root.glob("*.txt"))
    for p in paths:
        if not p.is_file() or p.suffix.lower() not in suffixes or p.stat().st_size>15*1024*1024:
            continue
        key=str(p)
        if key in seen: continue
        seen.add(key)
        try: txt=p.read_text(encoding="utf-8",errors="replace")
        except Exception: continue
        for term in terms:
            start=0
            while True:
                i=txt.find(term,start)
                if i<0: break
                line=txt.count("\n",0,i)+1
                records.append({
                    "path":key,"line":line,"term":term,
                    "context":txt[max(0,i-1200):min(len(txt),i+2400)]
                })
                start=i+len(term)
                if sum(1 for r in records if r["path"]==key and r["term"]==term)>=100: break
Path("analysis/supersecret/exact-reference-hits.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")
print(f"{len(records)} exact-reference hits")
for r in records[:100]:
    print(r["path"],r["line"],r["term"])
