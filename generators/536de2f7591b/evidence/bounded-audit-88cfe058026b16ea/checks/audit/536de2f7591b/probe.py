"""Bounded read-only audit of target 536de2f7591b; evidence only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from reviewer_support import canonical_pairs, load_selected_generator

TASK = "536de2f7591b"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK
EXPECTED_HASH = "c0f5598cf011e36aa5302bc3fd897c8f3fdc8851e043ccb64d05c4f5065fcf06"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def mirror(grid):
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        green = [c for c, value in enumerate(row) if value == 3]
        if not green:
            continue
        start = min(green)
        left_walls = [c for c in range(start) if row[c] == 8]
        destination = max(left_walls) + 1 if left_walls else 0
        for c in green:
            result[r][c] = 0
        for c in range(destination, destination + len(green)):
            result[r][c] = 3
    return result


def source_hashes():
    return {name: digest(ROOT / "generators" / TASK / name) for name in
            ("generator.py", "notes.md", "evidence/review_index.json")}


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    gen, path, selected_hash = load_selected_generator(TASK, root=ROOT)
    before = source_hashes()
    assert before["generator.py"] == EXPECTED_HASH
    assert gen.VERSION == "3.1.0"
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    save("canonical.json", canonical)
    records, failures, rejected, racket = [], [], [], []

    def generated(label, seed, index, difficulty=None, **overrides):
        call = dict(seed=seed, sample_index=index, difficulty=difficulty, **overrides)
        grid = gen.generate(**call)
        errors = gen.self_check(grid)
        observed = gen.observe_overrides(grid)
        replay_equal = grid == gen.generate(**call)
        exact = all(observed[key] == value for key, value in overrides.items())
        expected = mirror(grid)
        properties = {
            "shape_preserved": len(expected) == len(grid) and len(expected[0]) == len(grid[0]),
            "green_count_preserved": sum(row.count(3) for row in grid) == sum(row.count(3) for row in expected),
            "nonmarker_cells_preserved": all(expected[r][c] == value for r, row in enumerate(grid)
                                             for c, value in enumerate(row) if value not in (0, 3)),
        }
        item = dict(label=label, call=call, profile=gen.schedule_profile(seed, index, difficulty),
                    input=grid, mirror_output=expected, self_check=errors, observed=observed,
                    exact_controls=exact, deterministic_replay=replay_equal, properties=properties,
                    witnesses={name: bool(fn(grid)) for name, fn in gen.SEMANTIC_WITNESSES.items()},
                    rival_disagreements={name: fn(grid) != expected for name, fn in gen.SEMANTIC_RIVALS.items()})
        records.append(item)
        if errors or not replay_equal or not exact or not all(properties.values()):
            failures.append({"kind": "generated_check", "label": label})
        return item

    for seed in (0, 1, 17):
        for difficulty in (None, "easy", "medium", "hard"):
            for index in range(4):
                item = generated(f"default_s{seed}_d{difficulty}_p{index}", seed, index, difficulty)
                if index == 0 and gen.strict_canonical_like(item["input"]):
                    failures.append({"kind": "default_canonical_profile", "label": item["label"]})
                expected_witnesses = {1: ("moving_interior", "path_distractor"),
                                      2: ("path_distractor", "wide_block"),
                                      3: ("moving_interior", "wide_block")}.get(index, ())
                if any(not item["witnesses"][name] for name in expected_witnesses):
                    failures.append({"kind": "default_witness", "label": item["label"]})
                if seed == 0 and difficulty is None:
                    racket.append(item)

    endpoints = [("grid_h", v) for v in (5, 18)] + [("grid_w", v) for v in (6, 7, 20)]
    endpoints += [("n_green_rows", v) for v in (1, 6)]
    endpoints += [("max_block_width", v) for v in (1, 3)]
    endpoints += [("n_distractors", v) for v in (0, 3)]
    for seed in (0, 17):
        for index in range(4):
            for axis, value in endpoints:
                item = generated(f"endpoint_s{seed}_p{index}_{axis}{value}", seed, index, None, **{axis: value})
                if seed == 0 and axis == "grid_w" and value == 6:
                    racket.append(item)

    corners = [dict(grid_h=5, grid_w=6, n_green_rows=1, max_block_width=1, n_distractors=0),
               dict(grid_h=18, grid_w=20, n_green_rows=6, max_block_width=3, n_distractors=3),
               dict(grid_h=6, grid_w=7, n_green_rows=6, max_block_width=3, n_distractors=3)]
    for difficulty in ("easy", "hard"):
        for index in range(4):
            for number, overrides in enumerate(corners):
                item = generated(f"corner_d{difficulty}_p{index}_c{number}", 17, index, difficulty, **overrides)
                if difficulty == "hard" and number == 1:
                    racket.append(item)

    for index in range(4):
        call = dict(seed=0, sample_index=index, grid_h=5, n_green_rows=6)
        try:
            gen.generate(**call)
        except ValueError as exc:
            rejected.append(dict(call=call, error_type=type(exc).__name__, error=str(exc)))
        else:
            failures.append({"kind": "incompatible_override_accepted", "call": call})

    # Bounded four-of-five rotation check against only the three declared rivals.
    rotations = []
    for seed in (0, 17):
        for difficulty in (None, "easy", "hard"):
            for first in range(4):
                grids = [gen.generate(seed, first + k, difficulty=difficulty) for k in range(5)]
                killed = [{name for name, fn in gen.SEMANTIC_RIVALS.items() if fn(grid) != mirror(grid)}
                          for grid in grids]
                for held_out in range(5):
                    covered = set().union(*(names for k, names in enumerate(killed) if k != held_out))
                    missing = sorted(set(gen.SEMANTIC_RIVALS) - covered)
                    rotations.append(dict(seed=seed, difficulty=difficulty, first_index=first,
                                          query_index=held_out, surviving_rivals=missing))
                    if missing:
                        failures.append({"kind": "rival_rotation", **rotations[-1]})

    for i, pair in enumerate(canonical):
        matches = mirror(pair["input"]) == pair["output"]
        if not matches:
            failures.append({"kind": "canonical_mirror_mismatch", "index": i})
        racket.append(dict(label=f"canonical_{i}", input=pair["input"], mirror_output=pair["output"]))

    hand_rows = {
        "interior_right_wall_only": [0, 0, 3, 3, 0, 8],
        "nearest_of_multiple_left_walls": [8, 0, 8, 0, 3, 3, 0],
        "ignore_inert_path_distractor": [0, 0, 0, 4, 3, 3, 3],
        "stationary_adjacent_wall": [0, 8, 3, 3, 3, 0],
        "overlapping_shift": [0, 8, 0, 3, 3, 3],
        "wide_long_shift": [8, 0, 0, 0, 0, 0, 3, 3, 3],
    }
    for label, row in hand_rows.items():
        grid = [row, [8] + [0] * (len(row) - 1)] + [[0] * len(row) for _ in range(3)]
        errors = gen.self_check(grid)
        if errors:
            failures.append({"kind": "hand_domain", "label": label, "errors": errors})
        racket.append(dict(label=f"hand_{label}", input=grid, mirror_output=mirror(grid), self_check=errors))

    save("generated.json", records)
    save("racket-cases.json", racket)
    save("inputs.json", {"inputs": [item["input"] for item in racket]})
    save("rotations.json", rotations)
    summary = dict(task_id=TASK, version=gen.VERSION, source_hashes_before=before,
                   source_hashes_after=source_hashes(), generated_cases=len(records),
                   default_cases=48, endpoint_cases=88, crossed_corner_cases=24,
                   canonical_pairs=len(canonical), incompatible_overrides_rejected=rejected,
                   rotation_holdouts=len(rotations), racket_cases_prepared=len(racket), failures=failures)
    save("probe-summary.json", summary)
    print(json.dumps(summary, indent=2))
    return int(bool(failures) or summary["source_hashes_before"] != summary["source_hashes_after"])


if __name__ == "__main__":
    raise SystemExit(prepare())
