#!/usr/bin/env python3
"""Proposed, unapproved selection-metric prototype for e521d16d403e."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs, canonical_path, find_root, normalize_grid,
    public_challenge_bytes, public_challenge_id,
)

TASK_ID = "e521d16d403e"
VERSION = "proposed-selection-metric-v1"
ALLOWED_SELECTION_METRICS = ("occupied_cells", "bbox_area")
DEFAULT_SELECTION_METRIC = "occupied_cells"
CANONICAL_SOURCE_SHA256 = "2119340b5d5b36791ddb26b8488686ab3e370eedcac4069d814914d8bc260cc6"
OCCUPIED_COMPARATOR = "(lambda (a b) (> (obj-size a) (obj-size b)))"
AREA_COMPARATOR = """(lambda (a b)
                         (> (* (+ 1 (- (third (obj-bbox a)) (first (obj-bbox a))))
                               (+ 1 (- (fourth (obj-bbox a)) (second (obj-bbox a)))))
                            (* (+ 1 (- (third (obj-bbox b)) (first (obj-bbox b))))
                               (+ 1 (- (fourth (obj-bbox b)) (second (obj-bbox b)))))))"""


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(OCCUPIED_COMPARATOR) != 1 or AREA_COMPARATOR in source:
        raise ValueError("canonical source does not contain the unique guarded comparator")
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    sources = set()
    for line in canonical_path(root).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
            sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}")
    return _check_canonical_source(sources.pop())


def materialize_rule(selection_metric=DEFAULT_SELECTION_METRIC, *, root=None, source=None) -> str:
    if type(selection_metric) is not str or selection_metric not in ALLOWED_SELECTION_METRICS:
        raise ValueError(f"selection_metric must be one of {ALLOWED_SELECTION_METRICS!r}")
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if selection_metric == DEFAULT_SELECTION_METRIC:
        return canonical
    return canonical.replace(OCCUPIED_COMPARATOR, AREA_COMPARATOR, 1)


def restore_canonical(source: str) -> str:
    if source.count(AREA_COMPARATOR) != 1 or OCCUPIED_COMPARATOR in source:
        raise ValueError("source is not the guarded bbox_area variant")
    return _check_canonical_source(source.replace(AREA_COMPARATOR, OCCUPIED_COMPARATOR, 1))


def _selection_metric(source: str) -> str:
    if _sha256(source) == CANONICAL_SOURCE_SHA256:
        _check_canonical_source(source)
        return "occupied_cells"
    restore_canonical(source)
    return "bbox_area"


def rule_callable(source: str) -> str:
    _selection_metric(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len("(rule!"):-1].strip()
    body = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith(";;")
    ).strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    """Execute the exact materialized Racket rule; there is no Python label mirror."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _render_fixture(fixture_id: str, height: int, width: int, placements) -> dict:
    grid = [[0] * width for _ in range(height)]
    for shape, row0, col0, color in placements:
        for row, values in enumerate(shape):
            for col, value in enumerate(values):
                if not value:
                    continue
                rr, cc = row0 + row, col0 + col
                if not (0 <= rr < height and 0 <= cc < width):
                    raise ValueError(f"fixture {fixture_id} places a cell outside the board")
                if grid[rr][cc] != 0:
                    raise ValueError(f"fixture {fixture_id} has overlapping placements")
                grid[rr][cc] = color
    return {"fixture_id": fixture_id, "input": grid}


def fixtures() -> list[dict]:
    """Four lawful scenes where occupied-cell and bbox-area rankings disagree."""
    asym = [[1, 1, 0], [0, 1, 1]]
    rows = [
        _render_fixture(
            "solid_2x4_vs_cross_3x3", 10, 14,
            [([[1, 1, 1, 1], [1, 1, 1, 1]], 1, 1, 2),
             ([[0, 1, 0], [1, 1, 1], [0, 1, 0]], 5, 9, 3),
             (asym, 7, 2, 4)],
        ),
        _render_fixture(
            "seven_cells_vs_tall_six", 12, 15,
            [([[1, 1, 1], [1, 1, 1], [0, 1, 0]], 1, 1, 5),
             ([[1, 1, 1], [0, 1, 0], [0, 1, 0], [0, 1, 0]], 6, 10, 6),
             (asym, 8, 3, 7)],
        ),
        _render_fixture(
            "wide_eight_vs_tall_six", 12, 16,
            [([[1, 1, 1, 1, 1], [0, 1, 1, 1, 0]], 1, 1, 8),
             ([[0, 1, 0], [1, 1, 1], [0, 1, 0], [0, 1, 0]], 6, 11, 9),
             (asym, 9, 4, 2)],
        ),
        _render_fixture(
            "eleven_cells_area15_vs_ten_area16", 14, 18,
            [([[1, 1, 1, 1, 1], [0, 1, 1, 1, 0], [0, 1, 1, 1, 0]], 1, 1, 3),
             ([[1, 0, 0, 1], [1, 1, 1, 1], [0, 1, 1, 0], [0, 1, 1, 0]], 8, 12, 4),
             (asym, 10, 4, 6)],
        ),
    ]
    return rows


