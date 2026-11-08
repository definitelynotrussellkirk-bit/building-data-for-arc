#!/usr/bin/env python3
"""Check shape rejection before exact-code positions are indexed."""
from __future__ import annotations

import json
from pathlib import Path
import traceback

from reviewer_support import load_selected_generator


root=Path.cwd()
out=Path(__file__).resolve().parent
gen,source,digest=load_selected_generator("fc814cec3976",root=root)
original=gen.generate(0,0,scene_code=5)
cropped=[row[:16] for row in original[:16]]
rows=[]
for name in ("self_check","strict_canonical_like","observe_overrides"):
    try:
        value=getattr(gen,name)(cropped)
        rows.append({"hook":name,"status":"returned","value":value})
    except Exception as error:
        rows.append({"hook":name,"status":"raised","exception_type":type(error).__name__,"error":str(error),"traceback":traceback.format_exc()})
report={"generator_sha256":digest,"input":cropped,"shape":[16,16],"same_red_key":gen._red_key(original)==gen._red_key(cropped),"results":rows}
(out / "malformed-validator-review.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({"generator_sha256":digest,"same_red_key":report["same_red_key"],"results":[{k:r[k] for k in r if k!="traceback"} for r in rows]}),flush=True)
