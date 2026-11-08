#!/usr/bin/env python3
"""Proposed episode-level deflection-distance rules for task 8eb9146172f8.

The production generator and canonical authority remain unchanged.  This
prototype chooses one hidden distance per episode and labels every pair by
executing the exact materialized Racket rule with the bundled runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "8eb9146172f8"
ORIGINAL_FAMILY = "training:f15e1fac"
PUBLIC_INSPIRATION = "evaluation:20a9e565"
DEFAULT_DEFLECTION_DISTANCE = 1
DEFLECTION_DISTANCES = (1, 2)
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
HERE = TASK_HOME / "workspace" / "parametric"
CANONICAL_RECORD = (
    ROOT
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "f15e1fac__8eb9146172f8.json"
)

# The two episode pools deliberately cover all four ray origins and both signs
# of the edge-relative deflection.  Counts remain independently configurable.
DEMO_SPECS = (
    ("demo_top_left", "top", "left", 17, 17, 3, 2),
    ("demo_bottom_right", "bottom", "right", 17, 18, 3, 2),
    ("demo_left_top", "left", "top", 18, 17, 3, 2),
    ("demo_right_bottom", "right", "bottom", 18, 18, 3, 2),
)
QUERY_SPECS = (
    ("query_top_right", "top", "right", 19, 18, 4, 3),
    ("query_bottom_left", "bottom", "left", 18, 19, 4, 2),
    ("query_left_bottom", "left", "bottom", 20, 16, 3, 3),
    ("query_right_top", "right", "top", 16, 20, 3, 2),
)


def digest(data: bytes) -> str:
    if not isinstance(data, bytes):
        raise TypeError("digest expects bytes")
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _json_digest(value: Any) -> str:
    return digest(_json_bytes(value))


def canonical_rule() -> str:
    record = json.loads(CANONICAL_RECORD.read_text(encoding="utf-8"))
    if record.get("task_id") != TASK_ID:
        raise ValueError("canonical authority task ID mismatch")
    source = record.get("racket_target", {}).get("target_code")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("canonical record has no executable Racket target")
    return source


def normalized_rule_hash(source: str) -> str:
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be non-empty Racket text")
    return digest(" ".join(source.split()).encode("utf-8"))[:12]


def _validate_distance(deflection_distance: Any) -> int:
    if (
        type(deflection_distance) is not int
        or deflection_distance not in DEFLECTION_DISTANCES
    ):
        raise ValueError(
            f"deflection_distance must be one of {DEFLECTION_DISTANCES!r}"
        )
    return deflection_distance


def materialize_rule(
    deflection_distance: int = DEFAULT_DEFLECTION_DISTANCE,
) -> str:
    """Return exact canonical text or its distance-two shift-only variant."""
    distance = _validate_distance(deflection_distance)
    source = canonical_rule()
    if distance == DEFAULT_DEFLECTION_DISTANCE:
        return source

    pattern = re.compile(
        r"\(shift-val \(cond\s+"
        r"\(\(eq\? red-edge 'top\) 1\)\s+"
        r"\(\(eq\? red-edge 'bottom\) -1\)\s+"
        r"\(\(eq\? red-edge 'left\) 1\)\s+"
        r"\(else -1\)\)\)"
    )
    replacement = """(shift-val (cond
                               ((eq? red-edge 'top) 2)
                               ((eq? red-edge 'bottom) -2)
                               ((eq? red-edge 'left) 2)
                               (else -2)))"""
    variant, count = pattern.subn(replacement, source)
    if count != 1:
        raise ValueError(
            "canonical source no longer has the expected unique shift-val form"
        )
    return variant


def select_deflection_distance(seed: int) -> int:
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    byte = hashlib.sha256(
        f"{TASK_ID}:deflection_distance:{seed}".encode("utf-8")
    ).digest()[0]
    return DEFLECTION_DISTANCES[byte % len(DEFLECTION_DISTANCES)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("input must be a non-empty rectangular ARC grid")
    width = len(grid[0])
    if width == 0 or len(grid) > 30 or width > 30:
        raise ValueError("input must have 1..30 rows and columns")
    if any(
        not isinstance(row, list)
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError(
            "input must be rectangular with exact integer ARC colors in 0..9"
        )
    return [list(row) for row in grid]


def execute_rule(source: str, inputs: Iterable[Any]) -> list[list[list[int]]]:
    """Execute exact rule text against each input using the real Racket bridge."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be non-empty Racket text")
    grids = [_validate_grid(grid) for grid in inputs]
    outputs: list[list[list[int]]] = []
    with RacketBridge(timeout=30.0) as bridge:
        bridge.eval_text(
            f"(define __parametric_rule "
            f"(let ([rule! (lambda (f) f)]) {source}))"
        )
        for index, grid in enumerate(grids):
            name = f"__parametric_input_{index}"
            bridge.define_grid(name, grid)
            output = _validate_grid(bridge.eval_text(f"(__parametric_rule {name})"))
            if len(output) != len(grid) or len(output[0]) != len(grid[0]):
                raise RuntimeError("Racket output changed the grid dimensions")
            outputs.append(output)
    return outputs


def apply_python(
    grid: list[list[int]], deflection_distance: int = 1
) -> list[list[int]]:
    """Independent rule-loop mirror for audit; Racket remains label authority."""
    distance = _validate_distance(deflection_distance)
    generator, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
    facts, errors = generator._analyze(grid)
    if errors or facts is None:
        raise ValueError("rule expects a lawful scene: " + "; ".join(errors))

    h = facts["grid_h"]
    w = facts["grid_w"]
    cyan_edge = facts["cyan_edge"]
    red_edge = facts["red_edge"]
    cyan_cells = list(facts["cyan_cells"])
    red_cells = list(facts["red_cells"])
    red_rows = {row for row, _ in red_cells}
    red_cols = {col for _, col in red_cells}
    direction = 1 if red_edge in ("top", "left") else -1
    shift = direction * distance

    output = [row[:] for row in grid]
    for start_row, start_col in cyan_cells:
        row, col = start_row, start_col
        if cyan_edge == "top":
            for row in range(h):
                if row in red_rows:
                    col += shift
                if 0 <= col < w:
                    output[row][col] = 8
        elif cyan_edge == "bottom":
            for row in range(h - 1, -1, -1):
                if row in red_rows:
                    col += shift
                if 0 <= col < w:
                    output[row][col] = 8
        elif cyan_edge == "left":
            for col in range(w):
                if col in red_cols:
                    row += shift
                if 0 <= row < h:
                    output[row][col] = 8
        elif cyan_edge == "right":
            for col in range(w - 1, -1, -1):
                if col in red_cols:
                    row += shift
                if 0 <= row < h:
                    output[row][col] = 8
        else:  # pragma: no cover - the selected generator validates this.
            raise AssertionError(f"unexpected cyan edge {cyan_edge!r}")
    return output


def _validate_count(name: str, value: Any, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in 1..{maximum}")
    return value


def _draw_inputs(
    *,
    seed: int,
    demo_count: int,
    query_count: int,
    start: int,
    difficulty: str,
) -> tuple[list[dict[str, Any]], dict[int, list[list[list[int]]]]]:
    """Draw one jointly identifying candidate per requested role.

    The selected input set is independent of the hidden setting.  Both exact
    Racket rules are then executed; a bounded retry changes only sample indices
    if any candidate fails to distinguish the two distances.
    """
    if type(seed) is not int or type(start) is not int:
        raise ValueError("seed and start must be literal integers")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    demo_count = _validate_count("demo_count", demo_count, len(DEMO_SPECS))
    query_count = _validate_count("query_count", query_count, len(QUERY_SPECS))

    generator, source_path, source_sha256 = load_selected_generator(
        TASK_ID, root=ROOT
    )
    specs = [("train", *row) for row in DEMO_SPECS[:demo_count]] + [
        ("test", *row) for row in QUERY_SPECS[:query_count]
    ]

    for attempt in range(50):
        rows: list[dict[str, Any]] = []
        for role_index, (
            split,
            role,
            cyan_edge,
            red_edge,
            grid_h,
            grid_w,
            n_red,
            n_cyan,
        ) in enumerate(specs):
            sample_index = start + role_index * 101 + attempt
            grid = generator.generate(
                seed,
                sample_index,
                difficulty=difficulty,
                grid_h=grid_h,
                grid_w=grid_w,
                cyan_edge=cyan_edge,
                red_edge=red_edge,
                n_red=n_red,
                n_cyan=n_cyan,
            )
            errors = generator.self_check(grid)
            if errors:
                raise RuntimeError(
                    f"selected generator returned an unlawful prototype input: {errors}"
                )
            rows.append(
                {
                    "split": split,
                    "role": role,
                    "sample_index": sample_index,
                    "input": grid,
                }
            )

        inputs = [row["input"] for row in rows]
        predictions = {
            distance: execute_rule(materialize_rule(distance), inputs)
            for distance in DEFLECTION_DISTANCES
        }
        distinct_inputs = len({_json_digest(grid) for grid in inputs}) == len(inputs)
        disagreements = [
            predictions[1][index] != predictions[2][index]
            for index in range(len(inputs))
        ]
        if distinct_inputs and all(disagreements):
            for index, row in enumerate(rows):
                row["input_sha256"] = _json_digest(row["input"])
                row["prediction_sha256"] = {
                    str(distance): _json_digest(predictions[distance][index])
                    for distance in DEFLECTION_DISTANCES
                }
            return rows, predictions

    raise RuntimeError(
        "could not draw distinct inputs that separate both distances in 50 attempts"
    )


def build_episode(
    *,
    seed: int,
    deflection_distance: int | None = None,
    demo_count: int = 3,
    query_count: int = 4,
    start: int = 0,
    difficulty: str = "medium",
) -> dict[str, Any]:
    """Build one fixed-setting episode with real-Racket labels and rivals."""
    if deflection_distance is None:
        setting = select_deflection_distance(seed)
    else:
        setting = _validate_distance(deflection_distance)
    rows, predictions = _draw_inputs(
        seed=seed,
        demo_count=demo_count,
        query_count=query_count,
        start=start,
        difficulty=difficulty,
    )
    other = next(value for value in DEFLECTION_DISTANCES if value != setting)

    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    row_evidence: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        pair = {
            "input": copy.deepcopy(row["input"]),
            "output": copy.deepcopy(predictions[setting][index]),
        }
        (train if row["split"] == "train" else test).append(pair)
        row_evidence.append(
            {
                key: row[key]
                for key in (
                    "split",
                    "role",
                    "sample_index",
                    "input_sha256",
                    "prediction_sha256",
                )
            }
        )

    consistent_settings = [
        distance
        for distance in DEFLECTION_DISTANCES
        if all(
            predictions[distance][index] == predictions[setting][index]
            for index, row in enumerate(rows)
            if row["split"] == "train"
        )
    ]
    train_indices = [index for index, row in enumerate(rows) if row["split"] == "train"]
    test_indices = [index for index, row in enumerate(rows) if row["split"] == "test"]
    rival_demo_mismatches = [
        local_index
        for local_index, absolute_index in enumerate(train_indices)
        if predictions[other][absolute_index] != predictions[setting][absolute_index]
    ]
    rival_query_mismatches = [
        local_index
        for local_index, absolute_index in enumerate(test_indices)
        if predictions[other][absolute_index] != predictions[setting][absolute_index]
    ]
    if consistent_settings != [setting]:
        raise RuntimeError(
            f"demonstrations do not uniquely identify setting {setting}: "
            f"{consistent_settings}"
        )

    source = materialize_rule(setting)
    return {
        "schema": "arc-ray-deflection-distance-episode-v1",
        "status": "proposed_research_prototype",
        "task_id": TASK_ID,
        "original_family": ORIGINAL_FAMILY,
        "public_inspiration": PUBLIC_INSPIRATION,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": {"deflection_distance": setting},
        "parameter_domain": {"deflection_distance": list(DEFLECTION_DISTANCES)},
        "canonical_default": {"deflection_distance": DEFAULT_DEFLECTION_DISTANCE},
        "program": source,
        "program_sha256": digest(source.encode("utf-8")),
        "normalized_rule_hash": normalized_rule_hash(source),
        "train": train,
        "test": test,
        "draws": row_evidence,
        "rivals": {
            "declared_settings": list(DEFLECTION_DISTANCES),
            "consistent_settings": consistent_settings,
            "rival_setting": other,
            "rival_demo_mismatches": rival_demo_mismatches,
            "rival_query_mismatches": rival_query_mismatches,
            "rival_outputs": {
                "train": [copy.deepcopy(predictions[other][i]) for i in train_indices],
                "test": [copy.deepcopy(predictions[other][i]) for i in test_indices],
            },
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _canonical_parity() -> list[dict[str, Any]]:
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    outputs = execute_rule(materialize_rule(1), [pair["input"] for pair in pairs])
    rows = []
    for pair, output in zip(pairs, outputs, strict=True):
        rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": _json_digest(pair["input"]),
                "expected_output_sha256": _json_digest(pair["output"]),
                "actual_output_sha256": _json_digest(output),
                "matches": output == pair["output"],
            }
        )
    if not all(row["matches"] for row in rows):
        raise RuntimeError("canonical default parity failed")
    return rows


def _same_input_witness() -> dict[str, Any]:
    grid = [[0] * 9 for _ in range(9)]
    grid[0][2] = 8
    grid[3][0] = 2
    grid[6][0] = 2
    predictions = {
        distance: execute_rule(materialize_rule(distance), [grid])[0]
        for distance in DEFLECTION_DISTANCES
    }
    differing_cells = sum(
        predictions[1][row][col] != predictions[2][row][col]
        for row in range(9)
        for col in range(9)
    )
    return {
        "input": grid,
        "outputs": {str(key): value for key, value in predictions.items()},
        "differing_cells": differing_cells,
        "settings_disagree": predictions[1] != predictions[2],
    }


def write_evidence(
    *,
    out: Path,
    seed: int,
    settings: tuple[int, ...],
    demo_count: int,
    query_count: int,
    start: int,
    difficulty: str,
) -> dict[str, Any]:
    """Write private evidence and exact visible public challenge bytes."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"refusing to replace existing output directory: {out}")
    validated_settings = tuple(_validate_distance(value) for value in settings)
    if not validated_settings or len(set(validated_settings)) != len(validated_settings):
        raise ValueError("settings must be a nonempty sequence without duplicates")

    private_dir = out / "private"
    public_dir = out / "public"
    private_dir.mkdir(parents=True)
    public_dir.mkdir()

    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=ROOT
    )
    del generator
    parity = _canonical_parity()
    witness = _same_input_witness()
    _write_json(private_dir / "canonical-parity.json", parity)
    _write_json(private_dir / "same-input-witness.json", witness)

    episode_rows: list[dict[str, Any]] = []
    seen_public_ids: set[str] = set()
    episodes_by_public_id: list[tuple[str, dict[str, Any]]] = []
    for setting in validated_settings:
        episode = build_episode(
            seed=seed,
            deflection_distance=setting,
            demo_count=demo_count,
            query_count=query_count,
            start=start,
            difficulty=difficulty,
        )
        challenge_id = public_id(episode)
        if challenge_id in seen_public_ids:
            raise RuntimeError("duplicate visible public challenge payload")
        seen_public_ids.add(challenge_id)
        episodes_by_public_id.append((challenge_id, episode))

    for ordinal, (challenge_id, episode) in enumerate(
        sorted(episodes_by_public_id, key=lambda item: item[0])
    ):
        private_name = f"episode-{ordinal:03d}.json"
        rule_name = f"rule-{episode['program_sha256']}.rkt"
        public_name = f"challenge-{challenge_id}.json"
        _write_json(private_dir / private_name, episode)
        (private_dir / rule_name).write_text(episode["program"], encoding="utf-8")
        (public_dir / public_name).write_bytes(public_bytes(episode))
        episode_rows.append(
            {
                "private_path": f"private/{private_name}",
                "rule_path": f"private/{rule_name}",
                "public_path": f"public/{public_name}",
                "public_id": challenge_id,
                "parameters": episode["parameters"],
                "program_sha256": episode["program_sha256"],
                "normalized_rule_hash": episode["normalized_rule_hash"],
                "demo_count": len(episode["train"]),
                "query_count": len(episode["test"]),
                "consistent_settings": episode["rivals"]["consistent_settings"],
                "rival_demo_mismatches": episode["rivals"][
                    "rival_demo_mismatches"
                ],
                "rival_query_mismatches": episode["rivals"][
                    "rival_query_mismatches"
                ],
            }
        )

    tracked = [
        HERE / "prototype.py",
        HERE / "README.md",
        TASK_HOME / "tests" / "test_parametric_deflection_distance.py",
        CANONICAL_RECORD,
        generator_path,
        ROOT / "shared/runtime/reviewer_support.py",
        ROOT / "shared/runtime/arc_repl/racket_bridge.py",
    ]
    source_sha256 = {
        str(path.relative_to(ROOT)): digest(path.read_bytes())
        for path in tracked
        if path.is_file()
    }
    manifest = {
        "schema": "arc-ray-deflection-distance-evidence-v1",
        "status": "proposed",
        "task_id": TASK_ID,
        "original_family": ORIGINAL_FAMILY,
        "public_inspiration": PUBLIC_INSPIRATION,
        "seed": seed,
        "demo_count": demo_count,
        "query_count": query_count,
        "start": start,
        "difficulty": difficulty,
        "runtime": racket_runtime_status(),
        "selected_generator_sha256": generator_sha256,
        "canonical_default_rule_hash": normalized_rule_hash(materialize_rule(1)),
        "canonical_parity": parity,
        "same_input_witness": {
            "path": "private/same-input-witness.json",
            "differing_cells": witness["differing_cells"],
            "settings_disagree": witness["settings_disagree"],
        },
        "episodes": episode_rows,
        "source_sha256": source_sha256,
        "limits": [
            "Finite declared setting set {1,2}; no completeness claim for other rules.",
            "Prototype only; production generator and canonical Racket authority are unchanged.",
            "Evidence covers the retained seeds/roles and rejects ambiguous sampled inputs; it is not a census over all seeds.",
            "The evaluation task 20a9e565 contributes only the repeated-spatial-stride inspiration; no lineage or measured-difficulty claim is made.",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    files = {
        str(path.relative_to(out)): digest(path.read_bytes())
        for path in sorted(out.rglob("*"))
        if path.is_file() and path != out / "manifest.json"
    }
    manifest["files"] = files
    _write_json(out / "manifest.json", manifest)
    return {
        "status": "ok",
        "out": str(out),
        "episodes": len(episode_rows),
        "canonical_pairs": len(parity),
        "public_ids": sorted(seen_public_ids),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--deflection-distance", type=int, choices=DEFLECTION_DISTANCES)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.all_settings and args.deflection_distance is not None:
        parser.error("--all-settings and --deflection-distance are mutually exclusive")
    settings = (
        DEFLECTION_DISTANCES
        if args.all_settings
        else (
            args.deflection_distance
            if args.deflection_distance is not None
            else select_deflection_distance(args.seed),
        )
    )
    result = write_evidence(
        out=args.out,
        seed=args.seed,
        settings=tuple(settings),
        demo_count=args.demos,
        query_count=args.queries,
        start=args.start,
        difficulty=args.difficulty,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
