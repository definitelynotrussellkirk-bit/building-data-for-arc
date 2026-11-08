#!/usr/bin/env python3
from __future__ import annotations
from copy import deepcopy
import hashlib, importlib.util, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
TARGET = REPO / "generators" / "f891d1ff5dd8" / "generator.py"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
from reviewer_support import canonical_pairs

spec=importlib.util.spec_from_file_location("audit_f891",TARGET)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def two_cycles_only(grid):
    out=deepcopy(grid); width=len(grid[0])
    stop=min(len(grid),2+2*width)
    for r in range(2,stop):
        out[r]=[grid[0][(r-2)%width]]*width
    return out

canonical = canonical_pairs("f891d1ff5dd8", root=REPO)
canonical_fit = sum(two_cycles_only(pair["input"]) == pair["output"] for pair in canonical)
assert canonical_fit == len(canonical)

found=None
for difficulty in (None,"easy","medium","hard"):
    for seed in range(10000):
        grids=[mod.generate(seed,i,difficulty=difficulty) for i in range(4)]
        truths=[mod.rule_mirror(g) for g in grids]
        rivals=[two_cycles_only(g) for g in grids]
        if all(truths[i]==rivals[i] for i in range(3)) and truths[3]!=rivals[3]:
            found={
              "schema":"arcpuzzles-audit-semantic-counterexample-v1",
              "task_id":"f891d1ff5dd8",
              "generator_sha256":hashlib.sha256(TARGET.read_bytes()).hexdigest(),
              "declared_version":mod.VERSION,
              "difficulty":"none" if difficulty is None else difficulty,
              "seed":seed,
              "demo_sample_indices":[0,1,2],
              "query_sample_index":3,
              "rival":"two_header_cycles_only",
              "canonical_pairs":len(canonical),
              "canonical_rival_fit_count":canonical_fit,
              "rival_definition":"Preserve rows 0-1; overwrite at most the next 2*width rows using row 0 cyclically; leave later rows unchanged.",
              "demos":[
                {"sample_index":i,"input":grids[i],"expected_output":truths[i],"rival_output":rivals[i],
                 "dimensions":[len(grids[i]),len(grids[i][0])],"body_rows":len(grids[i])-2,
                 "two_cycle_rows":2*len(grids[i][0]),"self_check":mod.self_check(grids[i])}
                for i in range(3)
              ],
              "query":{"sample_index":3,"input":grids[3],"expected_output":truths[3],"rival_output":rivals[3],
                 "dimensions":[len(grids[3]),len(grids[3][0])],"body_rows":len(grids[3])-2,
                 "two_cycle_rows":2*len(grids[3][0]),"self_check":mod.self_check(grids[3])},
              "claim":"The canonical-fitting two-cycle rival fits all three sequential demonstrations but changes the next query."
            }
            break
    if found: break
if not found: raise SystemExit("no ambiguous sequential lesson found")
base=Path(__file__).parent
(base/'two_cycles_lesson.json').write_text(json.dumps(found,indent=2)+'\n')
(base/'lesson_inputs.json').write_text(json.dumps([d['input'] for d in found['demos']]+[found['query']['input']],indent=2)+'\n')
print(json.dumps({"difficulty":found['difficulty'],"seed":found['seed'],"demo_dimensions":[d['dimensions'] for d in found['demos']],"query_dimensions":found['query']['dimensions'],"generator_sha256":found['generator_sha256']},indent=2))
