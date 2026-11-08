"""Findings-only: a canonical-fitting directional restriction, not a repair."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
SOURCE = REPO / "generators/498af9326ab9/generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def restricted_union(grid):
    """Wrong rule: forbid backwards motion on the larger marker-displacement axis."""
    h, w = len(grid), len(grid[0])
    start = next((r,c) for r in range(h) for c in range(w) if grid[r][c] == 1)
    goal = next((r,c) for r in range(h) for c in range(w) if grid[r][c] == 2)
    axis = 0 if abs(goal[0]-start[0]) >= abs(goal[1]-start[1]) else 1
    sign = 1 if goal[axis] >= start[axis] else -1
    deltas = [d for d in ((1,0),(-1,0),(0,1),(0,-1)) if d[axis]*sign >= 0]
    def distances(origin, steps):
        out = {origin: 0}
        queue = deque([origin])
        while queue:
            r,c = queue.popleft()
            for dr,dc in steps:
                n = r+dr, c+dc
                if 0 <= n[0] < h and 0 <= n[1] < w and grid[n[0]][n[1]] != 5 and n not in out:
                    out[n] = out[r,c]+1
                    queue.append(n)
        return out
    ds = distances(start, deltas)
    dg = distances(goal, [(-dr,-dc) for dr,dc in deltas])
    D = ds.get(goal)
    return [[8 if grid[r][c] == 0 and D is not None and (r,c) in ds and (r,c) in dg and ds[r,c]+dg[r,c] == D else grid[r][c] for c in range(w)] for r in range(h)]


def corridor():
    g = [[5]*9 for _ in range(9)]
    points = [(4,1),(1,1),(1,5),(3,5),(3,3),(6,3),(6,7),(4,7)]
    for (r,c),(rr,cc) in zip(points, points[1:]):
        dr,dc = (rr>r)-(rr<r),(cc>c)-(cc<c)
        g[r][c] = 0
        while (r,c) != (rr,cc):
            r,c = r+dr,c+dc
            g[r][c] = 0
    g[4][1],g[4][7] = 1,2
    return g


def prepare():
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as f:
        canonical = next(json.loads(line) for line in f if json.loads(line).get("task_id") == gen.TASK_ID)
    pairs = canonical["train"] + canonical["test"]
    cases = [{"kind":"canonical", "pair_index":i, "input":p["input"], "expected":p["output"]} for i,p in enumerate(pairs) if p.get("output")]
    for b,band in enumerate((None,"easy","medium","hard")):
        for p,profile in enumerate(gen.GENERAL_PROFILES):
            seed = 100*b+p
            g = gen.generate(seed, 17, difficulty=band, scene_profile=profile)
            cases.append({"kind":"generated", "seed":seed, "sample_index":17, "difficulty":band, "overrides":{"scene_profile":profile}, "input":g, "expected":gen.rule_mirror(g)})
    g = corridor()
    cases.append({"kind":"handbuilt", "construction":"single corridor with obligatory leftward segment (3,5)->(3,3)", "input":g, "expected":gen.rule_mirror(g)})
    for case in cases:
        case["validator_errors"] = gen.self_check(case["input"])
        case["observed_profile"] = gen.observe_overrides(case["input"])
        case["rival_output"] = restricted_union(case["input"])
    identity = {"task_id":gen.TASK_ID,"generator_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),"canonical_rule_sha256":hashlib.sha256(" ".join(canonical["program_solution"].split()).encode()).hexdigest(),"declared_rule_hash":gen.RULE_HASH,"declared_canonical_shortcuts":getattr(gen,"CANONICAL_SHORTCUTS",None),"declared_lesson_competitors":getattr(gen,"LESSON_COMPETITORS",None)}
    (HERE/"input.json").write_text(json.dumps([c["input"] for c in cases])+"\n")
    (HERE/"cases.json").write_text(json.dumps({"source":identity,"cases":cases}, separators=(",",":"))+"\n")
    print(json.dumps({"source":identity,"canonical_cases":len(pairs),"generated_cases":len(cases)-len(pairs)-1,"handbuilt":1,"validation_errors":[c["validator_errors"] for c in cases if c["validator_errors"]],"rival_fits_canonical":sum(c["rival_output"]==c["expected"] for c in cases if c["kind"]=="canonical"),"rival_fits_generated":sum(c["rival_output"]==c["expected"] for c in cases if c["kind"]=="generated"),"counterexample_diff_cells":sum(a!=b for x,y in zip(cases[-1]["expected"],cases[-1]["rival_output"]) for a,b in zip(x,y))},indent=2))


def verify():
    record = json.loads((HERE/"cases.json").read_text())
    racket = json.loads((HERE/"racket.json").read_text())
    cases, results = record["cases"], racket["results"]
    assert record["source"]["generator_sha256"] == racket["generator_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert len(cases) == len(results) == 46
    assert all(not r["error"] and r["valid_output"] for r in results)
    assert all(c["expected"] == r["output"] for c,r in zip(cases,results))
    summary = {"source":record["source"],"racket_rule_text_sha256":racket["rule_text_sha256"],"racket_reference":racket["reference"],"phase":"final audit target, unchanged","racket_cases":len(cases),"racket_expected_matches":len(cases),"all_inputs_validator_accepted":all(not c["validator_errors"] for c in cases),"groups":{}}
    for kind in ("canonical","generated","handbuilt"):
        subset = [(c,r) for c,r in zip(cases,results) if c["kind"]==kind]
        summary["groups"][kind] = {"count":len(subset),"unique_inputs":len({json.dumps(c["input"]) for c,r in subset}),"rival_matches":sum(c["rival_output"]==r["output"] for c,r in subset)}
    c,r = cases[-1],results[-1]
    witness = {"source":summary["source"],"racket_rule_text_sha256":racket["rule_text_sha256"],"origin":"handbuilt; no seed/sample/overrides","validation":{"errors":c["validator_errors"],"observed_profile":c["observed_profile"]},"domain_membership":"Valid for the written shortest-path rule and accepted as twin_gates by self_check/observe_overrides; outside actual generator constructor support: not an exact public input, empty grid, solid wall, or one vertical barrier with two gaps.","input":c["input"],"actual_racket_output":r["output"],"rival_output":c["rival_output"],"differing_cells":[[i,j] for i,row in enumerate(r["output"]) for j,value in enumerate(row) if value!=c["rival_output"][i][j]],"command":{"cwd":"packet_root","argv":["python3","run_with_racket.py","python3","-m","arcpuzzles","apply",gen.TASK_ID,"--input","../checks/audit/498af9326ab9/input.json","--out","../checks/audit/498af9326ab9/racket.json"],"exit_code":0,"result_index":45}}
    (HERE/"counterexample.json").write_text(json.dumps(witness,indent=2)+"\n")
    (HERE/"verification.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    verify() if "--verify" in sys.argv else prepare()
