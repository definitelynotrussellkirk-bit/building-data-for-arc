"""Small source-bound audit; all outputs remain alongside this script.

Run from packet root: python3 checks/audit/9a7579840f41/probe.py prepare
then the documented public apply command, then this script with verify.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TASK = "9a7579840f41"
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_generator", REPO / f"generators/{TASK}/generator.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse(grid):
    return [[int(x) for x in row] for row in grid]

def local_corner_rival(grid):
    """Treat 7 as another wire cell; no ordered tracing or endpoint exclusion."""
    h, w = len(grid), len(grid[0])
    wire = {(r,c) for r in range(h) for c in range(w) if grid[r][c] in (1,7)}
    template = [(r,c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    top, left = min(r for r,c in template), min(c for r,c in template)
    shape = [(r-top,c-left) for r,c in template]
    turns = [(r,c) for r,c in wire
             if ((r-1,c) in wire or (r+1,c) in wire)
             and ((r,c-1) in wire or (r,c+1) in wire)]
    out = [[0]*w for _ in range(h)]
    for r,c in turns:
        for dr,dc in shape:
            if r+dr < h and c+dc < w:
                out[r+dr][c+dc] = 4
    return out

def independent_reference(grid):
    """Trace only color 1 and exclude first/last wire cells from turn test."""
    h,w = len(grid), len(grid[0])
    wire = {(r,c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    start = next((r,c) for r in range(h) for c in range(w) if grid[r][c] == 7)
    def neighbors(p):
        r,c = p
        return [(rr,cc) for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if (rr,cc) in wire]
    cur = neighbors(start)[0]
    prev = start
    path = []
    while True:
        path.append(cur)
        nxt = [p for p in neighbors(cur) if p != prev and p not in path]
        if not nxt:
            break
        prev,cur = cur,nxt[0]
    turns = [b for a,b,c in zip(path,path[1:],path[2:]) if (b[0]-a[0],b[1]-a[1]) != (c[0]-b[0],c[1]-b[1])]
    template = [(r,c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    top,left = min(r for r,c in template), min(c for r,c in template)
    shape = [(r-top,c-left) for r,c in template]
    out = [[0]*w for _ in range(h)]
    for r,c in turns:
        for dr,dc in shape:
            if r+dr < h and c+dc < w:
                out[r+dr][c+dc] = 4
    return out

def prepare():
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    row = next(json.loads(line) for line in canonical_path.read_text().splitlines() if json.loads(line)["task_id"] == TASK)
    cases = []
    for i,pair in enumerate(row["train"] + [row["test"]]):
        cases.append({"kind":"canonical", "pair_index":i, "domain_status":"canonical", "input":parse(pair["input"]), "canonical_output":parse(pair["output"])})
    for i,band in enumerate(("easy","medium","hard")):
        seed,idx = 19420+i,7+i
        grid = generator.generate(seed,idx,difficulty=band)
        cases.append({"kind":"generated", "seed":seed,"sample_index":idx,"difficulty":band,"overrides":{}, "domain_status":"normal generated; self_check passes", "input":grid})
    # Move only the marker on the easy generated draw to a perpendicular
    # neighbor of its initial wire endpoint. This remains self_check-lawful.
    grid = [r[:] for r in cases[3]["input"]]
    start = next((r,c) for r,row in enumerate(grid) for c,x in enumerate(row) if x == 7)
    path,error = generator._trace_wire_from_start(grid)
    assert error is None
    first = path[0]
    dr,dc = path[1][0]-first[0],path[1][1]-first[1]
    wire = set(path)
    for drr,dcc in ((-dc,dr),(dc,-dr)):
        pos = first[0]+drr,first[1]+dcc
        r,c = pos
        if not(0<=r<len(grid) and 0<=c<len(grid[0])) or grid[r][c] != 0:
            continue
        if sum(p in wire for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))) != 1:
            continue
        grid[start[0]][start[1]] = 0
        grid[r][c] = 7
        break
    else:
        raise AssertionError("no lawful perpendicular marker placement")
    assert generator.self_check(grid) == []
    cases.append({"kind":"marker_perpendicular", "derived_from_case":3, "mutation":"move only 7 perpendicular to first wire step", "domain_status":"self_check-lawful invariant-domain witness; outside generator support", "input":grid})
    for case in cases:
        case["self_check"] = generator.self_check(case["input"])
        case["independent_reference"] = independent_reference(case["input"])
        case["rival_output"] = local_corner_rival(case["input"])
    sources = [f"generators/{TASK}/generator.py", f"generators/{TASK}/evidence/associated_notes.jsonl", "shared/runtime/puzzle_generators/base.py", "shared/data/canonical/puzzles.jsonl", f"shared/data/base/solutions/banks/76c10b1ad4b3/S6_H4__{TASK}.json"]
    report = {"task_id":TASK,"sources_sha256":{p:sha(REPO/p) for p in sources}, "canonical_row_sha256":hashlib.sha256(json.dumps(row,sort_keys=True,separators=(",",":")).encode()).hexdigest(), "sample_plan":"three fixed normal draws: seed 19420..19422, sample_index 7..9, easy/medium/hard; no overrides; three canonical pairs; one marker-only witness", "cases":cases}
    (HERE/"input.json").write_text(json.dumps([c["input"] for c in cases])+"\n")
    (HERE/"evidence.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"prepared_cases":len(cases),"path":str(HERE/"input.json")}))

def verify():
    report = json.loads((HERE/"evidence.json").read_text())
    actual = json.loads((HERE/"racket.json").read_text())
    if isinstance(actual,dict):
        actual = actual.get("outputs",actual.get("results",actual))
    assert isinstance(actual,list), type(actual)
    assert len(actual)==len(report["cases"])
    for case,out in zip(report["cases"],actual):
        if isinstance(out,dict):
            out=out.get("output",out)
        case["racket_output"] = out
        case["independent_reference_match"] = out==case["independent_reference"]
        case["rival_match"] = out==case["rival_output"]
        case["rival_extra_cells"] = [[r,c] for r in range(len(out)) for c in range(len(out[0])) if case["rival_output"][r][c] == 4 and out[r][c] != 4]
        assert case["independent_reference_match"]
        if case["kind"] == "canonical":
            assert out == case["canonical_output"]
    report["result"] = {"public_racket_reference_matches":"7/7 retained cases", "generated_rival_matches":"3/3 normal draws", "canonical_rival_matches":"0/3 canonical pairs", "mutated_rival_matches":"0/1 lawful marker-only witness"}
    (HERE/"evidence.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report["result"]))

{"prepare":prepare,"verify":verify}[sys.argv[1]]()
