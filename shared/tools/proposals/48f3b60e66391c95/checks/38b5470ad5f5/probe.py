#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path

TASK="38b5470ad5f5"


def load_generator(repo):
    path=repo/"generators"/TASK/"generator.py"
    spec=importlib.util.spec_from_file_location(f"probe_{TASK}",path)
    module=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
    return module,path


def read_racket(path):
    if path is None: return None
    return json.loads(Path(path).read_text())["results"][0]["output"]


def rival(grid):
    h,w=len(grid),len(grid[0])
    # Exact canonical control flow, except for the deliberate shortcut that
    # treats both 0 and 7 as background. Horizontal fills have priority.
    h_fill={}
    v_fill={}
    for r in range(h):
        for c in range(w):
            color=grid[r][c]
            if color in (0,7):
                continue
            if c < w-1 and grid[r][c+1] == color and r not in h_fill:
                h_fill[r]=color
            if r < h-1 and grid[r+1][c] == color and c not in v_fill:
                v_fill[c]=color
    return [[h_fill[r] if r in h_fill else v_fill[c] if c in v_fill else 7
             for c in range(w)] for r in range(h)]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,default=Path.cwd()); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--racket",type=Path)
    args=ap.parse_args(); gen,source=load_generator(args.repo); args.out.mkdir(parents=True,exist_ok=True)
    zero_draws=0; unique=set()
    for band in ("easy",None,"hard"):
        for i in range(100):
            g=gen.generate(20261024,i,difficulty=band)
            zero_draws += int(any(v==0 for row in g for v in row))
            unique.add(json.dumps(g,separators=(",",":")))
    archived=args.repo/"generators"/TASK/"counterexamples"/"review-f6ed5c61ee54007c-v0001"/"retained"/"checks"/"audit"/TASK/"input.json"
    witness=json.loads(archived.read_text()); (args.out/"black-pair-input.json").write_text(json.dumps(witness,indent=2)+"\n")
    actual=read_racket(args.racket); wrong=rival(witness)
    report={"schema":"arcpuzzles-peer-adversarial-probe-v1","task_id":TASK,
      "generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"draws":300,"unique_inputs":len(unique),"zero_color_draws":zero_draws,
      "source_fact":"Every palette pool and fallback omits 0 although the canonical non-7 foreground domain includes black pairs.",
      "self_check":gen.self_check(witness),"rival":"treat_0_and_7_as_background","rival_output":wrong,
      "recommended_repair":"Lesson-schedule at least one ordinary demonstration with a black horizontal or vertical pair; include 0 in the generated palette while keeping 7 as the sole background.",
      "racket":{}}
    if actual is not None:
        diff=sum(a!=b for ra,rb in zip(actual,wrong) for a,b in zip(ra,rb))
        report["racket"]={"output":actual,"different_cells_vs_rival":diff}
        assert diff==15
    assert zero_draws==0 and report["self_check"]==[]
    (args.out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"task_id":TASK,"status":"finding_reproduced","zero_color_draws":zero_draws,"racket":report["racket"] and "verified" or "pending"},sort_keys=True))

if __name__=="__main__": main()
