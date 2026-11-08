#!/usr/bin/env python3
"""Task-local prototype for a fixed-per-episode border projection span.

This proposed extension stays separate from the selected production generator
and canonical authority.  It materializes two complete rules:

* span 1 — the byte-exact canonical/default behavior;
* span 2 — paint two consecutive cells from every marker toward its matching
  colored border.

Both settings preserve border orientation, marker roles, half-axis direction,
and copied border color.  The hidden span is selected once from the episode seed
and held fixed across all demonstrations and the query.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sys
from typing import Any

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


TASK_ID = "b19deac47327"
ALLOWED_PROJECTION_SPANS = (1, 2)
DEFAULT_PROJECTION_SPAN = 1
PROTOTYPE_VERSION = "1.0.0"
PAIR_COUNT = 4
DEMONSTRATION_COUNT = 3
PROTOTYPE_DIR = Path(__file__).resolve().parent
RULE_DIR = PROTOTYPE_DIR / "racket"

_EDGE_PAIRS = ((2, 4), (8, 3), (5, 9), (3, 4), (2, 8))
# Pair order deliberately alternates orientations and includes odd projection
# axes so the original tie-to-first convention remains visible.
_DIMENSION_PROFILES = (
    (13, 11, "horizontal"),
    (11, 13, "vertical"),
    (15, 12, "horizontal"),
    (12, 15, "vertical"),
)

_H_NR_ONE = "(nr (if (< (* 2 r) h) (- r 1) (+ r 1)))"
_H_NR_TWO = _H_NR_ONE + "\n                                             (nr2 (if (< (* 2 r) h) (- r 2) (+ r 2)))"
_H_WRITE_ONE = """(if (in-bounds? nr c h w)
                                            (set-cell acc nr c color)
                                            acc)"""
_H_WRITE_TWO = """(if (in-bounds? nr c h w)
                                            (let ((once (set-cell acc nr c color)))
                                              (if (in-bounds? nr2 c h w)
                                                  (set-cell once nr2 c color)
                                                  once))
                                            acc)"""
_V_NC_ONE = "(nc (if (< (* 2 c) w) (- c 1) (+ c 1)))"
_V_NC_TWO = _V_NC_ONE + "\n                                             (nc2 (if (< (* 2 c) w) (- c 2) (+ c 2)))"
_V_WRITE_ONE = """(if (in-bounds? r nc h w)
                                            (set-cell acc r nc color)
                                            acc)"""
_V_WRITE_TWO = """(if (in-bounds? r nc h w)
                                            (let ((once (set-cell acc r nc color)))
                                              (if (in-bounds? r nc2 h w)
                                                  (set-cell once r nc2 color)
                                                  once))
                                            acc)"""


def validate_projection_span(projection_span: Any) -> int:
    """Validate the bounded semantic parameter without coercing scalars."""
    if type(projection_span) is not int:
        raise TypeError("projection_span must be an integer (not bool)")
    if projection_span not in ALLOWED_PROJECTION_SPANS:
        raise ValueError(
            f"projection_span must be one of {ALLOWED_PROJECTION_SPANS}, "
            f"got {projection_span!r}"
        )
    return projection_span


def choose_projection_span(seed: Any) -> int:
    """Choose one hidden setting for an entire deterministic episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return ALLOWED_PROJECTION_SPANS[seed % len(ALLOWED_PROJECTION_SPANS)]


def normalized_hash(source: str) -> str:
    """Return the repository's 12-hex whitespace-normalized rule hash."""
    return hashlib.sha256(" ".join(source.split()).encode("utf-8")).hexdigest()[:12]


def _canonical_source(*, root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(f"{TASK_ID}: canonical program_solution not found")


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"expected one canonical {label} fragment, found {count}")
    return source.replace(old, new)


