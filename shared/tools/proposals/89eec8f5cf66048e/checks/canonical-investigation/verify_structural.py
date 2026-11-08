#!/usr/bin/env python3
"""Canonical Racket checks of the already measured minimal structural patches."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback

from arcpuzzles import Catalog
from mutation_probe import scan, summary, dump, ROOT, TASK, OUT


def main():
    census=json.loads((OUT / "structural-patch-census.json").read_text())
    rows=[x for x in census["templates"] if x["minimal_patch"]]
    inputs=[]
    for row in rows:
        patch=row["minimal_patch"]
        base=deepcopy(patch["input"])
        for r,c,before,after in patch["changes"]:
            assert base[r][c]==after
            base[r][c]=before
        inputs.extend([base,patch["input"]])
    receipt=Catalog(ROOT).apply(TASK,inputs,check_generator_domain=True,timeout=180)
    dump("structural-racket-raw-receipt.json",receipt)
    verified=[]
    for i,row in enumerate(rows):
        original,changed=inputs[2*i:2*i+2]
        base_result,patch_result=receipt["results"][2*i:2*i+2]
        base_out,actual=base_result["output"],patch_result["output"]
        lookup=deepcopy(changed)
        for r in range(19):
            for c in range(19):
                if base_out[r][c]!=original[r][c]:
                    lookup[r][c]=base_out[r][c]
        verified.append({
            "profile":row["profile"],"profile_index":row["profile_index"],"transform":row["transform"],
            "changes":row["minimal_patch"]["changes"],"racket_result_indexes":[2*i,2*i+1],
            "canonical_matches_independent_original":base_out==scan(original)[2],
            "canonical_matches_independent_changed":actual==scan(changed)[2],
            "canonical_differs_lookup":actual!=lookup,
            "lookup_mismatch_count":sum(actual[r][c]!=lookup[r][c] for r in range(19) for c in range(19)),
            "same_red_key":[(r,c) for r in range(19) for c in range(19) if original[r][c]==2]==[(r,c) for r in range(19) for c in range(19) if changed[r][c]==2],
            "facts":summary(changed),
            "rival_disagreements":{mode:scan(changed,mode)[2]!=actual for mode in ("reading_order","reverse_tie","cell_overlap","independent_windows")},
        })
    result={
        "schema":"fc814cec3976-structural-racket-verification-v1",
        "analytical_baseline_source":census["generator_source"],
        "analytical_baseline_sha256":census["generator_sha256"],
        "execution_generator_sha256":receipt["generator_sha256"],
        "executed_rule_hash":receipt["executed_rule_hash"],
        "rule_text_sha256":receipt["rule_text_sha256"],
        "rule_file":receipt["rule_file"],
        "raw_receipt_sha256":hashlib.sha256((OUT / "structural-racket-raw-receipt.json").read_bytes()).hexdigest(),
        "all_verified":all(x["canonical_matches_independent_original"] and x["canonical_matches_independent_changed"] and x["canonical_differs_lookup"] and x["same_red_key"] for x in verified),
        "pair_count":len(verified),"rows":verified,
    }
    dump("structural-racket-verification.json",result)
    print(json.dumps({k:result[k] for k in ("analytical_baseline_sha256","execution_generator_sha256","executed_rule_hash","rule_text_sha256","pair_count","all_verified")}),flush=True)


if __name__=="__main__":
    command={"argv":sys.argv,"python":sys.executable,"cwd":str(ROOT),"started_utc":datetime.now(timezone.utc).isoformat()}
    try:
        main()
    except BaseException as exc:
        command.update(exit_code=1,error=str(exc),traceback=traceback.format_exc(),run=getattr(exc,"run",None))
        dump("structural-racket-command.json",command)
        raise
    else:
        command.update(exit_code=0,finished_utc=datetime.now(timezone.utc).isoformat())
        dump("structural-racket-command.json",command)
