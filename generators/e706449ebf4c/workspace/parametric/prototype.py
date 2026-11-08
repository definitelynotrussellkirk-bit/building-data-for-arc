#!/usr/bin/env python3
"""Proposed fixed-per-episode aura radius-delta prototype for e706449ebf4c.

This module is deliberately separate from the selected production generator and
canonical authority.  ``radius_delta=0`` is the byte-exact canonical rule;
``radius_delta=2`` expands the doubled-Manhattan threshold by one cell while
preserving bar extraction, doubled half-cell centers, clipping, overlap, and
red-cell preservation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from typing import Any, Iterable

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "e706449ebf4c"
PROTOTYPE_VERSION = "proposed-radius-delta-v1"
ALLOWED_RADIUS_DELTAS = (0, 2)
DEFAULT_RADIUS_DELTA = 0
CANONICAL_RADIUS_SITE = "(radius bar-len)"
EXPANDED_RADIUS_SITE = "(radius (+ bar-len 2))"
INPUT_SEED = 2026102201
INPUT_SPECS = (
    (101, "single_vertical_odd"),
    (103, "single_horizontal_even"),
    (105, "two_perpendicular"),
    (107, "clipped_edge"),
)
PROTOTYPE_DIR = Path(__file__).resolve().parent


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode("utf-8")).hexdigest()[:12]


def _validate_radius_delta(radius_delta: Any) -> int:
    if type(radius_delta) is not int or radius_delta not in ALLOWED_RADIUS_DELTAS:
        raise ValueError(
            f"radius_delta must be one of {ALLOWED_RADIUS_DELTAS}, got {radius_delta!r}"
        )
    return radius_delta


def parameters_for_seed(seed: Any) -> dict[str, int]:
    """Choose one hidden rule setting for the whole episode."""
    if type(seed) is not int or seed < 0:
        raise ValueError("episode seed must be a nonnegative literal integer")
    return {"radius_delta": ALLOWED_RADIUS_DELTAS[seed % len(ALLOWED_RADIUS_DELTAS)]}


def canonical_source(*, root: Path | str) -> str:
    for line in canonical_path(Path(root)).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and row.get("program_solution"):
            return str(row["program_solution"])
    raise FileNotFoundError(f"{TASK_ID}: canonical program_solution not found")


def materialize_rule(radius_delta: Any, *, root: Path | str) -> str:
    """Return the complete Racket program for one bounded parameter value."""
    delta = _validate_radius_delta(radius_delta)
    source = canonical_source(root=Path(root))
    if source.count(CANONICAL_RADIUS_SITE) != 1:
        raise ValueError("canonical radius binding changed; refusing an unguarded rewrite")
    if EXPANDED_RADIUS_SITE in source:
        raise ValueError("canonical source unexpectedly already contains expanded radius")
    if delta == DEFAULT_RADIUS_DELTA:
        return source
    return source.replace(CANONICAL_RADIUS_SITE, EXPANDED_RADIUS_SITE, 1)


def rule_callable(source: str) -> str:
    stripped = source.strip()
    prefix = "(rule! "
    if not stripped.startswith(prefix) or not stripped.endswith(")"):
        raise ValueError("expected a plain (rule! <lambda>) program")
    callable_source = stripped[len(prefix) : -1].strip()
    if not callable_source.startswith("(lambda "):
        raise ValueError("prototype rule body must be a lambda")
    return callable_source


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def execute_rule(source: str, grid: list[list[int]], *, bridge=None) -> list[list[int]]:
    """Execute one complete materialized rule through the pinned Racket bridge."""
    from arc_repl.racket_bridge import RacketBridge

    expression = f"({rule_callable(source)} '{_racket_literal(grid)})"
    if bridge is not None:
        result = bridge.eval_text(expression)
    else:
        with RacketBridge() as runtime:
            result = runtime.eval_text(expression)
    if not isinstance(result, list):
        raise RuntimeError("Racket prototype returned a non-grid result")
    return result


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be literal ARC colors 0..9")
    return len(grid), width


def _red_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = _validate_grid(grid)
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        todo = [min(unseen)]
        cells: set[tuple[int, int]] = set()
        while todo:
            row, col = todo.pop()
            if (row, col) not in unseen:
                continue
            unseen.remove((row, col))
            cells.add((row, col))
            todo.extend(
                neighbor
                for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                if neighbor in unseen
            )
        components.append(cells)
    return components


def python_transform(grid: list[list[int]], radius_delta: Any) -> list[list[int]]:
    """Independent assertion mirror; Racket remains label authority."""
    delta = _validate_radius_delta(radius_delta)
    height, width = _validate_grid(grid)
    output = copy.deepcopy(grid)
    for cells in _red_components(grid):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
        length = max(row1 - row0 + 1, col1 - col0 + 1)
        center_row2 = row0 + row1
        center_col2 = col0 + col1
        threshold = length + delta
        for row in range(height):
            for col in range(width):
                distance2 = abs(2 * row - center_row2) + abs(2 * col - center_col2)
                if distance2 <= threshold and output[row][col] == 0:
                    output[row][col] = 8
    return output


def episode_inputs(*, root: Path | str, seed: int) -> list[dict[str, Any]]:
    """Materialize a fixed four-pair schedule; input draws do not reveal the rule setting."""
    if type(seed) is not int or seed < 0:
        raise ValueError("episode seed must be a nonnegative literal integer")
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=Path(root))
    rows = []
    for sample_index, profile in INPUT_SPECS:
        grid = module.generate(
            INPUT_SEED,
            sample_index,
            difficulty="medium",
            scene_profile=profile,
        )
        rows.append(
            {
                "sample_index": sample_index,
                "scene_profile": profile,
                "input": grid,
                "input_sha256": _sha256_text(json.dumps(grid, separators=(",", ":"))),
            }
        )
    return rows


def make_episode(seed: int, *, root: Path | str, bridge=None) -> dict[str, Any]:
    parameters = parameters_for_seed(seed)
    selected_delta = parameters["radius_delta"]
    inputs = episode_inputs(root=Path(root), seed=seed)
    rules = {delta: materialize_rule(delta, root=Path(root)) for delta in ALLOWED_RADIUS_DELTAS}
    predictions = {
        delta: [execute_rule(source, row["input"], bridge=bridge) for row in inputs]
        for delta, source in rules.items()
    }
    for delta in ALLOWED_RADIUS_DELTAS:
        for row, output in zip(inputs, predictions[delta]):
            mirror = python_transform(row["input"], delta)
            if output != mirror:
                raise AssertionError(f"Python/Racket mismatch for radius_delta={delta}")

    selected_outputs = predictions[selected_delta]
    pairs = [
        {
            "input": copy.deepcopy(row["input"]),
            "output": copy.deepcopy(output),
            "sample_index": row["sample_index"],
            "scene_profile": row["scene_profile"],
            "input_sha256": row["input_sha256"],
        }
        for row, output in zip(inputs, selected_outputs)
    ]
    rival_rows = []
    ambiguities = []
    for delta in ALLOWED_RADIUS_DELTAS:
        demo_mismatches = [
            index for index in range(3) if predictions[delta][index] != selected_outputs[index]
        ]
        query_mismatches = [0] if predictions[delta][3] != selected_outputs[3] else []
        status = (
            "refuted_by_demonstrations"
            if demo_mismatches
            else "ambiguous_query"
            if query_mismatches
            else "matches_episode"
        )
        row = {
            "radius_delta": delta,
            "racket_sha256": _sha256_text(rules[delta]),
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    selected_source = rules[selected_delta]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": "ALLOWED_RADIUS_DELTAS[seed % 2], once before all pairs",
        "input_schedule": [row["scene_profile"] for row in inputs],
        "racket_source": selected_source,
        "racket_sha256": _sha256_text(selected_source),
        "racket_normalized_hash": normalized_rule_hash(selected_source),
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": len(ALLOWED_RADIUS_DELTAS) * len(inputs),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Allowlist model-visible fields; omit hidden setting, source, seed, and query label."""
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative_file_rows(out: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name not in {"report.json", "manifest.json"}):
        rows.append({"path": path.relative_to(out).as_posix(), "sha256": _sha256_bytes(path.read_bytes())})
    return rows


