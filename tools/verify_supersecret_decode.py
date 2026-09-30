#!/usr/bin/env python3
from __future__ import annotations
import json, wave
from pathlib import Path
import numpy as np
from PIL import Image

wav=Path("assets/image_Game26585_681347534-0ccc807a7c7b0a55.wav")
ref=Path("assets/image_wav-4eb8725b7ff41261.png")
out=Path("analysis/supersecret")
out.mkdir(parents=True,exist_ok=True)

with wave.open(str(wav),"rb") as w:
    samples=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float64)/32768.0

assert samples.size == 610*376*3
ref_arr=np.asarray(Image.open(ref).convert("RGB"),dtype=np.int16)
assert ref_arr.shape == (376,610,3)

cands={}
def add(name,a):
    a=np.clip(a,0,255).astype(np.uint8).reshape(376,610,3)
    diff=np.abs(a.astype(np.int16)-ref_arr)
    cands[name]={
        "mean_abs_error":float(diff.mean()),
        "max_abs_error":int(diff.max()),
        "exact_component_fraction":float((diff==0).mean()),
        "exact_pixel_fraction":float(np.all(diff==0,axis=2).mean()),
    }

add("shift_round",np.rint((samples+1)*127.5))
add("shift_floor",np.floor((samples+1)*127.5))
add("clip_round",np.rint(samples*255))
add("clip_floor",np.floor(samples*255))
add("signed_offset_32768",np.floor((samples*32768+32768)/257))
add("signed_offset_32767",np.rint((samples*32768+32768)*255/65535))

# Pixel-channel correlations help detect reference postprocessing even if no candidate is byte-exact.
for name in list(cands):
    pass

(out/"decode-comparison.json").write_text(json.dumps({
    "sample_count":int(samples.size),
    "factorization":"610*376*3",
    "reference_shape":list(ref_arr.shape),
    "candidate_metrics":cands,
},indent=2)+"\n",encoding="utf-8")
print(json.dumps(cands,indent=2))