def _validate_seed(seed) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("episode seed must be a literal integer in 0..2**63-1")
    return seed


def parameters_for_seed(seed) -> dict[str, str]:
    _validate_seed(seed)
    return {
        "selection_metric": random.Random(seed).choice(ALLOWED_SELECTION_METRICS)
    }


def _grid_sha256(grid) -> str:
    normalized = normalize_grid(grid)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return _sha256(payload)


def make_episode(seed, *, root=None, bridge: RacketBridge | None = None) -> dict:
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge: RacketBridge) -> dict:
    root = find_root(__file__) if root is None else Path(root)
    canonical = canonical_source(root=root)
    rules = {
        metric: materialize_rule(metric, source=canonical)
        for metric in ALLOWED_SELECTION_METRICS
    }
    fixture_rows = fixtures()
    predictions = {
        metric: [execute_rule(source, row["input"], bridge=bridge) for row in fixture_rows]
        for metric, source in rules.items()
    }
    selected_metric = parameters["selection_metric"]
    selected_outputs = predictions[selected_metric]
    pairs = []
    for fixture, output in zip(fixture_rows, selected_outputs, strict=True):
        pairs.append({
            "fixture_id": fixture["fixture_id"],
            "input": fixture["input"],
            "output": output,
            "input_sha256": _grid_sha256(fixture["input"]),
            "output_sha256": _grid_sha256(output),
        })

    rival_rows, ambiguities = [], []
    for metric in ALLOWED_SELECTION_METRICS:
        train_mismatches = [
            index for index in range(3)
            if predictions[metric][index] != selected_outputs[index]
        ]
        query_mismatches = [0] if predictions[metric][3] != selected_outputs[3] else []
        status = (
            "refuted_by_demonstrations" if train_mismatches
            else "ambiguous_query" if query_mismatches
            else "matches_episode"
        )
        row = {
            "selection_metric": metric,
            "racket_sha256": _sha256(rules[metric]),
            "status": status,
            "demonstration_mismatch_indices": train_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": predictions[metric][:3],
            "query_predictions": predictions[metric][3:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    selected_source = rules[selected_metric]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice(('occupied_cells','bbox_area')) draw before any pair"
        ),
        "input_schedule": [row["fixture_id"] for row in fixture_rows],
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "racket_callable_sha256": _sha256(rule_callable(selected_source)),
        "racket_path": f"private/rules/selection-metric-{selected_metric}.rkt",
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": 8,
    }


def public_filename(episode: dict) -> str:
    """Name exports from visible content, excluding hidden metadata and answers."""
    return f"challenge-{public_challenge_id(episode)}.json"


def public_challenge(episode: dict) -> dict:
    return copy.deepcopy({
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    })


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(seeds, *, out, root=None) -> dict:
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        return _write_evidence(seeds, out=out, root=root)
    except Exception as exc:
        _write_json(out / "failure.json", {
            "status": "error", "error_type": type(exc).__name__,
            "error": str(exc), "seeds": list(seeds),
        })
        raise


