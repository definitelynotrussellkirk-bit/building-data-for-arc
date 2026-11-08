#!/usr/bin/env python3
"""One bounded Racket-backed probe of the four-connected-object shortcut."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import sys
import time

START = time.monotonic()
signal.alarm(110)
OUT = Path(__file__).resolve().parent
WORK = OUT.parents[1]
ROOT = WORK / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_path, canonical_pairs, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def components(grid, connectivity):
    unseen = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color}
    groups = []
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        pending, group = [first], [first]
        while pending:
            r, c = pending.pop()
            for dr, dc in offsets:
                point = r + dr, c + dc
                if point in unseen and grid[point[0]][point[1]] == grid[r][c]:
                    unseen.remove(point)
                    pending.append(point)
                    group.append(point)
        groups.append(sorted(group))
    return sorted(groups)


draw = json.loads((OUT / "draw.json").read_text())
ticket = draw["ticket"]
gen, source_path, source_sha = load_selected_generator(ticket["task_id"], root=ROOT)
assert source_sha == ticket["generator_sha256"]
with canonical_path(ROOT).open() as stream:
    records = [row for line in stream if (row := json.loads(line)).get("task_id") == ticket["rule_task_id"]]
program, = {record["program_solution"] for record in records}
assert sha(" ".join(program.split()).encode())[:12] == ticket["rule_hash"]
assert program.count("(objects-8 g bg)") == 1
rival = program.replace("(objects-8 g bg)", "(objects g bg)")
for name, text in (("reference.rkt", program), ("four-connected-rival.rkt", rival)):
    with (OUT / name).open("x", encoding="utf-8") as stream:
        stream.write(text)

# Minimal foreground witness at the declared 10x10 grid floor: two diagonal
# red cells form one 8-connected irregular object, plus a separate singleton.
# This input is authored, accepted by self_check, and unreachable by generate.
witness = [[0] * 10 for _ in range(10)]
for r, c in ((1, 1), (2, 2)):
    witness[r][c] = 2
witness[1][7] = 9
assert gen.self_check(witness) == []
assert gen.strict_canonical_like(witness) == []
assert len(components(witness, 8)) == 2
assert len(components(witness, 4)) == 3
seed = int(ticket["seed"], 16)
overrides = {"grid_h": 10, "grid_w": 10, "n_objects": 2}
inputs = [gen.generate(seed, index, difficulty="medium", **overrides) for index in range(3)]
assert all(gen.self_check(grid) == [] for grid in inputs)
assert all(components(grid, 4) == components(grid, 8) for grid in inputs)

calls = 0
with RacketBridge(timeout=15.0) as bridge:
    runtime_identity = bridge.runtime_identity
    assert runtime_identity.get("backend") == "racket"
    assert runtime_identity.get("protected") is True

    def evaluate(text, grid):
        global calls
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        result = bridge.eval_text(f"({wrap_rule(text)} {literal})")
        calls += 1
        return result

    canonical_checks = []
    for index, pair in enumerate(canonical_pairs(ticket["rule_task_id"], root=ROOT, labeled_only=True)):
        actual = evaluate(program, pair["input"])
        alternate = evaluate(rival, pair["input"])
        assert actual == alternate == pair["output"], ("canonical", index)
        canonical_checks.append({"index": index, "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"], "reference_matches_retained": True, "rival_matches_retained": True})

    demos = []
    for index, grid in enumerate(inputs):
        actual = evaluate(program, grid)
        alternate = evaluate(rival, grid)
        assert actual == alternate == gen._mirror(grid), ("demo", index)
        demos.append({"input": grid, "output": actual})
    expected = evaluate(program, witness)
    alternate = evaluate(rival, witness)
    assert expected == gen._mirror(witness)
    assert expected != alternate
    assert expected[0][0] == 3 and alternate[0][0] == 0

certificate_errors = gen.lesson_identifiable(demos, {"input": witness})
assert certificate_errors == [], certificate_errors
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_sha
differences = [
    {"row": r, "col": c, "reference": value, "rival": alternate[r][c]}
    for r, row in enumerate(expected) for c, value in enumerate(row) if value != alternate[r][c]
]
save("witness.json", {
    "task_id": ticket["task_id"], "generator_sha256": source_sha,
    "rule_hash": ticket["rule_hash"], "reference_program_sha256": sha(program.encode()),
    "rival_program_sha256": sha(rival.encode()),
    "input_origin": "Hand-authored strict-manifold witness; not constructively generated",
    "input": witness, "reference_output": expected, "rival_output": alternate,
    "components_8": components(witness, 8), "components_4": components(witness, 4),
    "self_check": [], "strict_canonical_like": [],
    "observed_axes": gen.observe_overrides(witness), "difference_count": len(differences),
    "differences": differences,
})
save("lesson.json", {
    "train": demos, "test": [{"input": witness, "output": expected}],
    "generated_demo_call": {"seed_hex": ticket["seed"], "seed_interpretation": "base-16 integer", "sample_indices": [0, 1, 2], "difficulty": "medium", "overrides": overrides},
    "label_basis": "Protected Racket executions for every demonstration and query",
    "query_origin": "Authored counterexample, not generated",
    "lesson_identifiable_errors": certificate_errors,
    "four_connected_rival_fits_all_demos": True,
    "four_connected_rival_changes_query_answer": True,
})
save("probe-result.json", {
    "schema": "reviewer-extra-ticket-probe-v1", "ticket": ticket,
    "status": "finding", "finding": "four_connected_shortcut_uncovered",
    "canonical_checks": canonical_checks, "canonical_pairs": len(canonical_checks),
    "generated_demonstrations": len(demos), "racket_executions": calls,
    "runtime_identity": runtime_identity,
    "reference_program_sha256": sha(program.encode()), "rival_program_sha256": sha(rival.encode()),
    "source_unchanged_before_after": True, "lawful_witness": True,
    "witness_is_generated": False, "query_difference_count": len(differences),
    "lesson_identifiable_errors": certificate_errors,
    "static_support_argument": [
        "Every constructed mask is a solid rectangle, singleton, or four-connected three-cell L; _fit_mask fallback is solid.",
        "Each object occupies one of four zones separated by two empty rows or columns, so different objects cannot meet diagonally.",
        "Therefore four- and eight-connected partitions agree for all generated inputs under the pinned source; this is source reasoning, not a sample census.",
        "The current finite competitor list omits the four-connected rival; accepted lessons refute only its three declared object-selection rivals.",
    ],
    "proposed_repair": "Add a diagonally joined, non-four-connected nonmaroon object to counterexample generation, with a visible Racket-checked output distinction, and include the four-connected rival in demo-only lesson checks.",
    "limits": ["One targeted probe; no full peer suite or census", "No source patch or approval change", "Manual maintainer assessment required for this extra ticket"],
    "probe_seconds": time.monotonic() - START,
    "completed_utc": datetime.now(timezone.utc).isoformat(),
})
signal.alarm(0)
print(json.dumps({"status": "finding", "ticket_id": ticket["ticket_id"], "canonical_pairs": len(canonical_checks), "generated_demos": len(demos), "racket_executions": calls, "query_difference_count": len(differences), "certificate_accepted": not certificate_errors, "probe_seconds": time.monotonic() - START}))
