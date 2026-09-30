#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import xml.etree.ElementTree as ET

p=Path("assets/SoundbanksInfo-92ab41c6b5a14432.xml")
root=ET.parse(p).getroot()
target="681347534"

parents={child:parent for parent in root.iter() for child in parent}
target_el=None
for el in root.iter():
    if el.attrib.get("Id")==target:
        target_el=el
        break

def summarize(el):
    return {"tag":el.tag,"attrib":dict(el.attrib),"text":(el.text or "").strip()[:500]}

anc=[]
x=target_el
while x is not None:
    anc.append(summarize(x))
    x=parents.get(x)

# Find enclosing SoundBank and summarize its identity + event population.
bank=None
x=target_el
while x is not None:
    if x.tag.lower().endswith("soundbank"):
        bank=x; break
    x=parents.get(x)

bank_info=None
if bank is not None:
    all_events=[]
    for e in bank.iter():
        if e.tag.lower().endswith("event"):
            all_events.append({"Id":e.attrib.get("Id"),"Name":e.attrib.get("Name")})
    names=[]
    for e in bank.iter():
        if e.tag.lower().endswith("shortname") and (e.text or "").strip():
            names.append((e.text or "").strip())
    bank_info={
        "attrib":dict(bank.attrib),
        "short_names":names[:20],
        "event_count":len(all_events),
        "secret_events":[e for e in all_events if "secret" in (e.get("Name") or "").lower()],
        "sample_events":all_events[:40],
    }

# Global event/file-name census for secret/image terms.
secret_events=[]
image_events=[]
secret_files=[]
for e in root.iter():
    tag=e.tag.lower()
    if tag.endswith("event"):
        name=e.attrib.get("Name") or ""
        if "secret" in name.lower():
            secret_events.append({"Id":e.attrib.get("Id"),"Name":name})
        if "image" in name.lower():
            image_events.append({"Id":e.attrib.get("Id"),"Name":name})
    if tag.endswith("file"):
        # inspect child ShortName / Path
        vals=[]
        for ch in e:
            if ch.tag.lower().endswith(("shortname","path")) and ch.text:
                vals.append(ch.text.strip())
        joined=" | ".join(vals)
        if "secret" in joined.lower() or "image" in joined.lower():
            secret_files.append({"Id":e.attrib.get("Id"),"values":vals})

out={
    "target_id":target,
    "ancestor_chain":anc,
    "enclosing_bank":bank_info,
    "global_secret_events":secret_events,
    "global_image_events":image_events,
    "global_secret_or_image_files":secret_files,
}
Path("analysis/supersecret/soundbanks-structure.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps({
    "target_found":target_el is not None,
    "enclosing_bank":bank_info and bank_info.get("short_names"),
    "bank_event_count":bank_info and bank_info.get("event_count"),
    "bank_secret_events":bank_info and bank_info.get("secret_events"),
    "global_secret_event_count":len(secret_events),
    "global_image_event_count":len(image_events),
    "secret_or_image_file_count":len(secret_files),
},indent=2))
