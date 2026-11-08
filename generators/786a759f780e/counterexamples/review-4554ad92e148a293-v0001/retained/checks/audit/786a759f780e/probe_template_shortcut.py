from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK = "786a759f780e"
ROOT = Path.cwd()
GEN, SOURCE, SHA = load_selected_generator(TASK, root=ROOT)
OUT = ROOT.parent / "checks" / "audit" / TASK

# Memorized ranks for the six shape signatures the generator emits.  This
# deliberately does not inspect zero connectivity or count holes.
PSEUDO_HOLES = {
    (4, 3, 2): 0,
    (8, 3, 3): 1,
    (23, 5, 7): 2,
    (12, 3, 4): 0,
    (13, 3, 5): 2,
    (12, 4, 4): 1,
}

def template_rival(grid):
    analysis = GEN._analyze(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"])
    objects = analysis["facts"]["objects"]
    ordered = sorted(
        objects,
        key=lambda obj: (
            PSEUDO_HOLES.get((obj["area"], obj["height"], obj["width"]), 0),
            obj["area"],
            obj["color"],
        ),
    )
    return GEN._pack_objects(ordered)

samples = []
profile_fingerprints = set()
matches = 0
for band_index, band in enumerate(("easy", "medium", "hard")):
    for i in range(100):
        seed = 81000 + band_index * 10000 + i
        sample_index = i
        grid = GEN.generate(seed, sample_index, difficulty=band)
        analysis = GEN._analyze(grid)
        objects = analysis["facts"]["objects"]
        fingerprint = tuple(sorted((o["area"], o["height"], o["width"]) for o in objects))
        profile_fingerprints.add(fingerprint)
        expected = GEN.rule_mirror(grid)
        rival = template_rival(grid)
        equal = rival == expected
        matches += int(equal)
        samples.append({
            "band": band, "seed": seed, "sample_index": sample_index,
            "fingerprint": fingerprint, "rival_matches": equal,
            "self_check": GEN.self_check(grid),
        })

# Valid for the Racket rule, but intentionally outside the selected generator's
# linked profile grammar: a large solid (0 holes) and a smaller 5x5 ring (1 hole).
grid = [[0] * 20 for _ in range(11)]
for r in range(1, 6):
    for c in range(1, 6):
        grid[r][c] = 4
for r in range(1, 6):
    for c in range(10, 15):
        if r in (1, 5) or c in (10, 14):
            grid[r][c] = 7

(OUT / "counterexample-input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
(OUT / "template-rival-output.json").write_text(json.dumps({"output": template_rival(grid)}, indent=2) + "\n")
report = {
    "schema": "audit-template-shortcut-v1",
    "task_id": TASK,
    "generator_sha256": SHA,
    "sample_count": len(samples),
    "matches": matches,
    "unique_fingerprint_sets": len(profile_fingerprints),
    "fingerprints": sorted(profile_fingerprints),
    "signature_table": {str(k): v for k, v in sorted(PSEUDO_HOLES.items())},
    "counterexample_self_check": GEN.self_check(grid),
    "counterexample_python_rule_differs": GEN.rule_mirror(grid) != template_rival(grid),
    "samples": samples,
}
(OUT / "template-probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: report[k] for k in ("task_id", "generator_sha256", "sample_count", "matches", "unique_fingerprint_sets", "counterexample_self_check", "counterexample_python_rule_differs")}, indent=2))
