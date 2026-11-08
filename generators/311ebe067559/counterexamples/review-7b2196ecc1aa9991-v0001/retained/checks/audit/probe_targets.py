#!/usr/bin/env python3
"""Deterministic adversarial probes for the two assigned audit-only generators.

This script imports only the public generator modules and canonical puzzle rows.
It never mutates either audit target.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
AUDIT_SEED = "5953a403a811133c874b93f1fc38ef49278e4e2122fabf4b8fca89f2fd858426"
DIFFICULTIES = ("easy", None, "hard")
BAND_NAME = {"easy": "easy", None: "default", "hard": "hard"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def norm_grid(grid):
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return [[int(v) for v in row] for row in grid]


def canonical_row(task_id: str) -> dict:
    with CANONICAL.open() as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(task_id)


def all_pairs(row: dict) -> list[dict]:
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return list(row.get("train", [])) + list(test)


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


# ---------------------------------------------------------------------------
# 311ebe067559: precedence rays


def ray_analysis_311(grid):
    grid = norm_grid(grid)
    legend = [v for v in grid[0] if v != 0]
    field = [row[:] for row in grid[1:]]
    fh, fw = len(field), len(field[0])
    blockers = {(r, c) for r in range(fh) for c in range(fw) if field[r][c] == 5}

    emitters = []
    for c in range(fw):
        v = field[0][c]
        if v not in (0, 5):
            emitters.append((0, c, v, 1, 0))
    for c in range(fw):
        v = field[fh - 1][c]
        if v not in (0, 5):
            emitters.append((fh - 1, c, v, -1, 0))
    for r in range(1, fh - 1):
        v = field[r][0]
        if v not in (0, 5):
            emitters.append((r, 0, v, 0, 1))
    for r in range(1, fh - 1):
        v = field[r][fw - 1]
        if v not in (0, 5):
            emitters.append((r, fw - 1, v, 0, -1))

    proposals = defaultdict(list)
    for r, c, color, dr, dc in emitters:
        rr, cc = r + dr, c + dc
        while 0 <= rr < fh and 0 <= cc < fw and (rr, cc) not in blockers:
            proposals[(rr, cc)].append(color)
            rr += dr
            cc += dc

    base = [[0 for _ in range(fw)] for _ in range(fh)]
    for r, c in blockers:
        base[r][c] = 5
    for r, c, color, _, _ in emitters:
        base[r][c] = color

    rank = {color: i for i, color in enumerate(legend)}
    intended = [row[:] for row in base]
    first_wins = [row[:] for row in base]
    numeric_max = [row[:] for row in base]
    conflict_cells = []
    for (r, c), colors in proposals.items():
        if base[r][c] != 0:
            continue
        if len(set(colors)) >= 2:
            conflict_cells.append({"r": r, "c": c, "colors": colors[:]})
        intended[r][c] = max(colors, key=lambda x: rank.get(x, -1))
        first_wins[r][c] = colors[0]
        numeric_max[r][c] = max(colors)

    return {
        "legend": legend,
        "field": field,
        "emitters": emitters,
        "proposal_cell_count": len(proposals),
        "conflict_cells": conflict_cells,
        "intended": intended,
        "first_wins": first_wins,
        "numeric_max": numeric_max,
        "first_disagrees": first_wins != intended,
        "numeric_disagrees": numeric_max != intended,
    }


def probe_311(samples_per_band: int) -> dict:
    task_id = "311ebe067559"
    mod, path = load_generator(task_id)
    row = canonical_row(task_id)
    generator_sha = sha256_bytes(path.read_bytes())
    program_sha = sha256_bytes(row["program_solution"].encode())

    canonical = []
    for i, pair in enumerate(all_pairs(row)):
        ana = ray_analysis_311(pair["input"])
        expected = norm_grid(pair["output"])
        canonical.append({
            "pair_index": i,
            "oracle_matches": ana["intended"] == expected,
            "conflict_cell_count": len(ana["conflict_cells"]),
            "first_wins_matches": ana["first_wins"] == expected,
            "numeric_max_matches": ana["numeric_max"] == expected,
        })

    bands = {}
    first_semantically_empty = None
    first_positive = None
    all_records = []
    for difficulty in DIFFICULTIES:
        stats = {
            "samples": samples_per_band,
            "self_check_failures": 0,
            "unique_inputs": set(),
            "with_any_distinct_color_crossing": 0,
            "precedence_changes_first_wins": 0,
            "precedence_changes_numeric_max": 0,
        }
        per_band_records = []
        for i in range(samples_per_band):
            seed = f"{AUDIT_SEED}:311:{BAND_NAME[difficulty]}"
            grid = mod.generate(seed, i, difficulty=difficulty)
            errs = mod.self_check(grid, difficulty=difficulty, meta={})
            if errs:
                stats["self_check_failures"] += 1
            ana = ray_analysis_311(grid)
            key = sha256_json(grid)
            stats["unique_inputs"].add(key)
            if ana["conflict_cells"]:
                stats["with_any_distinct_color_crossing"] += 1
            if ana["first_disagrees"]:
                stats["precedence_changes_first_wins"] += 1
            if ana["numeric_disagrees"]:
                stats["precedence_changes_numeric_max"] += 1
            rec = {
                "difficulty": BAND_NAME[difficulty],
                "seed": seed,
                "sample_index": i,
                "grid": grid,
                "validator_errors": errs,
                "analysis": ana,
            }
            per_band_records.append(rec)
            all_records.append(rec)
            if first_semantically_empty is None and not ana["first_disagrees"] and not ana["numeric_disagrees"]:
                first_semantically_empty = rec
            if first_positive is None and ana["first_disagrees"]:
                first_positive = rec
        # Sequential four-example windows approximate the ordinary lesson policy.
        windows = []
        for start in range(0, max(0, samples_per_band - 3)):
            chunk = per_band_records[start:start + 4]
            demos = chunk[:3]
            query = chunk[3]
            if not any(x["analysis"]["first_disagrees"] for x in demos):
                windows.append({
                    "start": start,
                    "demo_precedence_witnesses": 0,
                    "query_precedence_witness": bool(query["analysis"]["first_disagrees"]),
                })
        stats["unique_inputs"] = len(stats["unique_inputs"])
        stats["four_sample_windows"] = max(0, samples_per_band - 3)
        stats["windows_with_no_first_wins_disagreement_in_three_demos"] = len(windows)
        stats["of_those_query_requires_precedence"] = sum(1 for x in windows if x["query_precedence_witness"])
        stats["first_such_windows"] = windows[:5]
        bands[BAND_NAME[difficulty]] = stats

    # Exact-control probes. The advertised controls are ignored by generate().
    override_seed = f"{AUDIT_SEED}:311:override"
    override_index = 17
    override_pairs = []
    for axis, a, b in [
        ("grid_h", 7, 14),
        ("grid_w", 9, 16),
        ("n", 2, 5),
        ("palette_size", 2, 5),
        ("n_distinct_colors", 2, 5),
    ]:
        ga = mod.generate(override_seed, override_index, **{axis: a})
        gb = mod.generate(override_seed, override_index, **{axis: b})
        override_pairs.append({
            "axis": axis,
            "a": a,
            "b": b,
            "identical": ga == gb,
            "grid_a_shape": [len(ga), len(ga[0])],
            "grid_b_shape": [len(gb), len(gb[0])],
            "grid_hash": sha256_json(ga) if ga == gb else None,
        })
    unknown_override = {"accepted": False, "error": None}
    try:
        mod.generate(override_seed, override_index, definitely_not_an_axis=123)
        unknown_override["accepted"] = True
    except Exception as exc:  # pragma: no cover - evidence capture
        unknown_override["error"] = f"{type(exc).__name__}: {exc}"

    # Pick one ordinary generated input whose output is compatible with rivals.
    chosen = first_semantically_empty or all_records[0]
    chosen_dir = PACKET / "checks/audit/311ebe067559"
    chosen_dir.mkdir(parents=True, exist_ok=True)
    (chosen_dir / "input.json").write_text(json.dumps(chosen["grid"], indent=2) + "\n")
    (chosen_dir / "rival_output.json").write_text(json.dumps({
        "rival": "first proposal wins; legend precedence ignored",
        "output": chosen["analysis"]["first_wins"],
        "matches_independent_authority_oracle": not chosen["analysis"]["first_disagrees"],
    }, indent=2) + "\n")
    (chosen_dir / "generated_sample.json").write_text(json.dumps({
        "task_id": task_id,
        "generator_sha256": generator_sha,
        "declared_rule_hash": getattr(mod, "RULE_HASH", None),
        "canonical_program_sha256": program_sha,
        "seed": chosen["seed"],
        "sample_index": chosen["sample_index"],
        "difficulty": chosen["difficulty"],
        "overrides": {},
        "validator_errors": chosen["validator_errors"],
        "belongs_to_ordinary_generator_domain": True,
        "input_hash": sha256_json(chosen["grid"]),
        "conflict_cells": chosen["analysis"]["conflict_cells"],
        "first_wins_matches_independent_authority_oracle": not chosen["analysis"]["first_disagrees"],
        "numeric_max_matches_independent_authority_oracle": not chosen["analysis"]["numeric_disagrees"],
    }, indent=2) + "\n")

    result = {
        "task_id": task_id,
        "generator_sha256": generator_sha,
        "audit_assignment_generator_sha256": "2b6674e389e68102a1aa93c28a4c52929051e2b7bf36906595682a11d65891a1",
        "generator_hash_matches_assignment": generator_sha == "2b6674e389e68102a1aa93c28a4c52929051e2b7bf36906595682a11d65891a1",
        "declared_rule_hash": getattr(mod, "RULE_HASH", None),
        "canonical_program_sha256": program_sha,
        "samples_per_band": samples_per_band,
        "seed_policy": f"{AUDIT_SEED}:311:<band>",
        "bands": bands,
        "canonical_pairs": canonical,
        "override_pairs": override_pairs,
        "unknown_override": unknown_override,
        "saved_counterexample": {
            "seed": chosen["seed"],
            "sample_index": chosen["sample_index"],
            "difficulty": chosen["difficulty"],
            "input_path": "checks/audit/311ebe067559/input.json",
            "rival_path": "checks/audit/311ebe067559/rival_output.json",
            "metadata_path": "checks/audit/311ebe067559/generated_sample.json",
        },
        "first_positive_precedence_witness": None if first_positive is None else {
            "seed": first_positive["seed"],
            "sample_index": first_positive["sample_index"],
            "difficulty": first_positive["difficulty"],
            "conflict_cell_count": len(first_positive["analysis"]["conflict_cells"]),
        },
    }
    out = PACKET / "checks/audit/311ebe067559/probe.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    return result


# ---------------------------------------------------------------------------
# 34e41cf35fde: lowest red object


def components(grid, color=2):
    grid = norm_grid(grid)
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    out = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                q = (r + dr, c + dc)
                if q in unseen:
                    unseen.remove(q)
                    comp.add(q)
                    stack.append(q)
        out.append(comp)
    return out


def authority_34(grid):
    grid = norm_grid(grid)
    comps = components(grid, 2)
    if not comps:
        return [row[:] for row in grid], None
    def key(comp):
        return (max(r for r, _ in comp), min(r for r, _ in comp), min(c for _, c in comp))
    target = max(comps, key=key)
    out = [row[:] for row in grid]
    for r, c in target:
        out[r][c] = 3
    return out, target


def bottom_two_rival_34(grid):
    grid = norm_grid(grid)
    h = len(grid)
    comps = components(grid, 2)
    touching = [comp for comp in comps if any(r >= h - 2 for r, _ in comp)]
    out = [row[:] for row in grid]
    if len(touching) == 1:
        for r, c in touching[0]:
            out[r][c] = 3
    return out, len(touching)


def probe_34(samples_per_band: int) -> dict:
    task_id = "34e41cf35fde"
    mod, path = load_generator(task_id)
    row = canonical_row(task_id)
    generator_sha = sha256_bytes(path.read_bytes())
    program_sha = sha256_bytes(row["program_solution"].encode())

    canonical = []
    for i, pair in enumerate(all_pairs(row)):
        grid = norm_grid(pair["input"])
        expected = norm_grid(pair["output"])
        intended, target = authority_34(grid)
        rival, touching = bottom_two_rival_34(grid)
        canonical.append({
            "pair_index": i,
            "component_count": len(components(grid)),
            "oracle_matches": intended == expected,
            "target_bottom": max(r for r, _ in target) if target else None,
            "grid_h": len(grid),
            "unique_component_touching_final_two_rows": touching == 1,
            "bottom_two_rival_matches": rival == expected,
        })

    bands = {}
    first = None
    for difficulty in DIFFICULTIES:
        stats = {
            "samples": samples_per_band,
            "self_check_failures": 0,
            "unique_inputs": set(),
            "oracle_has_unique_lowest": 0,
            "target_touches_final_two_rows": 0,
            "unique_component_touches_final_two_rows": 0,
            "bottom_two_rival_matches": 0,
        }
        for i in range(samples_per_band):
            seed = f"{AUDIT_SEED}:34:{BAND_NAME[difficulty]}"
            grid = mod.generate(seed, i, difficulty=difficulty)
            errs = mod.self_check(grid, difficulty=difficulty, meta={})
            if errs:
                stats["self_check_failures"] += 1
            stats["unique_inputs"].add(sha256_json(grid))
            comps = components(grid)
            bottoms = [max(r for r, _ in comp) for comp in comps]
            if bottoms and bottoms.count(max(bottoms)) == 1:
                stats["oracle_has_unique_lowest"] += 1
            intended, target = authority_34(grid)
            rival, touching = bottom_two_rival_34(grid)
            if target and max(r for r, _ in target) >= len(grid) - 2:
                stats["target_touches_final_two_rows"] += 1
            if touching == 1:
                stats["unique_component_touches_final_two_rows"] += 1
            if rival == intended:
                stats["bottom_two_rival_matches"] += 1
            if first is None:
                first = {
                    "difficulty": BAND_NAME[difficulty], "seed": seed,
                    "sample_index": i, "grid": grid, "validator_errors": errs,
                    "intended": intended, "rival": rival,
                }
        stats["unique_inputs"] = len(stats["unique_inputs"])
        bands[BAND_NAME[difficulty]] = stats

    override_seed = f"{AUDIT_SEED}:34:override"
    override_index = 11
    override_results = []
    for axis, value in [("grid_h", 7), ("grid_h", 14), ("grid_w", 7), ("grid_w", 16)]:
        try:
            grid = mod.generate(override_seed, override_index, **{axis: value})
            override_results.append({"axis": axis, "value": value, "accepted": True,
                                     "shape": [len(grid), len(grid[0])], "error": None})
        except Exception as exc:
            override_results.append({"axis": axis, "value": value, "accepted": False,
                                     "shape": None, "error": f"{type(exc).__name__}: {exc}"})
    inert_pairs = []
    for axis, a, b in [("palette_kind", "default", "varied"), ("palette_size", 1, 1)]:
        ga = mod.generate(override_seed, override_index, **{axis: a})
        gb = mod.generate(override_seed, override_index, **{axis: b})
        inert_pairs.append({"axis": axis, "a": a, "b": b, "identical": ga == gb,
                           "grid_hash": sha256_json(ga) if ga == gb else None})
    unknown_override = {"accepted": False, "error": None}
    try:
        mod.generate(override_seed, override_index, definitely_not_an_axis=123)
        unknown_override["accepted"] = True
    except Exception as exc:
        unknown_override["error"] = f"{type(exc).__name__}: {exc}"

    # Validator counterexample: one connected two-cell object is accepted despite
    # the stated >=2-object invariant.
    validator_grid = [[0] * 7 for _ in range(7)]
    validator_grid[2][2] = 2
    validator_grid[2][3] = 2
    validator_errors = mod.self_check(validator_grid, meta={})

    # Task-domain counterexample to the bottom-two shortcut. It obeys the stated
    # background/all-red/unique-lowest invariants but places every object away
    # from the final two rows, which ordinary generation never does.
    counterexample = [[0] * 10 for _ in range(10)]
    for r, c in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        counterexample[r][c] = 2
    for r, c in [(3, 6), (4, 6), (4, 7)]:
        counterexample[r][c] = 2
    for r, c in [(5, 3), (6, 3), (6, 4)]:
        counterexample[r][c] = 2
    counter_errors = mod.self_check(counterexample, meta={})
    intended, target = authority_34(counterexample)
    rival, touching = bottom_two_rival_34(counterexample)
    out_dir = PACKET / "checks/audit/34e41cf35fde"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "input.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    (out_dir / "rival_output.json").write_text(json.dumps({
        "rival": "recolor the unique red component touching either of the final two rows; otherwise do nothing",
        "output": rival,
        "matches_independent_authority_oracle": rival == intended,
        "components_touching_final_two_rows": touching,
    }, indent=2) + "\n")
    (out_dir / "counterexample.json").write_text(json.dumps({
        "task_id": task_id,
        "generator_sha256": generator_sha,
        "declared_rule_hash": getattr(mod, "RULE_HASH", None),
        "canonical_program_sha256": program_sha,
        "seed": None,
        "sample_index": None,
        "overrides": None,
        "validator_errors": counter_errors,
        "belongs_to_documented_task_domain": True,
        "belongs_to_ordinary_generator_domain": False,
        "reason_not_ordinary_generator_domain": "ordinary generator always places the selected object's bottom on row h-1 or h-2",
        "input_hash": sha256_json(counterexample),
        "authority_target_cells": sorted([list(p) for p in target]) if target else [],
        "bottom_two_rival_matches_independent_authority_oracle": rival == intended,
    }, indent=2) + "\n")
    (out_dir / "validator_counterexample.json").write_text(json.dumps({
        "task_id": task_id,
        "generator_sha256": generator_sha,
        "input": validator_grid,
        "red_component_count": len(components(validator_grid)),
        "red_cell_count": 2,
        "validator_errors": validator_errors,
        "accepted_by_validator": validator_errors == [],
        "violated_stated_invariant": "at least two distinct red objects",
    }, indent=2) + "\n")

    result = {
        "task_id": task_id,
        "generator_sha256": generator_sha,
        "audit_assignment_generator_sha256": "ba87c1ba595b7fdcb1ea6473c9f3db36a2837f6337480081ce605a5e8d94ea20",
        "generator_hash_matches_assignment": generator_sha == "ba87c1ba595b7fdcb1ea6473c9f3db36a2837f6337480081ce605a5e8d94ea20",
        "declared_rule_hash": getattr(mod, "RULE_HASH", None),
        "canonical_program_sha256": program_sha,
        "samples_per_band": samples_per_band,
        "seed_policy": f"{AUDIT_SEED}:34:<band>",
        "bands": bands,
        "canonical_pairs": canonical,
        "override_results": override_results,
        "inert_override_pairs": inert_pairs,
        "unknown_override": unknown_override,
        "validator_counterexample": {
            "path": "checks/audit/34e41cf35fde/validator_counterexample.json",
            "accepted": validator_errors == [],
        },
        "saved_counterexample": {
            "input_path": "checks/audit/34e41cf35fde/input.json",
            "rival_path": "checks/audit/34e41cf35fde/rival_output.json",
            "metadata_path": "checks/audit/34e41cf35fde/counterexample.json",
        },
    }
    out = PACKET / "checks/audit/34e41cf35fde/probe.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples-per-band", type=int, default=1000)
    args = ap.parse_args()
    r311 = probe_311(args.samples_per_band)
    r34 = probe_34(args.samples_per_band)
    summary = {
        "audit_assignment_seed": AUDIT_SEED,
        "samples_per_band": args.samples_per_band,
        "targets": {
            "311ebe067559": r311,
            "34e41cf35fde": r34,
        },
    }
    out = PACKET / "checks/audit/probe_summary.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({
        "311": {
            k: {kk: vv for kk, vv in v.items() if kk not in {"first_such_windows"}}
            for k, v in r311["bands"].items()
        },
        "34": r34["bands"],
        "outputs": str(out.relative_to(PACKET)),
    }, indent=2, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