def _write_evidence(seeds, *, out: Path, root: Path) -> dict:
    source_path = Path(__file__).resolve()
    test_path = root / f"generators/{TASK_ID}/tests/test_parametric_prototype.py"
    source_rows = []
    for path in (source_path, test_path):
        if path.is_file():
            destination = out / "private/source_snapshot" / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
            source_rows.append({
                "path": str(path.relative_to(root)),
                "sha256": _sha256(path.read_bytes()),
                "snapshot": str(destination.relative_to(out)),
            })

    runtime_rows = []
    for name in (
        "reviewer_support.py",
        "arc_repl/racket_bridge.py",
        "arc_repl/racket_prelude/arc-prelude.rkt",
    ):
        path = root / "shared/runtime" / name
        runtime_rows.append({
            "path": str(path.relative_to(root)),
            "sha256": _sha256(path.read_bytes()),
        })

    canonical = canonical_source(root=root)
    rule_rows = []
    for metric in ALLOWED_SELECTION_METRICS:
        source = materialize_rule(metric, source=canonical)
        path = out / f"private/rules/selection-metric-{metric}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        rule_rows.append({
            "selection_metric": metric,
            "path": str(path.relative_to(out)),
            "sha256": _sha256(source),
            "callable_sha256": _sha256(rule_callable(source)),
        })

    episode_rows, canonical_rows = [], []
    distinct_inputs = set()
    with RacketBridge() as bridge:
        witness = fixtures()[0]
        witness_outputs = {
            metric: execute_rule(materialize_rule(metric, source=canonical),
                                 witness["input"], bridge=bridge)
            for metric in ALLOWED_SELECTION_METRICS
        }
        if len({json.dumps(value) for value in witness_outputs.values()}) != 2:
            raise AssertionError("parameter settings failed to change the witness output")
        _write_json(out / "private/distinguishing_witness.json", {
            "fixture_id": witness["fixture_id"],
            "input": witness["input"],
            "input_sha256": _grid_sha256(witness["input"]),
            "outputs_by_selection_metric": witness_outputs,
            "rules": rule_rows,
        })

        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(canonical, pair["input"], bridge=bridge)
            canonical_rows.append({
                **pair,
                "actual": actual,
                "matches": actual == pair["output"],
                "input_sha256": _grid_sha256(pair["input"]),
                "actual_output_sha256": _grid_sha256(actual),
            })
        _write_json(out / "private/canonical_default_check.json", canonical_rows)
        if not canonical_rows or not all(row["matches"] for row in canonical_rows):
            raise AssertionError("occupied_cells default failed a labeled canonical pair")

        for index, seed in enumerate(seeds):
            episode = make_episode(seed, root=root, bridge=bridge)
            replay = make_episode(seed, root=root, bridge=bridge)
            if episode != replay:
                _write_json(out / f"private/episode-{index:03d}-replay-failure.json", replay)
                raise AssertionError("same-seed episode replay changed")
            public_path = f"public/{public_filename(episode)}"
            private_path = f"private/episode-{index:03d}.json"
            destination = out / public_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(public_challenge_bytes(episode))
            _write_json(out / private_path, episode)
            distinct_inputs.update(
                pair["input_sha256"] for pair in episode["train"] + episode["test"]
            )
            episode_rows.append({
                "seed": seed,
                "parameters": episode["parameters"],
                "public_path": public_path,
                "private_path": private_path,
                "deterministic_replay": True,
                "episode_sha256": _sha256(json.dumps(
                    episode, sort_keys=True, separators=(",", ":")
                )),
                "parameter_rivals": [
                    {key: row[key] for key in (
                        "selection_metric", "status",
                        "demonstration_mismatch_indices", "query_mismatch_indices",
                    )}
                    for row in episode["parameter_rivals"]
                ],
            })

    files = [
        {"path": str(path.relative_to(out)), "sha256": _sha256(path.read_bytes())}
        for path in sorted(out.rglob("*")) if path.is_file()
    ]
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "parameter": {
            "name": "selection_metric",
            "allowed_values": list(ALLOWED_SELECTION_METRICS),
            "original_default": DEFAULT_SELECTION_METRIC,
            "input_constraints_depend_on_parameter": (
                "authored evidence requires two eligible objects whose occupied-size and bbox-area orders disagree"
            ),
        },
        "invariant_reasoning": (
            "find same-color 4-connected objects, retain width>1 raw-bbox LR-symmetric objects, "
            "rank one object, and return its exact bbox crop; only the ranking metric changes"
        ),
        "input_scope": "four lawful authored inputs; fixed three-demo/one-query schedule",
        "sources": source_rows,
        "runtime_files": runtime_rows,
        "runtime": racket_runtime_status(),
        "rules": rule_rows,
        "episodes": episode_rows,
        "files": files,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "counts": {
            "episodes": len(seeds),
            "train_pairs": 3 * len(seeds),
            "query_pairs": len(seeds),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len({
                row["parameters"]["selection_metric"] for row in episode_rows
            }),
            "canonical_pairs_checked": len(canonical_rows),
            "parameter_rival_episode_checks": len(ALLOWED_SELECTION_METRICS) * len(seeds),
            "ambiguous_parameter_rivals": sum(
                rival["status"] == "ambiguous_query"
                for episode in episode_rows for rival in episode["parameter_rivals"]
            ),
            "racket_evaluations_including_deterministic_replays": (
                16 * len(seeds) + len(canonical_rows) + 2
            ),
        },
        "limitations": [
            "Proposed prototype only; no variant approval or production API change.",
            "Evidence covers two settings, two seeds, and four authored inputs, not all inputs or hypotheses.",
            "The alternative changes only eligible-object ranking; all object extraction and crop semantics stay fixed.",
            "Rival checks cover only the two declared selection_metric settings.",
            "The occupied_cells setting is source-identical to the pinned canonical Racket rule.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps({
        "status": report["status"],
        "counts": report["counts"],
        "report": str(args.out / "report.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
