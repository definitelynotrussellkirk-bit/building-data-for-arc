#!/usr/bin/env python3
"""Focused, findings-only audit of the assigned generic emitted-program contract.

Run from WORK using the same isolated Python for wrapper and payload:
  env PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python \
    run_with_racket.py ../.venv-review/bin/python \
    ../checks/audit/generic_dense_field_gen2/audit_probe.py

Writes only beside this script. No canonical rule is assumed for this generic ID.
No private runner functions or blind/solve artifacts are loaded.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
REPO = WORK / "repo"
TASK_ID = "generic_dense_field_gen2"
SEEDS = range(100)
BANDS = ("easy", "medium", "hard")
PARITY_SEEDS = range(8)
PROGRAM = "(rule! (lambda (g) (flip-lr g)))"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def reverse_run_colors(grid):
    """Reverse each row's maximal-run colors but retain the original run lengths."""
    result = []
    for row in grid:
        runs = []
        for color in row:
            if runs and runs[-1][0] == color:
                runs[-1][1] += 1
            else:
                runs.append([color, 1])
        result.append([color for color, (_, length) in zip(
            [item[0] for item in reversed(runs)], runs) for _ in range(length)])
    return result


def half_shift(grid):
    return [row[len(row) // 2:] + row[:len(row) // 2] for row in grid]


def transpose(grid):
    return [list(row) for row in zip(*grid)]


RIVALS = {
    "reverse_run_colors_keep_lengths": reverse_run_colors,
    "half_width_cyclic_shift": half_shift,
    "rotate_180": lambda g: [row[::-1] for row in g[::-1]],
    "flip_ud": lambda g: g[::-1],
    "identity": lambda g: g,
    "transpose": transpose,
    "rotate_cw": lambda g: [row[::-1] for row in transpose(g)],
    "rotate_ccw": lambda g: transpose([row[::-1] for row in g]),
}


def grid_stats(grid):
    h, w = len(grid), len(grid[0])
    frequencies = Counter(v for row in grid for v in row)
    row_bands = 1 + sum(grid[r] != grid[r - 1] for r in range(1, h))
    col_bands = 1 + sum(any(row[c] != row[c - 1] for row in grid) for c in range(1, w))
    return {"shape": (h, w), "colors": len(frequencies),
            "zero_cells": frequencies[0], "area": h * w,
            "row_bands": row_bands, "column_bands": col_bands,
            "nonmodal_density": 1 - max(frequencies.values()) / (h * w)}


def encode_pair(pair, split, index, actual=None, rival=None):
    out = {"split": split, "index": index, "input": pair["input"],
           "generated_output": pair["output"], "input_sha256": digest(pair["input"]),
           "generated_output_sha256": digest(pair["output"])}
    if actual is not None:
        out.update(actual_racket_output=actual, actual_racket_output_sha256=digest(actual),
                   racket_matches_generated=actual == pair["output"])
    if rival is not None:
        prediction = RIVALS[rival](pair["input"])
        out.update(rival=rival, rival_output=prediction,
                   rival_matches_generated=prediction == pair["output"])
    return out


def main():
    started = time.time()
    source_paths = [
        f"generators/{TASK_ID}/generator.py",
        f"generators/{TASK_ID}/notes.md",
        f"generators/{TASK_ID}/SUMMARY.md",
        "shared/runtime/puzzle_generators/base.py",
        "shared/runtime/puzzle_generators/generic/concepts/dense_field/__init__.py",
        "shared/runtime/puzzle_generators/generic/concepts/dense_select/__init__.py",
        "shared/runtime/arc_repl/racket_bridge.py",
        "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
        "src/arcpuzzles/runtime.py", "src/arcpuzzles/worker.py",
    ]
    hashes = {path: file_digest(REPO / path) for path in source_paths}
    source_hash = hashes[source_paths[0]]
    assignment = json.loads((WORK / "AUDIT_ASSIGNMENT.json").read_text())
    assigned = next(row for row in assignment["targets"] if row["task_id"] == TASK_ID)
    assert source_hash == assigned["generator_sha256"], "Assigned source changed"
    identity = {
        "task_id": TASK_ID, "phase": "audit", "source_unchanged": True,
        "generator_sha256": source_hash,
        "audit_assignment_sha256": file_digest(WORK / "AUDIT_ASSIGNMENT.json"),
        "program": PROGRAM, "program_sha256": hashlib.sha256(PROGRAM.encode()).hexdigest(),
        "executed_rule_hash": hashlib.sha256(" ".join(PROGRAM.split()).encode()).hexdigest()[:12],
        "authority": "generic generator's emitted Racket program; not a canonical task row",
        "source_files_sha256": hashes,
        "probe_sha256": file_digest(Path(__file__)),
    }
    save("source_identity.json", identity)

    spec = importlib.util.spec_from_file_location("dense_field_audit_target", REPO / source_paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import validate_grid
    from arc_repl.racket_bridge import RacketBridge

    catalog = Catalog(REPO)
    described = catalog.describe(TASK_ID)
    override_cases = []
    for overrides in ({"gh_0": 12}, {"unknown_axis": 1}, {"palette": [1, 2, 3, 4]}):
        try:
            catalog.generate(TASK_ID, seed=0, count=1, allow_unapproved=True, overrides=overrides)
        except Exception as exc:
            override_cases.append({"overrides": overrides, "exception": type(exc).__name__,
                                   "message": str(exc), "rejected_as_unsupported": isinstance(exc, ValueError)
                                   and "no override axes" in str(exc)})
        else:
            override_cases.append({"overrides": overrides, "rejected_as_unsupported": False})
    for difficulty in ("invalid", 5):
        try:
            catalog.generate(TASK_ID, seed=0, count=1, allow_unapproved=True, difficulty=difficulty)
        except Exception as exc:
            override_cases.append({"difficulty": difficulty, "exception": type(exc).__name__,
                                   "message": str(exc), "rejected_as_unsupported": isinstance(exc, ValueError)})
        else:
            override_cases.append({"difficulty": difficulty, "rejected_as_unsupported": False})
    save("public_contract.json", {**identity, "catalog": {k: described.get(k) for k in
         ("id", "kind", "generator_sha256", "rule_hash", "runtime_generator", "approved", "approval_reasons")},
         "cases": override_cases, "normal_generation": "not invoked; avoids copying a full runtime for direct emitted-program parity",
         "direct_api": "generate_task(seed, *, difficulty='medium'); no override argument",
         "public_assembly_source": "worker.py checks all native pairs, then takes train[:n_train] and test[:n_test]"})

    rows = []
    candidates = []
    parity_inputs = []
    duplicate_inputs = Counter()
    all_shapes = Counter()
    invalid = []
    for band in BANDS:
        metrics = Counter()
        rivals = {name: Counter() for name in RIVALS}
        native_sizes = Counter()
        band_shapes = Counter()
        band_palettes = set()
        nonmodal = []
        for seed in SEEDS:
            task = module.generate_task(seed, difficulty=band)
            assert task["program"] == PROGRAM
            deterministic = module.generate_task(seed, difficulty=band) == task
            metrics["deterministic_replays"] += int(deterministic)
            task_before_check = digest(task)
            errors = module.self_check_task(task)
            check_mutated_task = digest(task) != task_before_check
            if errors or not deterministic or check_mutated_task:
                invalid.append({"seed": seed, "difficulty": band, "errors": errors,
                                "deterministic": deterministic, "self_check_mutated": check_mutated_task})
            native_sizes[(len(task["train"]), len(task["test"]))] += 1
            band_palettes.add(tuple(task["meta"]["palette"]))
            all_pairs = [(split, i, pair) for split in ("train", "test")
                         for i, pair in enumerate(task[split])]
            metrics["within_task_duplicate_pairs"] += len(all_pairs) - len({digest(pair) for _, _, pair in all_pairs})
            for split, index, pair in all_pairs:
                metrics["pairs"] += 1
                try:
                    validate_grid(pair["input"])
                    validate_grid(pair["output"])
                except ValueError as exc:
                    invalid.append({"seed": seed, "difficulty": band, "split": split,
                                    "index": index, "error": str(exc)})
                stats = grid_stats(pair["input"])
                band_shapes[stats["shape"]] += 1
                all_shapes[stats["shape"]] += 1
                metrics["identity_pairs"] += pair["input"] == pair["output"]
                metrics["zero_containing_pairs"] += stats["zero_cells"] > 0
                metrics["max_row_bands"] = max(metrics["max_row_bands"], stats["row_bands"])
                metrics["max_column_bands"] = max(metrics["max_column_bands"], stats["column_bands"])
                metrics[f"color_count_{stats['colors']}"] += 1
                nonmodal.append(stats["nonmodal_density"])
                duplicate_inputs[digest(pair["input"])] += 1
                if seed in PARITY_SEEDS:
                    parity_inputs.append((band, seed, split, index, pair))
            for name, rival in RIVALS.items():
                train_matches = [rival(p["input"]) == p["output"] for p in task["train"]]
                test_matches = [rival(p["input"]) == p["output"] for p in task["test"]]
                stat = rivals[name]
                stat["pair_matches"] += sum(train_matches) + sum(test_matches)
                stat["native_train_consistent"] += all(train_matches)
                stat["native_test_disagreement_after_consistent_train"] += all(train_matches) and not all(test_matches)
                stat["public3_train_consistent"] += all(train_matches[:3])
                stat["public3_query_disagreement_after_consistent_train"] += all(train_matches[:3]) and not test_matches[0]
                for policy, fits, fails in (
                    ("native_all_pairs", all(train_matches), not all(test_matches)),
                    ("public_n_train_3_n_test_1", all(train_matches[:3]), not test_matches[0]),
                ):
                    if fits and fails:
                        candidates.append({"difficulty": band, "seed": seed, "rival": name,
                                           "policy": policy, "task": task,
                                           "train_matches": train_matches, "test_matches": test_matches})
        rows.append({"difficulty": band, "seed_start": 0, "seed_stop_exclusive": 100,
                     "lessons": len(SEEDS), "metrics": dict(metrics),
                     "native_sizes": {f"{a}_train_{b}_test": count for (a, b), count in sorted(native_sizes.items())},
                     "unique_shapes": len(band_shapes), "unique_ordered_palettes": len(band_palettes),
                     "nonmodal_density": {"min": min(nonmodal), "mean": sum(nonmodal) / len(nonmodal), "max": max(nonmodal)},
                     "rivals": {name: dict(stat) for name, stat in rivals.items()}})
        print(f"python sample {band}: {metrics['pairs']} pairs, {len(candidates)} cumulative ambiguous lesson/rival/policy rows", flush=True)

    # Keep one complete native witness per rival. For the public policy, prefer
    # a lesson whose fourth native demonstration was its distinguishing witness.
    selected = []
    seen = set()
    for candidate in sorted(candidates, key=lambda c: (
            c["policy"] != "native_all_pairs",
            all(c["train_matches"]) if c["policy"] != "native_all_pairs" else False,
            c["seed"], c["difficulty"])):
        key = candidate["rival"], candidate["policy"]
        if key not in seen:
            seen.add(key)
            selected.append(candidate)

    # A lawful dense field with irregular rectangular widths, for domain support inspection.
    irregular = [[1] * 3 + [2] * 5 + [3] * 8 for _ in range(16)]
    manual_task = {"program": PROGRAM, "train": [{"input": irregular, "output": [r[::-1] for r in irregular]}],
                   "test": [{"input": irregular, "output": [r[::-1] for r in irregular]}]}
    manual_errors = module.self_check_task(manual_task)
    validate_grid(irregular)

    parity = []
    witnesses = []
    # As in the concept family's documented parity harness, evaluate the emitted
    # lambda on g through RacketBridge. This is equivalent to its rule! registration.
    assert PROGRAM.startswith("(rule! ") and PROGRAM.endswith(")")
    emitted_lambda = PROGRAM[len("(rule! "):-1]
    with RacketBridge() as bridge:
        runtime_identity = bridge.runtime_identity
        def apply_emitted(grid):
            bridge.define_grid("g", grid)
            return bridge.eval_text(f"({emitted_lambda} g)")
        for band, seed, split, index, pair in parity_inputs:
            actual = apply_emitted(pair["input"])
            parity.append({"difficulty": band, "seed": seed, "split": split, "index": index,
                           "input_sha256": digest(pair["input"]), "actual_output_sha256": digest(actual),
                           "generated_output_sha256": digest(pair["output"]), "match": actual == pair["output"]})
        print(f"Racket parity: {sum(row['match'] for row in parity)}/{len(parity)} exact", flush=True)
        for candidate in selected:
            task = candidate["task"]
            count_train = len(task["train"]) if candidate["policy"] == "native_all_pairs" else 3
            count_test = len(task["test"]) if candidate["policy"] == "native_all_pairs" else 1
            evidence = {k: v for k, v in candidate.items() if k != "task"}
            evidence.update(identity=identity, native_n_train=len(task["train"]), native_n_test=len(task["test"]),
                            n_train=count_train, n_test=count_test, generator_self_check_errors=module.self_check_task(task),
                            input_domain="generated, passes public grid validator and generator self_check_task", pairs=[])
            for split, count in (("train", count_train), ("test", count_test)):
                for index, pair in enumerate(task[split]):
                    actual = apply_emitted(pair["input"])
                    encoded = encode_pair(pair, split, index, actual=actual, rival=candidate["rival"])
                    encoded["included_by_policy"] = index < count
                    evidence["pairs"].append(encoded)
            witnesses.append(evidence)
        manual_actual = apply_emitted(irregular)
        manual = {**identity, "construction": "16 equal rows: color 1 width 3; color 2 width 5; color 3 width 8",
                  "generated": False, "seed": None, "sample_index": None, "overrides": None,
                  "self_check_task_errors": manual_errors,
                  "public_grid_validator": "pass",
                  "domain": "16x16, nonzero colors, three large contiguous rectangular regions, LR asymmetric; documented dense-field domain",
                  "generator_support": "outside 2..4 evenly spaced column-band construction",
                  **encode_pair(manual_task["train"][0], "manual", 0, actual=manual_actual,
                                rival="reverse_run_colors_keep_lengths")}
    save("racket_parity.json", {**identity, "runtime_identity": runtime_identity,
         "method": "RacketBridge.define_grid + direct application of emitted lambda, same generic concept parity contract",
         "seed_start": 0, "seed_stop_exclusive": 8, "difficulties": list(BANDS),
         "passed": sum(row["match"] for row in parity), "total": len(parity), "rows": parity})
    save("lesson_witnesses.json", {**identity, "runtime_identity": runtime_identity, "witnesses": witnesses})
    save("irregular_width_witness.json", manual)
    save("probe_results.json", {**identity, "elapsed_seconds": time.time() - started,
         "difficulties_reuse_seeded_latent_partition": True,
         "interpretation": "Python census compares generated labels; only racket_parity.json rows and retained witnesses are Racket-confirmed",
         "declared_CANONICAL_SHORTCUTS": getattr(module, "CANONICAL_SHORTCUTS", None),
         "declared_LESSON_COMPETITORS": getattr(module, "LESSON_COMPETITORS", None),
         "candidates_are_auditor_hypotheses": True,
         "lessons": len(SEEDS) * len(BANDS), "total_pairs": sum(r["metrics"]["pairs"] for r in rows),
         "unique_inputs": len(duplicate_inputs), "duplicate_input_occurrences": sum(v - 1 for v in duplicate_inputs.values()),
         "unique_shapes": len(all_shapes), "invalid": invalid, "bands": rows,
         "ambiguity_rows": [{k: v for k, v in c.items() if k != "task"} for c in candidates],
         "racket_confirmed_retained_witnesses": len(witnesses),
         "racket_parity_passed": sum(row["match"] for row in parity), "racket_parity_total": len(parity),
         "public_override_cases": len(override_cases),
         "public_override_cases_rejected_as_expected": sum(c["rejected_as_unsupported"] for c in override_cases),
         "source_hash_after": file_digest(REPO / source_paths[0]),
         "not_run": ["full battery", "canonical apply for generic ID", "public normal generation runtime copy",
                     "production lesson-census CLI", "query rotations"]})
    print(json.dumps({"lessons": len(SEEDS) * len(BANDS),
                      "pairs": sum(r["metrics"]["pairs"] for r in rows),
                      "invalid": len(invalid), "ambiguous_rival_policy_rows": len(candidates),
                      "retained_racket_witnesses": len(witnesses), "elapsed_seconds": time.time() - started}, sort_keys=True), flush=True)
    assert not invalid
    assert all(row["match"] for row in parity)
    assert all(c["rejected_as_unsupported"] for c in override_cases)
    assert file_digest(REPO / source_paths[0]) == source_hash


if __name__ == "__main__":
    main()
