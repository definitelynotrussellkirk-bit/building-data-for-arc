"""One source-pinned witness against accepting reflection as rotation."""
from pathlib import Path
import hashlib
import json
import sys
import time

START = time.monotonic()
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2] / "repo"
RUNTIME = ROOT / "shared/runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import load_selected_generator, canonical_path
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = "1d26c382ab68"
SOURCE = "7af83faf43c07849c2a1900002e2258846d052d4d9899a5d066658d32f538ac0"
RULE = "e4dd26fbc01b"
SEED_HEX = "c2b3c4e4fff71273834cd96ee04eed703ee141eb7599ee136c13ada32a92347c"
gen, source_path, source_sha = load_selected_generator(TASK, root=ROOT)
assert source_sha == SOURCE, (source_sha, SOURCE)
assert gen.RULE_HASH == RULE
rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
        if line.strip()]
record, = [row for row in rows if row.get("task_id") == TASK]
program = record["program_solution"]
normalized_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
assert normalized_hash == RULE, normalized_hash
grid = gen.generate(int(SEED_HEX, 16), 0, difficulty="medium")
assert gen.self_check(grid) == []

def normalize(cells):
    a = min(r for r,c in cells)
    b = min(c for r,c in cells)
    return tuple(sorted((r-a,c-b) for r,c in cells))

def orbit(shape):
    result = set()
    current = normalize(shape)
    for _ in range(4):
        result.add(current)
        current = normalize([(c,-r) for r,c in current])
    return result

def components(cells):
    unseen = set(cells)
    result = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        group = {first}
        pending = [first]
        while pending:
            r,c = pending.pop()
            for point in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if point in unseen:
                    unseen.remove(point)
                    group.add(point)
                    pending.append(point)
        result.append(group)
    return result

separator, = [r for r,row in enumerate(grid) if all(x == 9 for x in row)]
template = [(r,c) for r in range(separator) for c,x in enumerate(grid[r]) if x == 1]
rotation_orbit = orbit(template)
reflected_orbit = orbit([(r,-c) for r,c in template])
assert not (rotation_orbit & reflected_orbit), "Witness must be chiral"
candidates = components([(r,c) for r in range(separator+1,len(grid))
                         for c,x in enumerate(grid[r]) if x != 0])
assert len(candidates) == 3
rotation_matches = [group for group in candidates if normalize(group) in rotation_orbit]
reflection_matches = [group for group in candidates if normalize(group) in reflected_orbit]
assert len(rotation_matches) == len(reflection_matches) == 1
rival = [row[:] for row in grid]
for group in rotation_matches + reflection_matches:
    for r,c in group:
        rival[r][c] = 2

with RacketBridge(timeout=30.0) as bridge:
    identity = bridge.runtime_identity
    assert identity.get("backend") == "racket" and identity.get("protected") is True
    literal = "'(" + " ".join("(" + " ".join(map(str,row)) + ")" for row in grid) + ")"
    expected = bridge.eval_text(f"({wrap_rule(program)} {literal})")
assert expected == gen.expected_output(grid)
assert rival != expected
changed = [(r,c) for r,row in enumerate(grid) for c,x in enumerate(row) if expected[r][c] != x]
assert set(changed) == rotation_matches[0]
assert all(expected[r][c] == grid[r][c] for r,c in reflection_matches[0])
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == SOURCE

(OUT / "rule.rkt").write_text(program)
witness = {
    "task_id": TASK, "source_path": str(source_path.relative_to(ROOT)),
    "generator_sha256": SOURCE, "rule_hash": RULE,
    "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    "seed_hex": SEED_HEX, "seed_interpretation": "base-16 integer",
    "sample_index": 0, "difficulty": "medium", "overrides": {},
    "shortcut": "accept_reflection_as_rotation", "input": grid,
    "reference_output": expected, "rival_output": rival,
    "rotation_cells": sorted(map(list, rotation_matches[0])),
    "reflection_cells": sorted(map(list, reflection_matches[0])),
    "self_check": [], "runtime_identity": identity,
    "checks": {"pinned_source_before_and_after": True, "canonical_rule_hash": True,
               "lawful_generated_input": True, "racket_equals_python_claim": True,
               "reflection_preserved_by_reference": True, "shortcut_disagrees": True},
    "probe_seconds": time.monotonic()-START,
    "limits": "One generated scene and one rival; no lesson census, safety approval, or broad shortcut claim."
}
(OUT / "witness.json").write_text(json.dumps(witness, indent=2) + "\n")
print(json.dumps({"status": "completed", "shortcut": witness["shortcut"],
                  "rotation_cells": len(rotation_matches[0]),
                  "reflection_cells": len(reflection_matches[0]),
                  "source_sha256": SOURCE, "probe_seconds": witness["probe_seconds"]}))
