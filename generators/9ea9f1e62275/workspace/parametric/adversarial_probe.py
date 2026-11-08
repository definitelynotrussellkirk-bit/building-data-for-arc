"""Bounded adversarial probe for the framed-Voronoi metric family.

This tool attacks the declared two-demo lesson, named semantic shortcuts,
matched-input contract, color/axis nuisance controls, count boundaries, and
protected-Racket parity.  It writes one compact JSON receipt and intentionally
contains no public exporter or acceptance logic.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_9ea9_metric_probe_prototype", HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
P = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(P)


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _recolor_input(grid: list[list[int]], mapping: dict[int, int]) -> list[list[int]]:
    return [[mapping.get(value, value) for value in row] for row in grid]


def _difference(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def _expect_error(label: str, function, failures: list[dict[str, Any]]) -> None:
    try:
        function()
    except (TypeError, ValueError):
        return
    except Exception as exc:  # wrong rejection path is still useful evidence
        failures.append({"attack": label, "error": f"unexpected {type(exc).__name__}: {exc}"})
        return
    failures.append({"attack": label, "error": "malformed value was accepted"})


def run(seed_count: int, racket_seeds: list[int]) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 512:
        raise ValueError("seed_count must be an exact integer in 1..512")
    failures: list[dict[str, Any]] = []
    metric_signatures: set[tuple[int, int, int]] = set()
    first_roles: set[str] = set()
    frame_boxes_30: set[tuple[int, int, int, int]] = set()
    checked_scenes = 0
    color_controls = 0
    transpose_controls = 0
    max_retry_observation = 0

    for seed in range(seed_count):
        try:
            minimum = P.build_input_bank(seed, demos=2, queries=4)
            maximum = P.build_input_bank(seed, demos=6, queries=4)
        except Exception as exc:
            failures.append({"seed": seed, "attack": "bank_generation", "error": repr(exc)})
            continue

        if minimum["test"] != maximum["test"]:
            failures.append({"seed": seed, "attack": "demo_count_changed_query_bank"})
        if len({_sha(grid) for grid in maximum["train"] + maximum["test"]}) != 10:
            failures.append({"seed": seed, "attack": "duplicate_input"})
        if set(minimum["query_roles"]) != {"stress30", "thin_wide", "tall_narrow", "boundary_mix"}:
            failures.append({"seed": seed, "attack": "query_role_coverage", "roles": minimum["query_roles"]})
        first_roles.add(minimum["query_roles"][0])

        for metric in P.METRICS:
            survivors = P.metric_survivors(minimum["train"], metric)
            if survivors != [metric]:
                failures.append({"seed": seed, "metric": metric, "attack": "declared_metric_survivor", "survivors": survivors})
            rivals = P.rival_survivors(minimum["train"], metric)
            if rivals:
                failures.append({"seed": seed, "metric": metric, "attack": "named_shortcut_survivor", "survivors": rivals})

        for grid in maximum["train"] + maximum["test"]:
            checked_scenes += 1
            try:
                facts = P._analyze(grid)
            except Exception as exc:
                failures.append({"seed": seed, "attack": "structural_validation", "error": repr(exc)})
                continue
            if any(type(value) is not int for row in grid for value in row):
                failures.append({"seed": seed, "attack": "non_exact_input_cell"})
            outputs = {metric: P.apply_metric(grid, metric) for metric in P.METRICS}
            distances = (
                _difference(outputs["manhattan"], outputs["chebyshev"]),
                _difference(outputs["manhattan"], outputs["euclidean_sq"]),
                _difference(outputs["chebyshev"], outputs["euclidean_sq"]),
            )
            metric_signatures.add(distances)
            r0, c0, r1, c1 = facts["frame_bbox"]
            threshold = max(3, ((r1 - r0 - 1) * (c1 - c0 - 1)) // 50)
            if min(distances) < threshold:
                failures.append({"seed": seed, "attack": "weak_metric_margin", "distances": distances, "threshold": threshold})
            if len(grid) == 30 and len(grid[0]) == 30:
                frame_boxes_30.add(tuple(facts["frame_bbox"]))

            colors = [seed_row[2] for seed_row in facts["seeds"]]
            mapping = dict(zip(colors, reversed(colors)))
            recolored = _recolor_input(grid, mapping)
            for metric in P.METRICS:
                expected = _recolor_input(outputs[metric], mapping)
                actual = P.apply_metric(recolored, metric)
                color_controls += 1
                if actual != expected:
                    failures.append({"seed": seed, "metric": metric, "attack": "color_equivariance"})

                transposed = _transpose(grid)
                expected_transposed = _transpose(outputs[metric])
                actual_transposed = P.apply_metric(transposed, metric)
                transpose_controls += 1
                if actual_transposed != expected_transposed:
                    failures.append({"seed": seed, "metric": metric, "attack": "axis_transpose_equivariance"})

    # Numeric, shape, count, stale-program, duplicate and forged-label attacks.
    _expect_error("bool_seed", lambda: P.generate(True, {"metric": "manhattan"}, 2, 4), failures)
    _expect_error("bool_demos", lambda: P.generate(0, {"metric": "manhattan"}, True, 4), failures)
    _expect_error("short_demos", lambda: P.generate(0, {"metric": "manhattan"}, 1, 4), failures)
    _expect_error("long_demos", lambda: P.generate(0, {"metric": "manhattan"}, 7, 4), failures)
    _expect_error("wrong_query_count", lambda: P.generate(0, {"metric": "manhattan"}, 2, 3), failures)
    _expect_error("extra_setting", lambda: P.program({"metric": "manhattan", "x": 1}), failures)
    _expect_error("unknown_metric", lambda: P.program({"metric": "taxicab"}), failures)

    baseline = P.generate(19, {"metric": "manhattan"}, 2, 4)
    forged = copy.deepcopy(baseline)
    forged["program_solution"] += "\n"
    _expect_error("stale_program", lambda: P.certify(forged), failures)
    forged = copy.deepcopy(baseline)
    forged["test"][0]["input"] = copy.deepcopy(forged["train"][0]["input"])
    forged["test"][0]["output"] = copy.deepcopy(forged["train"][0]["output"])
    _expect_error("duplicate_input", lambda: P.certify(forged), failures)
    forged = copy.deepcopy(baseline)
    frame_cell = next(
        (r, c)
        for r, row in enumerate(forged["train"][0]["output"])
        for c, value in enumerate(row)
        if value == 1
    )
    forged["train"][0]["output"][frame_cell[0]][frame_cell[1]] = True
    _expect_error("bool_output_equal_to_one", lambda: P.certify(forged), failures)
    forged = copy.deepcopy(baseline)
    forged["train"][0]["output"][frame_cell[0]][frame_cell[1]] = 9
    _expect_error("tampered_label", lambda: P.certify(forged), failures)

    racket_pairs = 0
    racket_certificates = 0
    runtime_identity = None
    if racket_seeds:
        with P.RacketRunner() as execute:
            runtime_identity = execute.identity
            for seed in racket_seeds:
                for setting in P.SETTINGS:
                    episode = P.generate(seed, setting, 2, 4)
                    try:
                        certificate = P.certify(episode, execute)
                    except Exception as exc:
                        failures.append({"seed": seed, "settings": setting, "attack": "protected_racket_certificate", "error": repr(exc)})
                        continue
                    racket_certificates += 1
                    racket_pairs += len(episode["train"]) + len(episode["test"])
                    if certificate.get("survivors") != [dict(setting)]:
                        failures.append({"seed": seed, "settings": setting, "attack": "protected_racket_survivors", "certificate": certificate})

    if seed_count >= 12 and len(frame_boxes_30) < 4:
        failures.append({"attack": "fixed_30x30_frame_geometry", "distinct_boxes": len(frame_boxes_30)})
    if seed_count >= 16 and len(first_roles) < 3:
        failures.append({"attack": "query_zero_always_first", "first_roles": sorted(first_roles)})
    if seed_count >= 16 and len(metric_signatures) < seed_count:
        failures.append({"attack": "low_intermediate_spread", "signatures": len(metric_signatures), "seed_count": seed_count})

    return {
        "schema": "9ea9-distance-metric-adversarial-probe-v1",
        "task_id": P.TASK_ID,
        "status": "passed" if not failures else "failed",
        "scope": {
            "seeds": seed_count,
            "demos_per_seed": [2, 6],
            "queries_per_seed": 4,
            "metrics": list(P.METRICS),
            "named_rivals_per_metric": len(P._RIVAL_TIE_POLICIES) + len(P._RIVAL_DISTANCE_KINDS),
            "finite_only": True,
        },
        "counts": {
            "python_scenes": checked_scenes,
            "color_crossed_controls": color_controls,
            "transpose_crossed_controls": transpose_controls,
            "distinct_metric_signatures": len(metric_signatures),
            "distinct_first_query_roles": len(first_roles),
            "distinct_30x30_frame_boxes": len(frame_boxes_30),
            "protected_racket_certificates": racket_certificates,
            "protected_racket_selected_pairs": racket_pairs,
        },
        "runtime_identity": runtime_identity,
        "source_sha256": P.source_hashes(),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=96)
    parser.add_argument("--racket-seed", type=int, action="append", dest="racket_seeds")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.seeds, args.racket_seeds or [])
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["counts"], "out": str(args.out)}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
