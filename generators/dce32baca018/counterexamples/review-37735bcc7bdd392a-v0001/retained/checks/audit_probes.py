#!/usr/bin/env python3
"""Racket-backed adversarial evidence for the two assigned audit targets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

PACKET = Path(__file__).resolve().parents[1]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "src"))

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime

TARGETS = ("dce32baca018", "ed55b2928ac3")
COMMAND = [
    "python3", "run_with_racket.py", "python3", "../checks/audit_probes.py"
]


def norm_grid(grid: Any) -> list[list[int]]:
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(v) for v in row] for row in grid]
    return [list(row) for row in grid]


def canonical_record(task_id: str) -> dict[str, Any]:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def canonical_pairs(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(record.get("train") or [])
    test = record.get("test")
    if isinstance(test, dict):
        rows.append(test)
    elif isinstance(test, list):
        rows.extend(test)
    return [
        {"input": norm_grid(pair["input"]), "output": norm_grid(pair["output"])}
        for pair in rows
    ]


def crop_without_key(grid: list[list[int]]) -> list[list[int]]:
    work = [row[:] for row in grid]
    work[0][0] = 0
    cells = [(r, c) for r, row in enumerate(work) for c, v in enumerate(row) if v]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in work[r0:r1 + 1]]


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def flip_lr(grid):
    return [row[::-1] for row in grid]


def flip_ud(grid):
    return [row[:] for row in grid[::-1]]


def key_class(key: int) -> str:
    return {1: "cw", 2: "r180", 3: "lr", 4: "ud"}.get(key, "identity")


def intended_python(grid):
    key = grid[0][0]
    crop = crop_without_key(grid)
    return {
        "cw": rotate_cw,
        "r180": rotate_180,
        "lr": flip_lr,
        "ud": flip_ud,
        "identity": lambda value: [row[:] for row in value],
    }[key_class(key)](crop)


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    catalog = Catalog(REPO)
    assignment = json.loads((PACKET / "AUDIT_ASSIGNMENT.json").read_text())
    expected = {row["task_id"]: row["generator_sha256"] for row in assignment["targets"]}

    with tempfile.TemporaryDirectory(prefix="audit-probes-") as directory:
        stage = Path(directory)
        prepare_runtime(catalog, stage, task_ids=list(TARGETS))
        sys.path.insert(0, str(stage))
        from puzzle_generators import runner

        bundles = {task: runner._load_bundle(task) for task in TARGETS}
        bridges = {}
        try:
            for task, bundle in bundles.items():
                bridges[task] = runner._open_bridge_with_rule(bundle.rule_callable_text)

            # dce32baca018: exact right-origin input, which the bidirectional
            # Racket rule mirrors left but the generator's one-way curriculum
            # and a left-to-right-only rival do not.
            task = "dce32baca018"
            bundle = bundles[task]
            bridge, fn_name = bridges[task]
            gen = bundle.generator_module
            inp = [[0] * 7 for _ in range(5)]
            for r in range(5):
                inp[r][3] = 5
            inp[1][5] = 4
            actual = runner._apply_rule(bridge, fn_name, inp)
            rival = [row[:] for row in inp]
            # Left-to-right-only completion: there are no left source cells,
            # so the input is returned unchanged.
            census = {band: {"draws": 0, "right_source_nonzero": 0}
                      for band in ("easy", "medium", "hard")}
            for band in census:
                for index in range(100):
                    grid = gen.generate(700000 + index, index, difficulty=band)
                    div = len(grid[0]) // 2
                    census[band]["draws"] += 1
                    census[band]["right_source_nonzero"] += int(any(
                        grid[r][c] not in (0, 5)
                        for r in range(len(grid))
                        for c in range(div + 1, len(grid[0]))
                    ))
            source = REPO / f"generators/{task}/generator.py"
            result_dce = {
                "schema": "arcpuzzles-audit-counterexample-v1",
                "finding_type": "generated-curriculum directional shortcut",
                "task_id": task,
                "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "assigned_generator_sha256": expected[task],
                "rule_hash": catalog.describe(task)["rule_hash"],
                "seed": None,
                "sample_index": None,
                "overrides": {},
                "input": inp,
                "actual_racket_output": actual,
                "rival_name": "copy_left_to_right_only",
                "rival_output": rival,
                "outputs_disagree": actual != rival,
                "target_self_check": list(gen.self_check(inp)),
                "documented_rule_domain": (
                    "One centered full-height gray divider with a colored source cell "
                    "on the right; valid for the canonical bidirectional symmetry rule, "
                    "but intentionally outside this generator's left-only invariant."
                ),
                "finite_generator_census": census,
                "command": COMMAND,
                "cwd": "packet_root",
                "scope": "300 finite draws plus one exact Racket-backed counterexample; not universal proof.",
            }
            if not result_dce["outputs_disagree"]:
                raise AssertionError("dce counterexample did not distinguish rival")
            write(PACKET / "checks/audit_dce32baca018.json", result_dce)

            # ed55b2928ac3: reproduce canonical-domain rejection and find an
            # actual 3-demo lesson whose unseen query key class is compatible
            # with a default-identity rival.
            task = "ed55b2928ac3"
            bundle = bundles[task]
            bridge, fn_name = bridges[task]
            gen = bundle.generator_module
            canon = canonical_pairs(canonical_record(task))
            canonical_checks = []
            for index, pair in enumerate(canon):
                racket = runner._apply_rule(bridge, fn_name, pair["input"])
                canonical_checks.append({
                    "index": index,
                    "self_check": list(gen.self_check(pair["input"])),
                    "racket_matches_stored": racket == pair["output"],
                    "input": pair["input"],
                    "actual_racket_output": racket,
                })

            override_evidence: dict[str, Any] = {}
            key_grid = gen.generate(0, 0, key=1)
            override_evidence["key_equals_1"] = {
                "requested": 1,
                "observed": key_grid[0][0],
                "honored": key_grid[0][0] == 1,
            }
            size_grid = gen.generate(0, 0, blob_size=3)
            observed_size = sum(
                value != 0 for r, row in enumerate(size_grid)
                for c, value in enumerate(row) if (r, c) != (0, 0)
            )
            override_evidence["blob_size_equals_3"] = {
                "requested": 3,
                "observed": observed_size,
                "honored": observed_size == 3,
            }
            try:
                gen.generate(0, 0, typo_axis=123)
                unknown = "accepted"
            except Exception as exc:
                unknown = f"rejected: {type(exc).__name__}: {exc}"
            override_evidence["unknown_override"] = unknown
            try:
                gen.generate(0, 0, grid_h=6, grid_w=6)
                boundary = "accepted"
            except Exception as exc:
                boundary = f"rejected: {type(exc).__name__}: {exc}"
            override_evidence["declared_valid_6x6"] = boundary

            ambiguous = None
            for seed in range(100):
                instance = runner.run_one(
                    task, seed=seed, sample_index=0, n_train=3, n_test=1,
                    difficulty="medium", bundle=bundle, bridge=bridge, fn_name=fn_name,
                )
                demo_classes = {key_class(pair["input"][0][0]) for pair in instance["train"]}
                query = instance["test"][0]
                q_class = key_class(query["input"][0][0])
                if q_class == "identity" or q_class in demo_classes:
                    continue

                def rival_solver(grid):
                    cls = key_class(grid[0][0])
                    crop = crop_without_key(grid)
                    if cls not in demo_classes:
                        return [row[:] for row in crop]
                    return intended_python(grid)

                demo_matches = [
                    rival_solver(pair["input"]) == pair["output"]
                    for pair in instance["train"]
                ]
                rival_query = rival_solver(query["input"])
                if all(demo_matches) and rival_query != query["output"]:
                    ambiguous = {
                        "seed": seed,
                        "sample_index": 0,
                        "difficulty": "medium",
                        "demo_keys": [pair["input"][0][0] for pair in instance["train"]],
                        "demo_classes": [key_class(pair["input"][0][0]) for pair in instance["train"]],
                        "query_key": query["input"][0][0],
                        "query_class": q_class,
                        "input": query["input"],
                        "actual_racket_output": query["output"],
                        "rival_name": "unseen_key_classes_default_to_identity",
                        "rival_output": rival_query,
                        "rival_fits_all_three_demos": True,
                        "outputs_disagree": True,
                    }
                    break
            if ambiguous is None:
                raise AssertionError("no ed55 ambiguous lesson found in seeds 0..99")

            source = REPO / f"generators/{task}/generator.py"
            result_ed = {
                "schema": "arcpuzzles-audit-counterexample-v1",
                "finding_type": "canonical-domain rejection and lesson ambiguity",
                "task_id": task,
                "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "assigned_generator_sha256": expected[task],
                "rule_hash": catalog.describe(task)["rule_hash"],
                "canonical_pairs_checked": len(canonical_checks),
                "canonical_pairs_rejected_by_self_check": sum(bool(row["self_check"]) for row in canonical_checks),
                "canonical_checks": canonical_checks,
                "override_contract": override_evidence,
                "lesson_counterexample": ambiguous,
                "documented_generator_domain": (
                    "3..6-cell key-disjoint fully asymmetric blobs; this excludes every "
                    "canonical source pair and three random demos cannot cover five transform classes."
                ),
                "command": COMMAND,
                "cwd": "packet_root",
                "scope": "Four canonical pairs and the first distinguishing lesson in seeds 0..99.",
            }
            write(PACKET / "checks/audit_ed55b2928ac3.json", result_ed)
        finally:
            for bridge, _ in bridges.values():
                bridge.shutdown()

    print(json.dumps({
        "dce": str(PACKET / "checks/audit_dce32baca018.json"),
        "ed55": str(PACKET / "checks/audit_ed55b2928ac3.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
