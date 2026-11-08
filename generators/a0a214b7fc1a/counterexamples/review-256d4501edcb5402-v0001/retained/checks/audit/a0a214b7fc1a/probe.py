"""Focused, source-bound audit; run through the packet's review.py run wrapper.

All authored evidence stays beside this script. No generator is modified.
Canonical labels below are executed through the packet's protected Racket bridge.
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
REPO = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
TASK = "a0a214b7fc1a"
sys.path.insert(0, str(REPO / "shared/runtime"))

from reviewer_support import load_selected_generator, normalize_grid
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_grid(grid):
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def write(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2) + "\n")


def rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotations(grid):
    variants = [grid]
    for _ in range(3):
        variants.append(rotate(variants[-1]))
    return variants


def rotation_count(grid):
    return len({tuple(map(tuple, g)) for g in rotations(grid)})


def tile_rule(grid, *, omit_top_left_half_turn=False):
    """Explicit rival/interpretation, never used as the authoritative label."""
    n = len(grid)
    original, clockwise, half_turn, counterclockwise = rotations(grid)
    quadrants = [
        [original if omit_top_left_half_turn else half_turn, clockwise],
        [counterclockwise, original],
    ]
    return [[quadrants[r // (2*n)][c // (2*n)][r % n][c % n]
             for c in range(4*n)] for r in range(4*n)]


def first_difference(left, right):
    for r, row in enumerate(left):
        for c, cell in enumerate(row):
            if right[r][c] != cell:
                return {"row": r, "column": c, "reference": cell,
                        "rival": right[r][c]}
    return None


def main():
    started = time.monotonic()
    module, source_path, source_hash = load_selected_generator(TASK, root=REPO)
    ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    selected = []
    for raw_line in ledger.open():
        row = json.loads(raw_line)
        if row.get("task_id") == TASK:
            selected.append((row, raw_line.encode()))
    if len(selected) != 1:
        raise AssertionError(f"Expected one canonical record, got {len(selected)}")
    canonical, canonical_bytes = selected[0]
    rule = canonical["program_solution"]
    if not strip_rule_wrapper(rule).lstrip().startswith("(lambda (g)"):
        raise AssertionError("This direct bridge probe requires the canonical native lambda")
    authority = REPO / "shared/data/base/solutions/training/cf5fd0ad__a0a214b7fc1a.json"
    report = {
        "schema": "arcpuzzles-focused-audit-v1", "task_id": TASK,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "wrapper_argv": ["WORK/.venv/bin/python", "review.py", "run",
                         "../.venv/bin/python", "../checks/audit/a0a214b7fc1a/probe.py"],
        "wrapper_cwd": str(REPO.parent.parent), "payload_argv": sys.argv,
        "payload_cwd": str(REPO), "python_executable": sys.executable,
        "python_version": sys.version,
        "probe_sha256": sha_bytes(Path(__file__).read_bytes()),
        "generator_path": str(source_path.relative_to(REPO)),
        "generator_sha256": source_hash,
        "canonical_ledger_path": str(ledger.relative_to(REPO)),
        "canonical_record_sha256": sha_bytes(canonical_bytes),
        "canonical_rule_sha256": sha_bytes(rule.encode()),
        "selected_authority_path": str(authority.relative_to(REPO)),
        "selected_authority_sha256": sha_bytes(authority.read_bytes()),
    }

    bands = ("easy", "medium", "hard")
    census = {"seed": 0, "sample_indices": [0, 255],
              "samples_per_band": 256, "bands": {}}
    default_witnesses = []
    for band in bands:
        counts = collections.Counter()
        failures = []
        half_turn_indices = []
        witness = None
        for index in range(256):
            grid = module.generate(0, index, difficulty=band)
            check = module.self_check(grid, difficulty=band)
            if check:
                failures.append({"sample_index": index, "reasons": check})
            count = rotation_count(grid)
            counts[count] += 1
            if count == 2:
                half_turn_indices.append(index)
            if count < 4 and witness is None:
                witness = {"seed": 0, "sample_index": index,
                           "difficulty": band, "overrides": {}, "input": grid,
                           "input_sha256": sha_grid(grid), "unique_rotations": count,
                           "self_check": check}
        census["bands"][band] = {
            "unique_rotation_counts": dict(counts),
            "half_turn_symmetric_sample_indices": half_turn_indices,
            "self_check_failures": failures,
        }
        if witness is not None:
            default_witnesses.append(witness)
    report["default_census"] = census

    # A finite paired perturbation plus source reading establishes the inert axis.
    fg_pairs = []
    first_fg = None
    for band in bands:
        for seed in range(4):
            for index in range(16):
                low = module.generate(seed, index, difficulty=band, fg_density=0.1)
                high = module.generate(seed, index, difficulty=band, fg_density=1.0)
                equal = low == high
                fg_pairs.append(equal)
                if first_fg is None:
                    first_fg = {"seed": seed, "sample_index": index,
                                "difficulty": band, "low_override": {"fg_density": 0.1},
                                "high_override": {"fg_density": 1.0},
                                "low_input": low, "high_input": high,
                                "low_input_sha256": sha_grid(low),
                                "high_input_sha256": sha_grid(high), "equal": equal}
    report["fg_density_paired_probe"] = {
        "seeds": [0, 1, 2, 3], "sample_indices": [0, 15], "bands": list(bands),
        "pairs": len(fg_pairs), "identical_pairs": sum(fg_pairs),
        "first_witness": first_fg,
    }

    override_cases = []
    for band in bands:
        for axis, values in (("palette_size", (2, 3, 4, 5, 6)),
                             ("grid_n", (3, 4, 5, 6, 7))):
            for value in values:
                row = {"seed": 0, "sample_index": 0, "difficulty": band,
                       "overrides": {axis: value}}
                try:
                    grid = module.generate(0, 0, difficulty=band, **row["overrides"])
                    row.update(status="accepted", input_sha256=sha_grid(grid),
                               dimensions=[len(grid), len(grid[0])],
                               self_check=module.self_check(grid, difficulty=band))
                except Exception as exc:
                    row.update(status="rejected", exception_type=type(exc).__name__,
                               message=str(exc))
                override_cases.append(row)
    report["advertised_integer_domains"] = override_cases
    base = module.generate(0, 0, difficulty="easy")
    typo = module.generate(0, 0, difficulty="easy", __audit_unknown_axis__=123)
    report["unknown_axis"] = {
        "seed": 0, "sample_index": 0, "difficulty": "easy",
        "overrides": {"__audit_unknown_axis__": 123}, "status": "accepted",
        "identical_to_baseline": typo == base, "input_sha256": sha_grid(typo),
    }

    # An ordinary advertised texture with asymmetry_force=True can supply a
    # complete consecutive 3-demo/1-query lesson that leaves a rotation unresolved.
    lesson_overrides = {"texture": "stripes", "palette_size": 2,
                        "bg_density": 0.0, "noise_overlay": 0.0,
                        "asymmetry_force": True}
    candidates = [module.generate(0, i, difficulty="easy", **lesson_overrides)
                  for i in range(515)]
    lesson_start = next((i for i in range(512)
                         if all(rotation_count(g) == 2 for g in candidates[i:i+3])
                         and rotation_count(candidates[i+3]) == 4), None)
    lesson = None
    if lesson_start is not None:
        lesson = {"seed": 0, "start_sample_index": lesson_start,
                  "difficulty": "easy", "overrides": lesson_overrides,
                  "n_train": 3, "n_test": 1, "pairs": []}
        for offset in range(4):
            grid = candidates[lesson_start + offset]
            lesson["pairs"].append({
                "split": "train" if offset < 3 else "test",
                "sample_index": lesson_start + offset, "input": grid,
                "input_sha256": sha_grid(grid), "unique_rotations": rotation_count(grid),
                "self_check": module.self_check(grid, difficulty="easy"),
            })
    report["consecutive_lesson_search"] = {
        "seed": 0, "difficulty": "easy", "candidate_starts": [0, 511],
        "overrides": lesson_overrides, "first_found_start": lesson_start,
    }

    existing = module.generate(0, 0, difficulty="easy", grid_n=3,
                               palette_size=2, texture="full_4fold_sym")
    repeated_existing = {
        "seed": 0, "sample_index": 0, "difficulty": "easy",
        "overrides": {"grid_n": 3, "palette_size": 2, "texture": "full_4fold_sym"},
        "input": existing, "unique_rotations": rotation_count(existing),
        "self_check": module.self_check(existing, difficulty="easy"),
        "existing_review_status": "same-source needs_triage finding independently reproduced",
    }

    canonical_checks = []
    with RacketBridge(timeout=15.0) as bridge:
        # The source is the selected canonical native lambda, not a Python labeler.
        bridge.eval_text(f"(define audit_rule {strip_rule_wrapper(rule)})")

        def label(grid):
            bridge.define_grid("audit_input", grid)
            return bridge.eval_text("(audit_rule audit_input)")

        for split in ("train", "test"):
            for index, pair in enumerate(canonical.get(split, [])):
                grid = normalize_grid(pair["input"])
                output = label(grid)
                expected = normalize_grid(pair["output"]) if "output" in pair else None
                canonical_checks.append({
                    "split": split, "pair_index": index, "input_sha256": sha_grid(grid),
                    "unique_rotations": rotation_count(grid), "output_sha256": sha_grid(output),
                    "matches_saved_output": output == expected if expected is not None else None,
                    "matches_explicit_tile_interpretation": output == tile_rule(grid),
                })
        for witness in default_witnesses:
            output = label(witness["input"])
            witness.update(output=output, output_sha256=sha_grid(output),
                           output_dimensions=[len(output), len(output[0])],
                           omitted_half_turn_rival_fits=(
                               output == tile_rule(witness["input"], omit_top_left_half_turn=True)))
        repeated_existing["output"] = label(existing)
        repeated_existing["output_sha256"] = sha_grid(repeated_existing["output"])
        if lesson is not None:
            for pair in lesson["pairs"]:
                output = label(pair["input"])
                rival = tile_rule(pair["input"], omit_top_left_half_turn=True)
                pair.update(output=output, output_sha256=sha_grid(output),
                            rival_output=rival, rival_fits=output == rival,
                            first_rival_difference=first_difference(output, rival))
            lesson["rival"] = "omit the top-left quadrant's 180-degree turn; repeat original there"
            lesson["rival_fits_all_train"] = all(p["rival_fits"] for p in lesson["pairs"][:3])
            lesson["rival_changes_query"] = not lesson["pairs"][3]["rival_fits"]

    report["canonical_racket_checks"] = canonical_checks
    report["default_witness_files"] = []
    for witness in default_witnesses:
        name = f"default-{witness['difficulty']}-half-turn.json"
        write(name, witness)
        report["default_witness_files"].append(name)
    write("existing-fourfold-override.json", repeated_existing)
    if lesson is not None:
        write("ambiguous-consecutive-lesson.json", lesson)
        report["lesson_file"] = "ambiguous-consecutive-lesson.json"
        report["lesson_rival_fits_all_train"] = lesson["rival_fits_all_train"]
        report["lesson_rival_changes_query"] = lesson["rival_changes_query"]
    report["generator_sha256_after"] = sha_bytes(source_path.read_bytes())
    report["source_unchanged"] = report["generator_sha256_after"] == source_hash
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    assert report["source_unchanged"]
    assert all(row["matches_saved_output"] for row in canonical_checks)
    assert all(row["matches_explicit_tile_interpretation"] for row in canonical_checks)
    assert len(fg_pairs) == 192 and all(fg_pairs)
    assert lesson is not None and lesson["rival_fits_all_train"] and lesson["rival_changes_query"]
    report["exit_code"] = 0
    write("report.json", report)
    print(json.dumps({
        "task_id": TASK, "source_sha256": source_hash,
        "default_half_turn_counts": {b: census["bands"][b]["unique_rotation_counts"].get(2, 0)
                                     for b in bands},
        "default_draws": 768, "fg_density_identical_pairs": sum(fg_pairs),
        "consecutive_ambiguous_lesson_start": lesson_start,
        "canonical_racket_pairs_matched": len(canonical_checks),
        "source_unchanged": report["source_unchanged"], "exit_code": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