def _span_two_source(canonical: str) -> str:
    source = canonical
    for old, new, label in (
        (_H_NR_ONE, _H_NR_TWO, "horizontal first-step binding"),
        (_H_WRITE_ONE, _H_WRITE_TWO, "horizontal write"),
        (_V_NC_ONE, _V_NC_TWO, "vertical first-step binding"),
        (_V_WRITE_ONE, _V_WRITE_TWO, "vertical write"),
    ):
        source = _replace_once(source, old, new, label)
    return source


def racket_source(projection_span: Any, *, root: Path | str) -> str:
    """Materialize the exact complete Racket rule for one parameter value."""
    span = validate_projection_span(projection_span)
    canonical = _canonical_source(root=Path(root))
    return canonical if span == 1 else _span_two_source(canonical)


def rule_path(projection_span: Any) -> Path:
    span = validate_projection_span(projection_span)
    return RULE_DIR / f"span-{span}.rkt"


def materialize_rules(*, root: Path | str) -> dict[str, str]:
    """Write both exact complete programs and return raw SHA-256 hashes."""
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for span in ALLOWED_PROJECTION_SPANS:
        source = racket_source(span, root=root)
        rule_path(span).write_text(source, encoding="utf-8")
        hashes[str(span)] = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return hashes


def _seeded_rng(seed: int, pair_index: int) -> random.Random:
    payload = f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{pair_index}".encode("utf-8")
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")
    return random.Random(integer)


def _marker_cell(orientation: str, axis: int, lane: int) -> tuple[int, int]:
    return (axis, lane) if orientation == "horizontal" else (lane, axis)


def sample_input(seed: Any, pair_index: Any) -> list[list[int]]:
    """Construct one lawful family input with two visible projection cells.

    The sampler is independent of the selected generator so changing the hidden
    span never changes the input.  It preserves the original solid opposite
    borders, color-1 markers, half-axis direction, and both orientations.
    """
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(pair_index) is not int:
        raise TypeError("pair_index must be an integer (not bool)")
    if not 0 <= pair_index < PAIR_COUNT:
        raise ValueError(f"pair_index must be in 0..{PAIR_COUNT - 1}")

    height, width, orientation = _DIMENSION_PROFILES[pair_index]
    rng = _seeded_rng(seed, pair_index)
    edge_a, edge_b = _EDGE_PAIRS[(seed + 2 * pair_index) % len(_EDGE_PAIRS)]
    marker_count = 6 + ((seed + pair_index) % 2)
    first_count = (marker_count + 1) // 2
    second_count = marker_count - first_count

    axis_extent = height if orientation == "horizontal" else width
    lane_extent = width if orientation == "horizontal" else height
    # Stay at least three cells from the matching border.  Thus both span
    # settings paint background cells and every pair distinguishes 1 from 2.
    first_axes = [
        axis for axis in range(3, axis_extent - 3) if 2 * axis < axis_extent
    ]
    second_axes = [
        axis for axis in range(3, axis_extent - 3) if 2 * axis >= axis_extent
    ]
    if not first_axes or not second_axes:
        raise AssertionError("dimension profile cannot support two-cell projections")

    first_lanes = list(range(lane_extent))
    second_lanes = list(range(lane_extent))
    rng.shuffle(first_lanes)
    rng.shuffle(second_lanes)
    first_lanes = first_lanes[:first_count]
    second_lanes = second_lanes[:second_count]

    markers: list[tuple[int, int]] = []
    midline = (axis_extent - 1) // 2
    for offset, lane in enumerate(first_lanes):
        # Odd-axis profiles explicitly retain the original tie-to-first case.
        if axis_extent % 2 == 1 and offset == 0 and midline in first_axes:
            axis = midline
        else:
            axis = rng.choice(first_axes)
        markers.append(_marker_cell(orientation, axis, lane))
    for lane in second_lanes:
        markers.append(_marker_cell(orientation, rng.choice(second_axes), lane))

    grid = [[0] * width for _ in range(height)]
    if orientation == "horizontal":
        grid[0] = [edge_a] * width
        grid[-1] = [edge_b] * width
    else:
        for row in grid:
            row[0] = edge_a
            row[-1] = edge_b
    for row, col in markers:
        if grid[row][col] != 0:
            raise AssertionError("marker construction collided with a border")
        grid[row][col] = 1

    validate_input(grid)
    return grid


