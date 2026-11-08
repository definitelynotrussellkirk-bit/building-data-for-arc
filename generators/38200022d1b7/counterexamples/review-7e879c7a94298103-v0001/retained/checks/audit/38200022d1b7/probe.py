"""Source-bound findings-only probe for a local-window copy shortcut."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs

TASK = "38200022d1b7"
SOURCE = REPO / f"generators/{TASK}/generator.py"
spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert sha == "972a9fe6682f87810649cde398fa1c7e2692cfe58740badabb708becc2ab65d1"
row = next(json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()
           if json.loads(line).get("task_id") == TASK)
rule_hash = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
assert rule_hash == gen.RULE_HASH == "514de6262239"

def local_window_rival(grid):
    """Keep source cells; copy only sources inside the pivot's 7x7 window."""
    out = [r[:] for r in grid]
    pivots = [(r,c) for r,rr in enumerate(grid) for c,v in enumerate(rr) if v == 5]
    assert len(pivots) == 1
    pr,pc = pivots[0]
    for r,rr in enumerate(grid):
        for c,v in enumerate(rr):
            if v not in (0,5) and max(abs(pr-r),abs(pc-c)) <= 3:
                tr,tc = 2*pr-r,2*pc-c
                if 0 <= tr < len(grid) and 0 <= tc < len(grid[0]):
                    out[tr][tc] = v
    return out

def support_radius(grid):
    pr,pc = next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 5)
    return max(max(abs(pr-r),abs(pc-c)) for r,row in enumerate(grid)
               for c,v in enumerate(row) if v not in (0,5))

inputs, cases = [], []
for band in ("easy","medium","hard"):
    for i in range(16):
        seed = 200+i
        grid = gen.generate(seed,i,difficulty=band)
        cases.append(dict(kind="generated", seed=seed,sample_index=i,difficulty=band,overrides={},
                          self_check=gen.self_check(grid),strict_canonical_like=gen.strict_canonical_like(grid),
                          observed=gen.observe_overrides(grid),radius=support_radius(grid)))
        inputs.append(grid)
canonical = canonical_pairs(TASK,root=REPO,labeled_only=True)
assert len(canonical) == 3
for i,pair in enumerate(canonical):
    inputs.append(pair["input"])
    cases.append(dict(kind="canonical",canonical_pair_index=i,seed=None,sample_index=None,
                      difficulty=None,overrides=None,self_check=gen.self_check(pair["input"]),
                      strict_canonical_like=gen.strict_canonical_like(pair["input"]),radius=support_radius(pair["input"]),
                      canonical_output=pair["output"]))

# Shift the color-3 two-cell blob in canonical train[0] up by one row.
extended = [r[:] for r in canonical[0]["input"]]
assert [(r,c) for r,row in enumerate(extended) for c,v in enumerate(row) if v == 3] == [(1,5),(2,5)]
extended[1][5] = extended[2][5] = 0
extended[0][5] = extended[1][5] = 3
assert gen.self_check(extended) == gen.strict_canonical_like(extended) == []
assert support_radius(extended) == 4
inputs.append(extended)
cases.append(dict(kind="counterexample",origin="canonical train[0]",seed=None,sample_index=None,
                  difficulty=None,overrides=None,mutation="translate color-3 blob one row upward",
                  self_check=gen.self_check(extended),strict_canonical_like=gen.strict_canonical_like(extended),
                  observed=gen.observe_overrides(extended),radius=support_radius(extended)))
assert len(inputs) == 52
for case,grid in zip(cases,inputs):
    case["rival_output"] = local_window_rival(grid)
report = dict(task_id=TASK,generator_version=gen.VERSION,generator_sha256=sha,
              canonical_rule_hash=rule_hash,canonical_rule_raw_sha256=hashlib.sha256(row["program_solution"].encode()).hexdigest(),
              rival="local_window_radius3",cases=cases,
              unique_generated_inputs=len({json.dumps(g) for g in inputs[:48]}),
              sample_count=48,canonical_count=3,counterexample_index=51,
              template_radius_bound=max(max(abs(r),abs(c)) for template in
                  list(gen._CANONICAL_TEMPLATES)+list(gen._TEMPLATES.values()) for r,c in template))
(OUT / "input.json").write_text(json.dumps(inputs)+"\n")
(OUT / "probe.json").write_text(json.dumps(report,separators=(",",":"))+"\n")
print(json.dumps({k:v for k,v in report.items() if k != "cases"},indent=2))
