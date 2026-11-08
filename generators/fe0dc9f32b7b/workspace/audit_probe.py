#!/usr/bin/env python3
"""Reproduce the two assignment-bound adversarial audit witnesses.

The probe is intentionally source-bound: it hashes and imports the exact audit
subjects named by ``AUDIT_ASSIGNMENT.json``, executes their selected Racket
rules, and writes compact counterexample JSON files.  It does not edit either
audit target.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

WORKSPACE = Path(__file__).resolve().parent
PACKET_ROOT = WORKSPACE.parents[3]
REPO_ROOT = PACKET_ROOT / "repo"
for _path in (REPO_ROOT / "shared/runtime", REPO_ROOT / "src", REPO_ROOT):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)

TARGET_CONTRACT = {
    "9e21d782f5e6": "d57f4a44d412a3fe4ef31c09d913ad686ce1e0f5916bd85c546bd2350ac74fcb",
    "bedcbc1cb6fb": "893ce4c00ef7279f7318641b5c299e8cb04f67ce98da8e2a9ed436f5e50ec440",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator(task_id: str):
    path = REPO_ROOT / "generators" / task_id / "generator.py"
    actual = _sha(path)
    expected = TARGET_CONTRACT[task_id]
    if actual != expected:
        raise RuntimeError(
            f"audit target {task_id} changed: expected {expected}, got {actual}"
        )
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _canonical_row(task_id: str):
    rows = []
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                rows.append(row)
    if not rows:
        raise KeyError(task_id)
    hashes = {
        hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
        for row in rows
    }
    if len(hashes) != 1:
        raise RuntimeError(f"{task_id} has multiple authority rule hashes: {hashes}")
    return rows[0], next(iter(hashes)), len(rows)


def _racket_output(task_id: str, grid):
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    row, _rule_hash, _count = _canonical_row(task_id)
    with tempfile.TemporaryDirectory(prefix=f"audit-{task_id}-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO_ROOT), stage, task_id)
        (stage / "request.json").write_text(
            json.dumps({"program": row["program_solution"], "grid": grid}),
            encoding="utf-8",
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps(runner._apply_rule(bridge, name, request['grid'])))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        return json.loads(result["stdout"])


def _row_major_marker_rival(grid):
    """Wrong Bed rule: use every nonzero/nonblue cell in row-major order."""
    output = [list(row) for row in grid]
    markers = [value for row in grid for value in row if value not in (0, 1)]
    blue = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    row1 = min(row for row, _col in blue) + 1
    row2 = max(row for row, _col in blue) - 1
    col1 = min(col for _row, col in blue) + 1
    col2 = max(col for _row, col in blue) - 1
    for color in markers:
        if row1 > row2 or col1 > col2:
            break
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                output[row][col] = color
        row1 += 1
        row2 -= 1
        col1 += 1
        col2 -= 1
    return output


def _audit_9e(out_dir: Path) -> dict:
    task_id = "9e21d782f5e6"
    module, source = _load_generator(task_id)
    _canonical, authority_hash, row_count = _canonical_row(task_id)
    call = {
        "seed": 0,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"texture": "no_blobs", "grid_h": 10},
    }
    grid = module.generate(
        call["seed"],
        call["sample_index"],
        difficulty=call["difficulty"],
        **call["overrides"],
    )
    actual = _racket_output(task_id, grid)

    try:
        generated = module.generate(0, 0, difficulty="easy", grid_h=10)
        advertised = {"accepted": True, "shape": [len(generated), len(generated[0])]}
    except Exception as exc:  # evidence records the exact public behavior
        advertised = {"accepted": False, "exception": f"{type(exc).__name__}: {exc}"}
    try:
        generated = module.generate(
            0, 0, difficulty="easy", definitely_unknown=17
        )
        unknown = {
            "accepted": True,
            "shape": [len(generated), len(generated[0])],
            "self_check": module.self_check(generated),
        }
    except Exception as exc:
        unknown = {"accepted": False, "exception": f"{type(exc).__name__}: {exc}"}

    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "target_task_id": task_id,
        "finding": "override/domain contract is internally inconsistent",
        "generator_sha256": _sha(source),
        "generator_rule_hash": getattr(module, "RULE_HASH", None),
        "authority_rule_hash": authority_hash,
        "canonical_rows_with_same_rule": row_count,
        **call,
        "exact_input": grid,
        "actual_racket_output": actual,
        "rival_name": "identity_on_empty",
        "rival_output": [list(row) for row in grid],
        "rival_matches_racket": actual == grid,
        "validator_result": module.self_check(
            grid,
            difficulty=call["difficulty"],
            meta={"overrides": call["overrides"]},
        ),
        "observed": {
            "grid_h": len(grid),
            "grid_w": len(grid[0]),
            "nonzero_cells": sum(value != 0 for row in grid for value in row),
        },
        "declared_axes": module.AXES,
        "additional_exact_checks": {
            "advertised_grid_h_10_without_texture": advertised,
            "unknown_override_definitely_unknown": unknown,
        },
        "replay": {
            "cwd": "packet_root",
            "argv": [
                "python3",
                "run_with_racket.py",
                "python3",
                "generators/fe0dc9f32b7b/workspace/audit_probe.py",
                "--out-dir",
                "checks",
            ],
        },
        "interpretation": (
            "The combined call is accepted but grid_h is ignored, a fixed 7x9 "
            "empty grid is emitted, and self_check rejects it. Separately, the "
            "advertised-valid grid_h=10 is rejected in easy mode and an unknown "
            "override key is accepted."
        ),
    }
    path = out_dir / "audit-9e21d782f5e6-counterexample.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _audit_bed(out_dir: Path) -> dict:
    task_id = "bedcbc1cb6fb"
    module, source = _load_generator(task_id)
    _canonical, authority_hash, row_count = _canonical_row(task_id)
    call = {
        "seed": 123,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {
            "scene_profile": "two_markers_10x10",
            "layout_variant": "canonical",
        },
    }
    base = module.generate(
        call["seed"],
        call["sample_index"],
        difficulty=call["difficulty"],
        **call["overrides"],
    )
    base_actual = _racket_output(task_id, base)
    base_rival = _row_major_marker_rival(base)

    witness = [list(row) for row in base]
    witness[0][1] = 9
    actual = _racket_output(task_id, witness)
    rival = _row_major_marker_rival(witness)
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "target_task_id": task_id,
        "finding": (
            "declared rule has no generated distinction from row-major marker "
            "collection; off-diagonal distractors are outside the calibrated "
            "validator domain"
        ),
        "generator_sha256": _sha(source),
        "generator_rule_hash": getattr(module, "RULE_HASH", None),
        "authority_rule_hash": authority_hash,
        "canonical_rows_with_same_rule": row_count,
        **call,
        "base_generated_input": base,
        "base_actual_racket_output": base_actual,
        "base_rival_output": base_rival,
        "base_rival_matches_racket": base_rival == base_actual,
        "exact_input": witness,
        "mutation": {
            "row": 0,
            "col": 1,
            "value": 9,
            "purpose": (
                "off-diagonal distractor before the second diagonal marker in "
                "row-major order"
            ),
        },
        "actual_racket_output": actual,
        "rival_name": "collect_all_nonzero_nonblue_row_major_then_fill",
        "rival_output": rival,
        "rival_matches_racket": rival == actual,
        "validator_result": module.self_check(
            witness,
            difficulty=call["difficulty"],
            meta={"overrides": call["overrides"]},
        ),
        "base_validator_result": module.self_check(
            base,
            difficulty=call["difficulty"],
            meta={"overrides": call["overrides"]},
        ),
        "replay": {
            "cwd": "packet_root",
            "argv": [
                "python3",
                "run_with_racket.py",
                "python3",
                "generators/fe0dc9f32b7b/workspace/audit_probe.py",
                "--out-dir",
                "checks",
            ],
        },
        "interpretation": (
            "The target is clean inside its declared calibrated grammar, but every "
            "generated marker is both a diagonal marker and a row-major marker. "
            "The exact off-domain mutation makes the canonical main-diagonal rule "
            "disagree with the plausible row-major shortcut. A semantic witness "
            "contract would make this teaching limitation explicit."
        ),
    }
    path = out_dir / "audit-bedcbc1cb6fb-shortcut.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="directory for the two compact audit JSON reports",
    )
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_9e = _audit_9e(out_dir)
    report_bed = _audit_bed(out_dir)
    print(
        json.dumps(
            {
                "status": "passed",
                "9e21d782f5e6": {
                    "validator_result": report_9e["validator_result"],
                    "observed": report_9e["observed"],
                },
                "bedcbc1cb6fb": {
                    "base_rival_matches_racket": report_bed[
                        "base_rival_matches_racket"
                    ],
                    "mutated_rival_matches_racket": report_bed[
                        "rival_matches_racket"
                    ],
                    "validator_result": report_bed["validator_result"],
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
