#!/usr/bin/env python3
"""Deterministic source-bound probes for the two assigned audit targets.

This utility imports only public generator modules from the extracted packet.
It does not import rule runners; Racket outputs are obtained separately through
`python -m arcpuzzles apply` and merged into the retained evidence.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
AUDIT_SEED = "680d214d64458d4ad3efebcc937049db4423b67bb4a2d8ecb4d002ee01ed66a5"
DIFFICULTIES = ("easy", "medium", "hard")
SAMPLES_PER_BAND = 30


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def transpose(grid):
    return [list(col) for col in zip(*grid)]


def rot180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def rot90(grid):
    return [list(row) for row in zip(*reversed(grid))]


def rot270(grid):
    return [list(row) for row in reversed(list(zip(*grid)))]


def flip_h(grid):
    return [list(reversed(row)) for row in grid]


def flip_v(grid):
    return [row[:] for row in reversed(grid)]


def anti_transpose(grid):
    return rot180(transpose(grid))


TRANSFORMS = (
    ("id", lambda x: [row[:] for row in x]),
    ("r1", rot90),
    ("r2", rot180),
    ("r3", rot270),
    ("fh", flip_h),
    ("fv", flip_v),
    ("tr", transpose),
    ("atr", anti_transpose),
)


def split_panels(grid):
    side = len(grid)
    if len(grid[0]) != 4 * side + 3:
        raise AssertionError(f"unexpected panel layout {side}x{len(grid[0])}")
    return [[row[i * (side + 1): i * (side + 1) + side] for row in grid] for i in range(4)]


def merge_conflicts(left, right):
    out = []
    for lrow, rrow in zip(left, right):
        row = []
        for a, b in zip(lrow, rrow):
            if a == 0:
                row.append(b)
            elif b == 0 or a == b:
                row.append(a)
            else:
                row.append(9)
        out.append(row)
    return out


def infer_transform(a, b):
    matches = [name for name, fn in TRANSFORMS if fn(a) == b]
    return matches


def probe_d2() -> dict[str, Any]:
    task_id = "d2f8cb1c91b2"
    gen, path = load_generator(task_id)
    expected_sha = "ea25409ce9949fdc8c0ac94114b2c4d8b4d46aa431036ba2d279b1fe2758f1a5"
    actual_sha = file_sha(path)
    assert actual_sha == expected_sha

    comparisons = 0
    identical = 0
    validator_failures = 0
    pair_relation_counts: dict[str, int] = {}
    for difficulty in DIFFICULTIES:
        for sample_index in range(SAMPLES_PER_BAND):
            tr_grid = gen.generate(AUDIT_SEED, sample_index, difficulty=difficulty, transform="tr")
            atr_grid = gen.generate(AUDIT_SEED, sample_index, difficulty=difficulty, transform="atr")
            comparisons += 1
            identical += int(tr_grid == atr_grid)
            validator_failures += int(bool(gen.self_check(atr_grid, difficulty=difficulty, meta={"transform": "atr"})))
            p0, p1, _, _ = split_panels(atr_grid)
            relation = "+".join(infer_transform(p0, p1)) or "none"
            pair_relation_counts[relation] = pair_relation_counts.get(relation, 0) + 1

    # Independently quantify the separately documented conflict invariant.
    ordinary_draws = 0
    no_conflict_draws = 0
    ambiguous_transform_draws = 0
    conflict_counts_by_band: dict[str, dict[str, int]] = {}
    for difficulty in DIFFICULTIES:
        band_total = 0
        band_zero = 0
        band_ambiguous = 0
        for sample_index in range(100):
            grid = gen.generate(AUDIT_SEED + ":ordinary", sample_index, difficulty=difficulty)
            p0, p1, x, y = split_panels(grid)
            matches = infer_transform(p0, p1)
            # Canonical rule chooses the first match in its fixed order.
            fn = dict(TRANSFORMS)[matches[0]]
            tx = fn(x)
            conflicts = sum(
                1 for r in range(len(tx)) for c in range(len(tx[0]))
                if tx[r][c] != 0 and y[r][c] != 0 and tx[r][c] != y[r][c]
            )
            ordinary_draws += 1
            band_total += 1
            if conflicts == 0:
                no_conflict_draws += 1
                band_zero += 1
            if len(matches) != 1:
                ambiguous_transform_draws += 1
                band_ambiguous += 1
        conflict_counts_by_band[difficulty] = {
            "draws": band_total,
            "no_conflict": band_zero,
            "ambiguous_transform_pair": band_ambiguous,
        }

    sample_index = 0
    difficulty = "hard"
    atr_grid = gen.generate(AUDIT_SEED, sample_index, difficulty=difficulty, transform="atr")
    tr_grid = gen.generate(AUDIT_SEED, sample_index, difficulty=difficulty, transform="tr")
    p0, p1, x, y = split_panels(atr_grid)
    transpose_output = merge_conflicts(transpose(x), y)
    intended_atr_output = merge_conflicts(anti_transpose(x), y)
    assert atr_grid == tr_grid
    assert p1 == transpose(p0)
    assert p1 != anti_transpose(p0)
    assert transpose_output != intended_atr_output
    errs = gen.self_check(atr_grid, difficulty=difficulty, meta={"transform": "atr"})
    assert not errs

    out_dir = PACKET / "checks" / "audit" / task_id
    (out_dir / "input.json").write_text(json.dumps(atr_grid, indent=2) + "\n")
    (out_dir / "rival_output.json").write_text(json.dumps(intended_atr_output, indent=2) + "\n")
    (out_dir / "requested_tr_input.json").write_text(json.dumps(tr_grid, indent=2) + "\n")

    return {
        "schema": "arc-audit-probe-v1",
        "task_id": task_id,
        "generator_sha256": actual_sha,
        "rule_hash": "a401bcfe7b0a",
        "audit_seed": AUDIT_SEED,
        "finding": "advertised transform values tr and atr collapse to the same generator behavior",
        "source_observation": "the atr fallback in _xform_grid computes transpose rather than rotate-180(transpose)",
        "matrix_probe": {
            "difficulties": list(DIFFICULTIES),
            "sample_indices": [0, SAMPLES_PER_BAND - 1],
            "comparisons": comparisons,
            "tr_equals_atr": identical,
            "validator_failures": validator_failures,
            "inferred_pair_relations": pair_relation_counts,
        },
        "secondary_conflict_probe": {
            "seed": AUDIT_SEED + ":ordinary",
            "sample_indices_per_band": [0, 99],
            "draws": ordinary_draws,
            "no_conflict_draws": no_conflict_draws,
            "ambiguous_transform_pair_draws": ambiguous_transform_draws,
            "by_band": conflict_counts_by_band,
            "note": "ordinary sampling does not enforce the stated at-least-one-conflict invariant",
        },
        "counterexample": {
            "difficulty": difficulty,
            "sample_index": sample_index,
            "overrides": {"transform": "atr"},
            "alternate_overrides": {"transform": "tr"},
            "input_path": f"checks/audit/{task_id}/input.json",
            "input_sha256": json_sha(atr_grid),
            "alternate_input_sha256": json_sha(tr_grid),
            "inputs_identical": atr_grid == tr_grid,
            "validator_passes": not errs,
            "documented_generator_domain": True,
            "panel_pair_matches_transpose": p1 == transpose(p0),
            "panel_pair_matches_anti_transpose": p1 == anti_transpose(p0),
            "generator_semantic_output_if_transpose": transpose_output,
            "rival_output_path": f"checks/audit/{task_id}/rival_output.json",
            "rival_description": "output implied by the advertised anti-transpose override",
            "rival_differs": intended_atr_output != transpose_output,
        },
    }


DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def attached_wire(grid):
    h, w = len(grid), len(grid[0])
    marker = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 2)
    starts = []
    for dr, dc in DIRS:
        r, c = marker[0] + dr, marker[1] + dc
        if 0 <= r < h and 0 <= c < w and grid[r][c] == 1:
            starts.append((r, c))
    if len(starts) != 1:
        raise AssertionError(f"expected one attached start, got {starts}")
    q = [starts[0]]
    seen = {starts[0]}
    for r, c in q:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))
    return seen


def probe_5f() -> dict[str, Any]:
    task_id = "5fbb6efffb19"
    gen, path = load_generator(task_id)
    expected_sha = "fec645d1e5c9ba853d4914143a678049e77f6d7b6d090bbe18bd214feb8517d6"
    actual_sha = file_sha(path)
    assert actual_sha == expected_sha

    sample_points = 0
    all_five_identical = 0
    pairwise_comparisons = 0
    pairwise_equal = 0
    validator_failures = 0
    unique_grid_counts: dict[str, list[int]] = {d: [] for d in DIFFICULTIES}
    for difficulty in DIFFICULTIES:
        for sample_index in range(SAMPLES_PER_BAND):
            grids = [gen.generate(AUDIT_SEED, sample_index, difficulty=difficulty, wire_shape=i) for i in range(5)]
            sample_points += 1
            unique = len({json_sha(grid) for grid in grids})
            unique_grid_counts[difficulty].append(unique)
            all_five_identical += int(unique == 1)
            for i in range(5):
                validator_failures += int(bool(gen.self_check(grids[i], difficulty=difficulty, meta={"wire_shape": i})))
                for j in range(i + 1, 5):
                    pairwise_comparisons += 1
                    pairwise_equal += int(grids[i] == grids[j])

    sample_index = 0
    difficulty = "medium"
    grids = [gen.generate(AUDIT_SEED, sample_index, difficulty=difficulty, wire_shape=i) for i in range(5)]
    assert all(grid == grids[0] for grid in grids)
    errs = gen.self_check(grids[0], difficulty=difficulty, meta={"wire_shape": 0})
    assert not errs
    wire_len = len(attached_wire(grids[0]))
    racket_expected = [[6] * wire_len]

    out_dir = PACKET / "checks" / "audit" / task_id
    (out_dir / "input.json").write_text(json.dumps(grids[0], indent=2) + "\n")
    (out_dir / "rival_output.json").write_text(json.dumps(racket_expected, indent=2) + "\n")
    (out_dir / "wire_shape_inputs.json").write_text(json.dumps({str(i): grid for i, grid in enumerate(grids)}, indent=2) + "\n")

    return {
        "schema": "arc-audit-probe-v1",
        "task_id": task_id,
        "generator_sha256": actual_sha,
        "rule_hash": "70de2799de0a",
        "audit_seed": AUDIT_SEED,
        "finding": "advertised exact control wire_shape is not consumed by generate",
        "matrix_probe": {
            "difficulties": list(DIFFICULTIES),
            "sample_indices": [0, SAMPLES_PER_BAND - 1],
            "sample_points": sample_points,
            "all_five_wire_shape_values_identical": all_five_identical,
            "pairwise_comparisons": pairwise_comparisons,
            "pairwise_equal": pairwise_equal,
            "validator_failures": validator_failures,
            "unique_grid_count_range_by_band": {
                band: [min(vals), max(vals)] for band, vals in unique_grid_counts.items()
            },
        },
        "counterexample": {
            "difficulty": difficulty,
            "sample_index": sample_index,
            "overrides": [{"wire_shape": i} for i in range(5)],
            "input_path": f"checks/audit/{task_id}/input.json",
            "all_input_hashes": [json_sha(grid) for grid in grids],
            "all_inputs_identical": True,
            "validator_passes": not errs,
            "documented_generator_domain": True,
            "attached_wire_length": wire_len,
            "rival_output_path": f"checks/audit/{task_id}/rival_output.json",
            "rival_description": "same rule output retained beside the dead-control counterexample; this is a generator-control defect, not a competing solver rule",
        },
    }


def main() -> None:
    reports = {
        "d2f8cb1c91b2": probe_d2(),
        "5fbb6efffb19": probe_5f(),
    }
    for task_id, report in reports.items():
        path = PACKET / "checks" / "audit" / task_id / "probe.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"wrote {path.relative_to(PACKET)}")
    summary = PACKET / "checks" / "audit" / "summary.json"
    summary.write_text(json.dumps(reports, indent=2, sort_keys=True) + "\n")
    print(f"wrote {summary.relative_to(PACKET)}")


if __name__ == "__main__":
    main()
