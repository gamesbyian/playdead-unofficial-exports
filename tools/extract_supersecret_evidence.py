#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, wave
from pathlib import Path

CHANNEL=Path("Playdead Unofficial - ARG - solving-breakout [463106924708233216].txt")
OUT=Path("analysis/supersecret")
OUT.mkdir(parents=True, exist_ok=True)

lines=CHANNEL.read_text(encoding="utf-8",errors="replace").splitlines()
# Window containing discovery, attempted decoding, claimed solve, and day-1 provenance.
lo,hi=10820,11480
window=lines[lo-1:hi]
(OUT/"discussion-window.txt").write_text(
    "\n".join(f"{i}: {line}" for i,line in enumerate(window,start=lo))+"\n",
    encoding="utf-8"
)

asset_re=re.compile(r"assets\\([^\s|]+)")
names=[]
for line in window:
    names.extend(asset_re.findall(line))
names=sorted(set(names))

# Build basename->paths map because exported attachment names are content-hash suffixed.
assets=list(Path("assets").iterdir())
by_name={p.name:p for p in assets if p.is_file()}
records=[]
for name in names:
    p=by_name.get(name)
    if not p:
        records.append({"referenced_name":name,"status":"missing"})
        continue
    b=p.read_bytes()
    rec={"referenced_name":name,"path":str(p),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
    if b.startswith(b"\x89PNG\r\n\x1a\n") and len(b)>=24:
        rec["format"]="png"
        rec["width"]=int.from_bytes(b[16:20],"big")
        rec["height"]=int.from_bytes(b[20:24],"big")
    elif b.startswith(b"RIFF") and b[8:12]==b"WAVE":
        rec["format"]="wav"
        try:
            with wave.open(str(p),"rb") as w:
                rec["channels"]=w.getnchannels()
                rec["sample_width"]=w.getsampwidth()
                rec["sample_rate"]=w.getframerate()
                rec["frames"]=w.getnframes()
                rec["duration_s"]=w.getnframes()/w.getframerate()
        except Exception as e:
            rec["wave_error"]=repr(e)
    records.append(rec)

(OUT/"attachment-manifest.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")

# Search the entire assets directory for exact duplicates of the superSecret WAV.
target=Path("assets/image_Game26585_681347534-0ccc807a7c7b0a55.wav")
if target.exists():
    h=hashlib.sha256(target.read_bytes()).hexdigest()
    dup=[]
    for p in assets:
        if p.is_file() and p.stat().st_size==target.stat().st_size:
            if hashlib.sha256(p.read_bytes()).hexdigest()==h:
                dup.append(str(p))
    (OUT/"wav-duplicates.json").write_text(json.dumps({"sha256":h,"paths":dup},indent=2)+"\n",encoding="utf-8")

print(f"window lines {lo}-{hi}; {len(records)} referenced assets")