def _solid_color(values: list[int]) -> int | None:
    if values and len(set(values)) == 1 and values[0] not in (0, 1):
        return values[0]
    return None


def validate_input(grid: Any) -> dict[str, Any]:
    """Parse the prototype domain and prove capacity for both span settings."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a nonempty list of rows")
    if not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid palette must contain integer ARC colors 0..9")

    height = len(grid)
    top = _solid_color(grid[0])
    bottom = _solid_color(grid[-1])
    left = _solid_color([row[0] for row in grid])
    right = _solid_color([row[-1] for row in grid])
    horizontal = top is not None and bottom is not None
    vertical = left is not None and right is not None
    if horizontal == vertical:
        raise ValueError("expected exactly one solid opposite-border orientation")

    if horizontal:
        orientation = "horizontal"
        edge_a, edge_b = top, bottom
        axis_extent = height
    else:
        orientation = "vertical"
        edge_a, edge_b = left, right
        axis_extent = width
    assert edge_a is not None and edge_b is not None
    if edge_a == edge_b:
        raise ValueError("the two border colors must be distinct")

    allowed = {0, 1, edge_a, edge_b}
    palette = {value for row in grid for value in row}
    if palette != allowed:
        raise ValueError(
            f"prototype palette must be exactly {sorted(allowed)}; got {sorted(palette)}"
        )

    for row in range(height):
        for col in range(width):
            on_colored_border = (
                row in (0, height - 1)
                if orientation == "horizontal"
                else col in (0, width - 1)
            )
            if not on_colored_border and grid[row][col] in (edge_a, edge_b):
                raise ValueError("border colors may not occur in the input interior")

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    if not 4 <= len(markers) <= 12:
        raise ValueError(f"expected 4..12 markers; found {len(markers)}")

    first_count = 0
    second_count = 0
    ray_cells: list[tuple[int, int]] = []
    occupied = set(markers)
    for row, col in markers:
        axis = row if orientation == "horizontal" else col
        first = 2 * axis < axis_extent
        first_count += int(first)
        second_count += int(not first)
        delta = -1 if first else 1
        for distance in ALLOWED_PROJECTION_SPANS:
            target = (
                (row + delta * distance, col)
                if orientation == "horizontal"
                else (row, col + delta * distance)
            )
            target_row, target_col = target
            if not (0 <= target_row < height and 0 <= target_col < width):
                raise ValueError("projection ray leaves the grid")
            if grid[target_row][target_col] != 0:
                raise ValueError("both projection cells must be background")
            if target in occupied:
                raise ValueError("marker projection rays must be disjoint")
            occupied.add(target)
            ray_cells.append(target)

    if not first_count or not second_count:
        raise ValueError("markers must occupy both halves of the projection axis")
    return {
        "height": height,
        "width": width,
        "orientation": orientation,
        "edge_a": edge_a,
        "edge_b": edge_b,
        "axis_extent": axis_extent,
        "markers": markers,
        "ray_cells": ray_cells,
        "first_count": first_count,
        "second_count": second_count,
        "palette": palette,
        "projection_span_capacity": max(ALLOWED_PROJECTION_SPANS),
    }


def python_transform(grid: list[list[int]], projection_span: Any) -> list[list[int]]:
    """Independent assertion mirror; retained labels are executed by Racket."""
    span = validate_projection_span(projection_span)
    facts = validate_input(grid)
    output = copy.deepcopy(grid)
    for row, col in facts["markers"]:
        axis = row if facts["orientation"] == "horizontal" else col
        first = 2 * axis < facts["axis_extent"]
        delta = -1 if first else 1
        color = facts["edge_a"] if first else facts["edge_b"]
        for distance in range(1, span + 1):
            if facts["orientation"] == "horizontal":
                output[row + delta * distance][col] = color
            else:
                output[row][col + delta * distance] = color
    return output


def build_episode(
    *,
    root: Path | str,
    seed: Any,
    projection_span: Any | None = None,
) -> dict[str, Any]:
    """Build three labelled demonstrations and one labelled query."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    span = (
        choose_projection_span(seed)
        if projection_span is None
        else validate_projection_span(projection_span)
    )
    _module, selected_source_path, selected_source_sha = load_selected_generator(
        TASK_ID, root=Path(root)
    )
    pairs = []
    for pair_index in range(PAIR_COUNT):
        grid = sample_input(seed, pair_index)
        facts = validate_input(grid)
        pairs.append(
            {
                "pair_index": pair_index,
                "orientation": facts["orientation"],
                "input": grid,
                "output": python_transform(grid, span),
            }
        )
    return {
        "schema": "arcpuzzles-parametric-projection-span-episode-v1",
        "status": "prototype",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"projection_span": span},
        "selected_generator_path": str(selected_source_path.relative_to(Path(root))),
        "selected_generator_sha256": selected_source_sha,
        "train": pairs[:DEMONSTRATION_COUNT],
        "test": pairs[DEMONSTRATION_COUNT:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Whitelist projection: labelled demos and an unlabelled query only."""
    return {
        "schema": "arcpuzzles-parametric-projection-span-public-v1",
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


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def _callable_racket_source(source: str) -> str:
    stripped = source.strip()
    prefix = "(rule! "
    if not stripped.startswith(prefix) or not stripped.endswith(")"):
        raise ValueError("expected a plain (rule! <lambda>) program")
    callable_source = stripped[len(prefix) : -1].strip()
    if not callable_source.startswith("(lambda "):
        raise ValueError("prototype rule body must be a lambda")
    return callable_source


def _racket_outputs(source: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketBridge

    callable_source = _callable_racket_source(source)
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define prototype-rule {callable_source})")
        result = bridge.eval_text(f"(map prototype-rule '{_racket_literal(grids)})")
    if not isinstance(result, list) or len(result) != len(grids):
        raise RuntimeError("unexpected Racket result shape")
    return result


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _racket_runtime_metadata() -> dict[str, Any]:
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError(
            "racket executable not found; run through review.py run or run_with_racket.py"
        )
    path = Path(executable).resolve()
    return {
        "executable": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _lesson_gate(
    actual_outputs: list[list[list[int]]],
    rival_outputs: list[list[list[int]]],
    *,
    query_index: int,
) -> dict[str, Any]:
    """Reusable pairwise hidden-parameter identifiability check."""
    if len(actual_outputs) != len(rival_outputs) or not actual_outputs:
        raise ValueError("actual and rival output lists must have the same nonzero length")
    if not 0 <= query_index < len(actual_outputs):
        raise ValueError("query_index out of range")
    disagreements = [
        actual != rival for actual, rival in zip(actual_outputs, rival_outputs)
    ]
    demonstrations = [index for index in range(len(disagreements)) if index != query_index]
    refuting = [index for index in demonstrations if disagreements[index]]
    return {
        "query_index": query_index,
        "demonstration_indices": demonstrations,
        "refuting_demonstration_indices": refuting,
        "identifiable": bool(refuting),
        "query_requires_parameter": disagreements[query_index],
    }


def build_report(
    *,
    root: Path | str,
    seeds: dict[int, int] | None = None,
) -> dict[str, Any]:
    """Execute both complete Racket settings and retain bounded evidence."""
    root = Path(root).resolve()
    seeds = dict(seeds or {1: 20, 2: 21})
    if set(seeds) != set(ALLOWED_PROJECTION_SPANS):
        raise ValueError(
            f"seeds must have exactly keys {ALLOWED_PROJECTION_SPANS}; got {sorted(seeds)}"
        )
    for span, seed in seeds.items():
        if choose_projection_span(seed) != span:
            raise ValueError(
                f"seed {seed} selects {choose_projection_span(seed)}, not span {span}"
            )

    module, selected_source_path, selected_source_sha = load_selected_generator(
        TASK_ID, root=root
    )
    sources = {
        span: racket_source(span, root=root) for span in ALLOWED_PROJECTION_SPANS
    }
    if sources[1] != _canonical_source(root=root):
        raise AssertionError("span 1 is not byte-exact canonical source")
    if normalized_hash(sources[1]) != module.RULE_HASH:
        raise AssertionError("span 1 no longer matches selected RULE_HASH")
    for span, source in sources.items():
        retained = rule_path(span).read_text(encoding="utf-8")
        if retained != source:
            raise AssertionError(f"retained span-{span}.rkt differs from source")

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_inputs = [pair["input"] for pair in canonical]
    canonical_actual = _racket_outputs(sources[1], canonical_inputs)
    canonical_matches = [
        actual == pair["output"] for actual, pair in zip(canonical_actual, canonical)
    ]
    if not all(canonical_matches):
        raise AssertionError("byte-exact span 1 failed a canonical labelled pair")

    settings: dict[str, Any] = {}
    public: dict[str, Any] = {}
    total_rotations = 0
    identifiable_rotations = 0
    for span in ALLOWED_PROJECTION_SPANS:
        rival = 2 if span == 1 else 1
        episode = build_episode(root=root, seed=seeds[span])
        if episode["parameter"] != {"projection_span": span}:
            raise AssertionError("episode seed did not select the expected span")
        pairs = [*episode["train"], *episode["test"]]
        inputs = [pair["input"] for pair in pairs]
        actual_outputs = _racket_outputs(sources[span], inputs)
        rival_outputs = _racket_outputs(sources[rival], inputs)
        mirror_outputs = [python_transform(grid, span) for grid in inputs]
        if actual_outputs != mirror_outputs:
            raise AssertionError(f"span {span}: Python/Racket output mismatch")

        executed_pairs = []
        for offset, (pair, actual, rival_output) in enumerate(
            zip(pairs, actual_outputs, rival_outputs)
        ):
            if pair["output"] != actual:
                raise AssertionError(f"span {span}: episode label mismatch at {offset}")
            split = "train" if offset < DEMONSTRATION_COUNT else "test"
            local_index = offset if split == "train" else offset - DEMONSTRATION_COUNT
            executed_pairs.append(
                {
                    "split": split,
                    "pair_index": local_index,
                    "episode_pair_index": pair["pair_index"],
                    "orientation": pair["orientation"],
                    "input": pair["input"],
                    "racket_output": actual,
                    "rival_projection_span": rival,
                    "rival_racket_output": rival_output,
                    "settings_disagree": actual != rival_output,
                    "input_sha256": _digest(pair["input"]),
                    "output_sha256": _digest(actual),
                }
            )

        rotations = [
            _lesson_gate(actual_outputs, rival_outputs, query_index=query_index)
            for query_index in range(PAIR_COUNT)
        ]
        total_rotations += len(rotations)
        identifiable_rotations += sum(row["identifiable"] for row in rotations)
        production = rotations[DEMONSTRATION_COUNT]
        if not production["identifiable"] or not production["query_requires_parameter"]:
            raise AssertionError(f"span {span}: production lesson is not identifiable")
        if not all(row["identifiable"] for row in rotations):
            raise AssertionError(f"span {span}: at least one query rotation is ambiguous")

        settings[str(span)] = {
            "projection_span": span,
            "is_canonical_default": span == DEFAULT_PROJECTION_SPAN,
            "seed": seeds[span],
            "racket_path": str(rule_path(span).relative_to(root)),
            "racket_text": sources[span],
            "racket_sha256": hashlib.sha256(sources[span].encode("utf-8")).hexdigest(),
            "racket_rule_hash": normalized_hash(sources[span]),
            "episode": episode,
            "executed_pairs": executed_pairs,
            "production_lesson": production,
            "query_rotations": rotations,
            "all_pairs_match_python_and_racket": True,
            "every_pair_refutes_rival": all(
                row["settings_disagree"] for row in executed_pairs
            ),
        }
        public[str(span)] = public_challenge(episode)

    source_paths = [
        Path(__file__).resolve(),
        PROTOTYPE_DIR / "README.md",
        root
        / "generators"
        / TASK_ID
        / "tests"
        / "test_parametric_projection_span.py",
    ]
    return {
        "schema": "arcpuzzles-parametric-projection-span-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "projection_span",
            "allowed_values": list(ALLOWED_PROJECTION_SPANS),
            "canonical_default": DEFAULT_PROJECTION_SPAN,
            "selection": "ALLOWED_PROJECTION_SPANS[seed % 2], once per episode",
            "input_constraints": (
                "Exactly one pair of opposite solid colored borders; color-1 markers "
                "in both axis halves; two disjoint background cells toward each "
                "marker's matching border."
            ),
        },
        "invariants_across_settings": [
            "one solid opposite-border pair and its two color roles",
            "color-1 marker positions and both projection-axis halves",
            "first half projects up/left; second half projects down/right",
            "projected cells use the matching border color",
            "only the contiguous projection length changes from one to two",
        ],
        "prototype_source_sha256": {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_paths
        },
        "selected_generator_path": str(selected_source_path.relative_to(root)),
        "selected_generator_sha256": selected_source_sha,
        "canonical_reference_unchanged": True,
        "canonical_labeled_pairs": len(canonical),
        "canonical_span_one_matches": sum(canonical_matches),
        "racket_runtime": _racket_runtime_metadata(),
        "settings": settings,
        "public_challenges": public,
        "lesson_census": {
            "episodes": len(ALLOWED_PROJECTION_SPANS),
            "demonstrations_per_episode": DEMONSTRATION_COUNT,
            "queries_per_episode": 1,
            "declared_rivals_per_episode": 1,
            "production_identifiable": sum(
                setting["production_lesson"]["identifiable"]
                for setting in settings.values()
            ),
            "production_total": len(settings),
            "query_rotations_identifiable": identifiable_rotations,
            "query_rotations_total": total_rotations,
        },
        "limits": [
            "Proposed task-local extension; not a production parametric API or approval.",
            "Bounded evidence for seeds 20 and 21 and only the declared span rival.",
            "The prototype sampler requires two clear ray cells, a stricter input "
            "domain than the canonical span-1 task.",
            "The selected generator and canonical Racket authority remain span 1.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    parser.add_argument("--span-one-seed", type=int, default=20)
    parser.add_argument("--span-two-seed", type=int, default=21)
    args = parser.parse_args()

    root = find_root(__file__)
    materialize_rules(root=root)
    report = build_report(
        root=root,
        seeds={1: args.span_one_seed, 2: args.span_two_seed},
    )
    report["execution"] = {"argv": list(sys.argv), "cwd": os.getcwd()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for span, challenge in report["public_challenges"].items():
            (args.write_public / f"span-{span}-public.json").write_text(
                json.dumps(challenge, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    print(
        json.dumps(
            {
                "status": report["status"],
                "parameter": report["parameter"],
                "canonical_span_one_matches": report[
                    "canonical_span_one_matches"
                ],
                "canonical_labeled_pairs": report["canonical_labeled_pairs"],
                "lesson_census": report["lesson_census"],
                "settings": {
                    span: {
                        "seed": setting["seed"],
                        "racket_sha256": setting["racket_sha256"],
                        "racket_rule_hash": setting["racket_rule_hash"],
                        "every_pair_refutes_rival": setting[
                            "every_pair_refutes_rival"
                        ],
                    }
                    for span, setting in report["settings"].items()
                },
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
