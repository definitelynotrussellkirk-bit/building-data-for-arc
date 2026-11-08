"""Bounded peer learnability probe; labels and rival use protected Racket."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import load_selected_generator
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator

TASK = "630d6cc550e4"
EXPECTED = "bc09219197b55adc2e6a1680b5da303f3bff235d7d3524ad03331e22de50404c"
gen, source, source_hash = load_selected_generator(TASK, root=ROOT)
assert source_hash == EXPECTED, "source changed; reassess before reusing probe"
programs = {v["program_solution"] for v in Catalog(ROOT)._variants()[TASK]}
assert len(programs) == 1
program = programs.pop()
ring = tuple(gen._RING_SOURCE)
zero_checks = " ".join(
    f"(zero? (at g (+ (first blk) {r}) (+ (second blk) {c})))"
    for r, c in ring
)
marker = "blocks))))"
assert program.count(marker) == 1
rival = program.replace(marker, "(filter (lambda (blk) (not (or " + zero_checks + "))) blocks)))))")
assert rival.count("(") == rival.count(")")

def predicts(grid):
    output = [row[:] for row in grid]
    for r, c in gen._detect_blocks(grid):
        if any(grid[r + dr][c + dc] == 0 for dr, dc in ring):
            continue
        for (dr, dc), (sr, sc) in gen._RING_SOURCE.items():
            output[r + dr][c + dc] = grid[r + sr][c + sc]
    return output

selected = None
screen = []
for seed in range(128):
    grids = [gen.generate(seed, index) for index in range(4)]
    assert all(gen.self_check(g) == [] for g in grids)
    assert len({json.dumps(g) for g in grids}) == 4
    agrees = [predicts(g) == gen.rule_mirror(g) for g in grids]
    screen.append({"seed": seed, "sample_indices": [0, 1, 2, 3], "python_screen_agreement": agrees})
    if all(agrees[:3]) and not agrees[3]:
        selected = (seed, grids)
        break

# Even a finite no-finding executes one actual lesson; Python screening is
# candidate discovery only and never the source of retained reference labels.
seed, grids = selected or (0, [gen.generate(0, i) for i in range(4)])
apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
try:
    pairs = [{"sample_index": i, "input": g,
              "output": apply(program, g), "rival_output": apply(rival, g)}
             for i, g in enumerate(grids)]
finally:
    bridge.close()
agreement = [p["output"] == p["rival_output"] for p in pairs]
assert all(p["output"] == gen.rule_mirror(p["input"]) for p in pairs)
finding = all(agreement[:3]) and not agreement[3]
assert finding == (selected is not None)
report = {
    "schema": "arcpuzzles-bounded-peer-learnability-v1", "task_id": TASK,
    "generator_sha256": source_hash, "canonical_rule_hash": gen.RULE_HASH,
    "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
    "canonical_program": program, "rival_program": rival,
    "rival": "skip any detected ring containing black zero; transform other rings canonically",
    "source_binding": "current selected generator and unique catalog canonical rule",
    "schedule": "default difficulty=None, same seed, consecutive sample_index 0..3; first three demos, last query; all pass self_check and are distinct",
    "seed": seed, "screen": screen, "finding": finding,
    "demo_agreement": agreement[:3], "query_agreement": agreement[3:],
    "racket": identity, "racket_evaluations": 8, "pairs": pairs,
    "limits": ["One rival, at most 128 ordinary four-pair lessons screened in Python.",
               "Exactly one four-pair lesson and its rival executed in protected Racket.",
               "No production edits, full battery, acceptance, or training admission."]
}
out = Path(__file__).with_name("result.json")
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in ("task_id", "seed", "finding", "demo_agreement", "query_agreement", "racket_evaluations")}))
