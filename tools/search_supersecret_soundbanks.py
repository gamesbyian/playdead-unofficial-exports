#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path

p=Path("assets/SoundbanksInfo-92ab41c6b5a14432.xml")
out=Path("analysis/supersecret/soundbanks-search.json")
terms=["681347534","6585","Game2#6585","superSecret","supersecret","SecretProbe","WristSecret"]
text=p.read_text(encoding="utf-8",errors="replace")
results={}
for term in terms:
    hits=[]
    start=0
    while True:
        i=text.find(term,start)
        if i<0: break
        hits.append({
            "offset":i,
            "context":text[max(0,i-1200):min(len(text),i+2600)]
        })
        start=i+len(term)
        if len(hits)>=100: break
    results[term]={"count":len(hits),"hits":hits}
out.write_text(json.dumps({"bytes":p.stat().st_size,"terms":results},indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v["count"] for k,v in results.items()},indent=2))
