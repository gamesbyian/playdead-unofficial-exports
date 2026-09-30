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
    raw=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2")
samples=raw.astype(np.float64)/32768.0

assert samples.size == 610*376*3
ref_arr=np.asarray(Image.open(ref).convert("RGB"),dtype=np.int16)
assert ref_arr.shape == (376,610,3)

cands={}
def score_arr(name,a):
    a=np.clip(a,0,255).astype(np.uint8)
    diff=np.abs(a.astype(np.int16)-ref_arr)
    cands[name]={
        "mean_abs_error":float(diff.mean()),
        "max_abs_error":int(diff.max()),
        "exact_component_fraction":float((diff==0).mean()),
        "exact_pixel_fraction":float(np.all(diff==0,axis=2).mean()),
    }

def interleaved(v):
    return v.reshape(376,610,3)

def row_planar(v):
    return v.reshape(376,3,610).transpose(0,2,1)

mappings={
    "shift_round":np.rint((samples+1)*127.5),
    "shift_floor":np.floor((samples+1)*127.5),
    "clip_round":np.rint(samples*255),
    "clip_floor":np.floor(samples*255),
    "signed_offset_32768":np.floor((samples*32768+32768)/257),
    "signed_offset_32767":np.rint((samples*32768+32768)*255/65535),
    "high_byte":((raw.astype(np.int32)+32768)//256),
    "high_byte_round":np.rint((raw.astype(np.float64)+32768)/256),
    "u16_65535_round":np.rint((raw.astype(np.float64)+32768)*255/65535),
    "u16_65535_floor":np.floor((raw.astype(np.float64)+32768)*255/65535),
    "posneg_32767_round":np.rint(((np.where(raw>=0,raw.astype(np.float64)/32767.0,raw.astype(np.float64)/32768.0))+1)*127.5),
    "posneg_32767_floor":np.floor(((np.where(raw>=0,raw.astype(np.float64)/32767.0,raw.astype(np.float64)/32768.0))+1)*127.5),
}
for norm,v in mappings.items():
    score_arr("interleaved_"+norm,interleaved(v))
    score_arr("row_planar_"+norm,row_planar(v))

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
