#!/usr/bin/env python3
"""Focused, read-only source-bound audit of 9adaf46a8128.

From WORK/repo:
  PYTHONDONTWRITEBYTECODE=1 python3 ../run_with_racket.py python3 ../checks/audit/9adaf46a8128/reproduce.py

Exit 0 confirms the recorded findings, not that the audited generator is fixed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3] / "repo"
OUT = Path(__file__).resolve().parent
TASK = "9adaf46a8128"
SOURCE = ROOT / f"generators/{TASK}/generator.py"
EXPECTED_SOURCE = "6ebe47df62eb74cf28b46409f0a96d9e5c6b8db81455cb79aa6019795b1ff845"
sys.path[:0] = [str(ROOT / "src"),str(ROOT / "shared/runtime")]
from arcpuzzles import Catalog


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value_hash(value):
    return hashlib.sha256(json.dumps(value,separators=(",",":"),sort_keys=True).encode()).hexdigest()


def apply_python(grid, *, marker4_identity=False):
    """Independent transcription of the selected rule, with one rival branch."""
    h,w = len(grid),len(grid[0])
    sep = next(r for r,row in enumerate(grid) if all(c==5 for c in row))
    cells = [(r,c) for r in range(sep) for c in range(w) if grid[r][c]!=0]
    r0,r1 = min(r for r,c in cells),max(r for r,c in cells)
    c0,c1 = min(c for r,c in cells),max(c for r,c in cells)
    template = [row[c0:c1+1] for row in grid[r0:r1+1]]
    out = [[0]*w for _ in range(h-sep-1)]
    for r in range(sep+1,h):
        for c in range(w):
            marker = grid[r][c]
            if marker not in (1,2,3,4):
                continue
            if marker==2:
                shape = [list(row) for row in zip(*reversed(template))]
            elif marker==3:
                shape = [list(reversed(row)) for row in reversed(template)]
            elif marker==4 and not marker4_identity:
                shape = [list(row) for row in zip(*template)]
            else:
                shape = template
            rr0 = r-sep-1-len(shape)//2
            cc0 = c-len(shape[0])//2
            for i,row in enumerate(shape):
                for j,colour in enumerate(row):
                    rr,cc = rr0+i,cc0+j
                    if colour!=0 and 0<=rr<len(out) and 0<=cc<w:
                        out[rr][cc]=colour
    return out


def marker_values(grid):
    sep = next(r for r,row in enumerate(grid) if all(c==5 for c in row))
    return sorted({c for row in grid[sep+1:] for c in row if c in (1,2,3,4)})


def main():
    assert sha256(SOURCE)==EXPECTED_SOURCE,"Audit is bound to the selected source bytes"
    spec = importlib.util.spec_from_file_location("audited_9adaf46a8128",SOURCE)
    gen = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(gen)
    catalog = Catalog(ROOT)
    record = catalog.get(TASK)
    assert record["rule_hash"]=="97f1e4b799fa"
    canonical = record["variants"][0]["train"]+record["variants"][0]["test"]
    assert len(canonical)==4

    controls = []
    endpoints = []
    for difficulty in (None,"easy","medium","hard"):
        baseline = gen.generate(0,0,difficulty=difficulty)
        for axis in ("palette_size","n_distinct_colors"):
            overrides = {axis:2}
            grid = gen.generate(0,0,difficulty=difficulty,**overrides)
            colors = sorted({c for row in grid for c in row})
            errors = gen.self_check(grid,difficulty=difficulty,meta={"overrides":overrides})
            assert len(colors)>2 and not errors
            assert grid==baseline
            controls.append({"seed":0,"sample_index":0,"difficulty":difficulty,
                "overrides":overrides,"input":grid,"input_sha256":value_hash(grid),
                "observed_colors":colors,"observed_distinct_colors":len(colors),
                "unchanged_from_no_override":grid==baseline,"self_check":errors})
        for overrides in ({"grid_h":8},{"grid_h":14},{"grid_w":10}):
            try:
                grid=gen.generate(0,0,difficulty=difficulty,**overrides)
            except (TypeError,ValueError) as exc:
                endpoints.append({"seed":0,"sample_index":0,"difficulty":difficulty,
                    "overrides":overrides,"error_type":type(exc).__name__,"error":str(exc)})
            else:
                raise AssertionError(f"Expected documented endpoint rejection: {difficulty}, {overrides}, {grid}")

    # The review index already contains this source-bound teaching witness.
    # Recreate it independently through the production API; do not import old
    # audit programs or any solve artifacts.
    episode = catalog.generate(TASK,count=1,seed=6,difficulty="easy",n_train=3,
        n_test=1,sample_index=0,allow_unapproved=True)[0]
    assert episode["sample_indices"]==[0,1,2,3]
    assert episode["rejections"]==[]
    assert episode["executed_rule_hash"]=="97f1e4b799fa"
    pairs=episode["train"]+episode["test"]
    rival_rows=[]
    for index,pair in zip(episode["sample_indices"],pairs):
        grid=pair["input"]
        assert gen.self_check(grid,difficulty="easy")==[]
        assert apply_python(grid)==pair["output"]
        rival=apply_python(grid,marker4_identity=True)
        disagreements=[{"row":r,"col":c,"authority":pair["output"][r][c],"rival":rival[r][c]}
            for r in range(len(rival)) for c in range(len(rival[0]))
            if pair["output"][r][c]!=rival[r][c]]
        rival_rows.append({"sample_index":index,**pair,"input_sha256":value_hash(grid),
            "output_sha256":value_hash(pair["output"]),"markers":marker_values(grid),
            "rival_output":rival,"rival_matches":rival==pair["output"],
            "disagreements":disagreements,"self_check":[]})
    assert [row["rival_matches"] for row in rival_rows]==[True,True,True,False]

    # One small reference-application batch checks all canonical examples and
    # one palette override input per difficulty against the selected authority.
    override_inputs=[row["input"] for row in controls if "n_distinct_colors" in row["overrides"]]
    applied=catalog.apply(TASK,[p["input"] for p in canonical]+override_inputs,
        allow_unapproved=True,check_generator_domain=True)
    assert applied["executed_rule_hash"]=="97f1e4b799fa"
    assert applied["generator_sha256"]==EXPECTED_SOURCE
    for pair,result in zip(canonical,applied["results"][:4]):
        assert result["error"] is None
        assert result["output"]==pair["output"]==apply_python(pair["input"])
    for result in applied["results"][4:]:
        assert result["error"] is None
        assert result["generator_domain"]["status"]=="valid"

    report={
        "schema":"arcpuzzles-focused-audit-v1","task_id":TASK,
        "source_sha256":EXPECTED_SOURCE,"rule_hash":applied["executed_rule_hash"],
        "rule_text_sha256":applied["rule_text_sha256"],
        "source_path":f"generators/{TASK}/generator.py",
        "support_hashes":{str(p.relative_to(ROOT)):sha256(p) for p in (
            ROOT/f"generators/{TASK}/notes.md",
            ROOT/f"generators/{TASK}/evidence/review_index.json",
            ROOT/"shared/runtime/puzzle_generators/base.py",
            ROOT/"src/arcpuzzles/worker.py",
        )},
        "command":"PYTHONDONTWRITEBYTECODE=1 python3 ../run_with_racket.py python3 ../checks/audit/9adaf46a8128/reproduce.py",
        "cwd":str(ROOT),"exit_code":0,
        "findings":[
            {"id":"A1","status":"newly_reproduced","kind":"override_contract",
             "summary":"Declared palette_size=2 and n_distinct_colors=2 are silently ignored in every difficulty mode; returned valid grids use more colors and equal the no-override draw.",
             "evidence":"override-cases.json"},
            {"id":"A2","status":"newly_reproduced","kind":"override_domain",
             "summary":"Documented grid_h endpoints 8 and 14 and grid_w endpoint 10 raise ValueError in every difficulty mode.",
             "evidence":"endpoint-cases.json"},
            {"id":"A3","status":"existing_unresolved_finding_independently_reproduced",
             "kind":"lesson_ambiguity",
             "summary":"The easy-seed-6 query uses marker 4 without a single marker-4 demonstration; marker4_is_identity fits all demos and fails the query.",
             "prior_return_ids":["review-6e327f73fe1ea04f:v0001","review-18d3b90f01140858:v0001"],
             "evidence":"lesson-reproduction.json"},
        ],
        "coverage":{"override_success_calls":8,"endpoint_error_calls":12,
                    "production_episodes":1,"production_pairs":4,
                    "canonical_reference_pairs":4,"override_reference_pairs":4},
        "limits":["Focused audit, not a full battery or seed census.",
                  "The teaching witness was already recorded; this receipt supplies a fresh independent replay.",
                  "No target or shared source, tests, notes, catalog, or prior solve artifacts were changed or executed.",
                  "No new output-label defect was observed in the four canonical and four production pairs checked."],
    }
    lesson={"task_id":TASK,"source_sha256":EXPECTED_SOURCE,"rule_hash":applied["executed_rule_hash"],
        "recipe":{"seed":6,"difficulty":"easy","sample_index":0,"overrides":{},
                  "n_train":3,"n_test":1,"allow_unapproved":True},
        "accepted_sample_indices":episode["sample_indices"],"rejections":episode["rejections"],
        "lesson_check":episode["lesson_check"],"rival_name":"marker4_is_identity","pairs":rival_rows}
    for name,data in [("audit.json",report),("override-cases.json",controls),
                      ("endpoint-cases.json",endpoints),("lesson-reproduction.json",lesson),
                      ("racket.json",applied)]:
        (OUT/name).write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({"task_id":TASK,"source_sha256":EXPECTED_SOURCE,
        "rule_hash":report["rule_hash"],"rule_text_sha256":report["rule_text_sha256"],
        "override_observed_counts":[r["observed_distinct_colors"] for r in controls],
        "endpoint_errors":len(endpoints),"accepted_indices":episode["sample_indices"],
        "marker_sets":[r["markers"] for r in rival_rows],
        "rival_matches":[r["rival_matches"] for r in rival_rows],
        "query_disagreements":rival_rows[-1]["disagreements"],
        "coverage":report["coverage"],"exit_code":0},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
