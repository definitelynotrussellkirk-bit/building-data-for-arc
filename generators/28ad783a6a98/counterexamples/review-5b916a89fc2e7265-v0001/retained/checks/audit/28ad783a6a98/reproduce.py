#!/usr/bin/env python3
"""Reproduce 28ad783a6a98's exact second_transform override rewrite."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path

TASK="28ad783a6a98"
CODES=("r1","r2","r3","fh","fv","tr","atr")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path: Path):
    spec=importlib.util.spec_from_file_location("audit_28ad", path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def xform(grid, code):
    h,w=len(grid),len(grid[0])
    if code=="r1": return [[grid[h-1-r][c] for r in range(h)] for c in range(w)]
    if code=="r2": return [[grid[h-1-r][w-1-c] for c in range(w)] for r in range(h)]
    if code=="r3": return [[grid[c][h-1-r] for c in range(w)] for r in range(h)]
    if code=="fh": return [list(reversed(row)) for row in grid]
    if code=="fv": return list(reversed([row[:] for row in grid]))
    if code=="tr": return [[grid[r][c] for r in range(h)] for c in range(w)]
    if code=="atr": return [[grid[w-1-c][h-1-r] for c in range(w)] for r in range(h)]
    raise ValueError(code)

def panels(grid):
    return [[[grid[r][k*5+c] for c in range(4)] for r in range(4)] for k in range(5)]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,default=Path.cwd()); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    source=(args.repo/f"generators/{TASK}/generator.py").resolve(); mod=load(source)
    requested=("r1","r3")
    grid=mod.generate(0,0,difficulty="medium",first_transform=requested[0],second_transform=requested[1])
    ps=panels(grid)
    observed_first=[code for code in CODES if xform(ps[0],code)==ps[1]]
    observed_second=[code for code in CODES if xform(ps[2],code)==ps[3]]
    composed_requested=xform(xform(ps[4],requested[0]),requested[1])
    composed_observed=xform(xform(ps[4],observed_first[0]),observed_second[0])
    payload={
      "schema":"arcpuzzles-audit-counterexample-v1","task_id":TASK,
      "generator_sha256":sha(source),"rule_hash":getattr(mod,"RULE_HASH",None),
      "seed":0,"sample_index":0,"difficulty":"medium",
      "overrides":{"first_transform":requested[0],"second_transform":requested[1]},
      "observed":{"first_transform":observed_first,"second_transform":observed_second},
      "override_honored":observed_first==[requested[0]] and observed_second==[requested[1]],
      "root_cause":"generate rewrites t2 after draw when requested composition leaves X unchanged",
      "requested_composition_leaves_x_unchanged":composed_requested==ps[4],
      "observed_composition_leaves_x_unchanged":composed_observed==ps[4],
      "self_check":mod.self_check(grid,difficulty="medium"),
      "input":grid,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    (args.out.parent/"input.json").write_text(json.dumps(grid,indent=2)+"\n")
    print(json.dumps({k:payload[k] for k in ("generator_sha256","overrides","observed","override_honored","requested_composition_leaves_x_unchanged","self_check")},indent=2))
    return 0 if (not payload["override_honored"] and not payload["self_check"]) else 1
if __name__=="__main__": raise SystemExit(main())
