#!/usr/bin/env python3
"""Reproduce the canonical 3x3-crop shortcut and generated refutation."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path

TASK="27387ebf1485"

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path: Path):
    spec=importlib.util.spec_from_file_location("audit_27387",path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def rival(grid):
    marker=grid[0][0]
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==marker and (r,c)!=(0,0)]
    r1=min(r for r,_ in cells); c1=min(c for _,c in cells)
    return [row[c1:c1+3] for row in grid[r1:r1+3]]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,default=Path.cwd()); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    source=(args.repo/f"generators/{TASK}/generator.py").resolve(); mod=load(source)
    grid=mod.generate(0,0,difficulty="medium",scene_profile="singleton_target")
    expected=mod.rule_mirror(grid); wrong=rival(grid)
    canonical=[]
    for line in (args.repo/"shared/data/canonical/puzzles.jsonl").open():
      row=json.loads(line)
      if row.get("task_id")==TASK:
        pairs=row["train"]+(row["test"] if isinstance(row["test"],list) else [row["test"]])
        canonical=[{"index":i,"rival_matches":rival(p["input"])==p["output"],"output_shape":[len(p["output"]),len(p["output"][0])]} for i,p in enumerate(pairs)]
        break
    payload={
      "schema":"arcpuzzles-audit-counterexample-v1","task_id":TASK,
      "generator_sha256":sha(source),"rule_hash":getattr(mod,"RULE_HASH",None),
      "seed":0,"sample_index":0,"difficulty":"medium","overrides":{"scene_profile":"singleton_target"},
      "self_check":mod.self_check(grid,difficulty="medium"),"observed":mod.observe_overrides(grid),
      "canonical_rival_fit":canonical,"canonical_all_fit":all(x["rival_matches"] for x in canonical),
      "input":grid,"authority_mirror_output":expected,"fixed_3x3_rival_output":wrong,
      "rival_differs_on_generated_input":wrong!=expected,
      "semantic_contract_declared":any(hasattr(mod,name) for name in ("strict_canonical_like","SEMANTIC_WITNESSES","lesson_identifiable")),
    }
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    (args.out.parent/"input.json").write_text(json.dumps(grid,indent=2)+"\n")
    print(json.dumps({k:payload[k] for k in ("generator_sha256","self_check","observed","canonical_all_fit","rival_differs_on_generated_input","semantic_contract_declared")},indent=2))
    return 0 if (not payload["self_check"] and payload["canonical_all_fit"] and payload["rival_differs_on_generated_input"]) else 1
if __name__=="__main__": raise SystemExit(main())