def write_evidence(seeds: Iterable[int], *, out: Path | str, root: Path | str) -> dict[str, Any]:
    """Execute both exact Racket settings and write finite, hash-bound evidence."""
    from arc_repl.racket_bridge import RacketBridge

    seed_values = tuple(seeds)
    if not seed_values or len(set(seed_values)) != len(seed_values):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seed_values:
        parameters_for_seed(seed)
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(out_path)
    out_path.mkdir(parents=True)
    root_path = Path(root)

    rules = {delta: materialize_rule(delta, root=root_path) for delta in ALLOWED_RADIUS_DELTAS}
    for delta, source in rules.items():
        rule_path = out_path / "private" / "rules" / f"radius-delta-{delta}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(source, encoding="utf-8")

    with RacketBridge() as bridge:
        canonical_checks = []
        default_source = rules[DEFAULT_RADIUS_DELTA]
        for index, pair in enumerate(canonical_pairs(TASK_ID, root=root_path, labeled_only=True)):
            output = execute_rule(default_source, pair["input"], bridge=bridge)
            if output != pair["output"]:
                raise AssertionError(f"canonical default mismatch at pair {index}")
            canonical_checks.append(
                {
                    "pair_index": index,
                    "input_sha256": _sha256_text(json.dumps(pair["input"], separators=(",", ":"))),
                    "output_sha256": _sha256_text(json.dumps(output, separators=(",", ":"))),
                }
            )
        _write_json(
            out_path / "private" / "canonical-default-check.json",
            {
                "task_id": TASK_ID,
                "radius_delta": DEFAULT_RADIUS_DELTA,
                "racket_sha256": _sha256_text(default_source),
                "pairs": canonical_checks,
            },
        )

        episode_rows = []
        episodes = []
        for index, seed in enumerate(seed_values):
            episode = make_episode(seed=seed, root=root_path, bridge=bridge)
            episodes.append(episode)
            private_rel = f"private/episode-{index:03d}.json"
            public_rel = f"public/episode-{index:03d}.json"
            _write_json(out_path / private_rel, episode)
            _write_json(out_path / public_rel, public_challenge(episode))
            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "private_path": private_rel,
                    "public_path": public_rel,
                    "ambiguities": len(episode["ambiguities"]),
                    "parameter_rivals": episode["parameter_rivals"],
                }
            )

        witness_input = episodes[0]["train"][0]["input"]
        witness_outputs = {
            str(delta): execute_rule(source, witness_input, bridge=bridge)
            for delta, source in rules.items()
        }
        if witness_outputs["0"] == witness_outputs["2"]:
            raise AssertionError("retained parameter witness does not distinguish settings")
        _write_json(
            out_path / "private" / "distinguishing-witness.json",
            {
                "input": witness_input,
                "outputs": witness_outputs,
                "rule_sha256": {str(delta): _sha256_text(source) for delta, source in rules.items()},
            },
        )

    source_snapshot = out_path / "private" / "source_snapshot"
    source_snapshot.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), source_snapshot / "prototype.py")
    test_source = PROTOTYPE_DIR.parent.parent / "tests" / "test_parametric_radius_delta.py"
    if test_source.exists():
        shutil.copy2(test_source, source_snapshot / test_source.name)

    files = _relative_file_rows(out_path)
    settings = {episode["parameters"]["radius_delta"] for episode in episodes}
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "parameter": {
            "name": "radius_delta",
            "allowed_values": list(ALLOWED_RADIUS_DELTAS),
            "original_default": DEFAULT_RADIUS_DELTA,
            "units": "doubled Manhattan distance (2 equals one grid cell)",
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "extract red 4-connected bars, measure inclusive length, use the doubled bbox midpoint, "
            "paint only zero cells, and preserve clipping/overlap; only the distance threshold changes"
        ),
        "counts": {
            "episodes": len(episodes),
            "settings_exercised": len(settings),
            "train_pairs": sum(len(episode["train"]) for episode in episodes),
            "query_pairs": sum(len(episode["test"]) for episode in episodes),
            "canonical_pairs_checked": len(canonical_checks),
            "ambiguous_parameter_rivals": sum(len(episode["ambiguities"]) for episode in episodes),
            "racket_evaluations": len(canonical_checks)
            + sum(episode["racket_evaluations"] for episode in episodes)
            + len(ALLOWED_RADIUS_DELTAS),
        },
        "rules": [
            {
                "radius_delta": delta,
                "path": f"private/rules/radius-delta-{delta}.rkt",
                "sha256": _sha256_text(source),
                "normalized_hash": normalized_rule_hash(source),
            }
            for delta, source in rules.items()
        ],
        "episodes": episode_rows,
        "limitations": [
            "Proposed prototype only; no variant approval or production API change.",
            "Evidence covers two settings, two seeds, four scheduled inputs, and declared parameter rivals only.",
            "The expanded setting may be indistinguishable on a fully saturated or extremely clipped grid; scheduled demonstrations avoid that ambiguity.",
            "Public challenge files intentionally omit hidden parameters, Racket source, seeds, and query answers.",
        ],
        "files": files,
    }
    _write_json(out_path / "report.json", report)
    _write_json(
        out_path / "manifest.json",
        {"schema": "arcpuzzles-parametric-evidence-manifest-v1", "files": files},
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    report = write_evidence(args.seeds, out=Path(args.out), root=root)
    print(json.dumps({"status": report["status"], "counts": report["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
