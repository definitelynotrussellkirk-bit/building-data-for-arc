#!/usr/bin/env python3
"""Proposed episode-level proximity-radius extension for ARC task 19c5f15066d3.

The selected production generator and canonical Racket authority remain
unchanged.  This task-local prototype varies one hidden integer once per
complete episode: the maximum perpendicular distance from a marked row/column
at which a red object is recolored blue.  Radius 1 is the exact canonical rule.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "19c5f15066d3"
VERSION = "proposed-proximity-radius-v1"
ALLOWED_PROXIMITY_RADII = (0, 1, 2)
DEFAULT_PROXIMITY_RADIUS = 1
CANONICAL_SHA256 = "ed64ca10036251fa97fee353aa573bf2f3abc62f77cacc4992c5a765b7f48579"
CANONICAL_RULE_HASH = "1ffa1234962c"
MAX_EPISODE_PAIRS = 16

CANONICAL_TOUCH_BLOCK = """(or (member? c vcols)
                      (member? (- c 1) vcols)
                      (member? (+ c 1) vcols)
                      (member? r hrows)
                      (member? (- r 1) hrows)
                      (member? (+ r 1) hrows))"""

_ROOT = find_root(__file__)
_GENERATOR, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=_ROOT
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode())


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


def grid_sha256(grid) -> str:
    return _sha256_bytes(_json_bytes(grid))


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")


def _validate_radius(proximity_radius: int) -> None:
    if (
        type(proximity_radius) is not int
        or proximity_radius not in ALLOWED_PROXIMITY_RADII
    ):
        raise ValueError(
            "proximity_radius must be one of the exact integers "
            f"{ALLOWED_PROXIMITY_RADII}"
        )


def _validate_count(name: str, value: int) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive exact integer")


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256_text(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_TOUCH_BLOCK) != 1:
        raise ValueError("canonical source must contain exactly one pinned touch block")
    return source


def canonical_source(*, root=None) -> str:
    """Load and pin the selected canonical Racket source."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.append(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources[0])


def _touch_block(proximity_radius: int) -> str:
    _validate_radius(proximity_radius)
    clauses = []
    for coordinate, collection in (("c", "vcols"), ("r", "hrows")):
        clauses.append(f"(member? {coordinate} {collection})")
        for distance in range(1, proximity_radius + 1):
            clauses.append(
                f"(member? (- {coordinate} {distance}) {collection})"
            )
            clauses.append(
                f"(member? (+ {coordinate} {distance}) {collection})"
            )
    block = "(or " + clauses[0]
    block += "".join("\n                      " + item for item in clauses[1:])
    block += ")"
    return block


def materialize_rule(
    proximity_radius: int = DEFAULT_PROXIMITY_RADIUS,
    *,
    root=None,
    source: str | None = None,
) -> str:
    """Return exact executable Racket for one proposed radius setting."""
    _validate_radius(proximity_radius)
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    replacement = _touch_block(proximity_radius)
    if proximity_radius == DEFAULT_PROXIMITY_RADIUS:
        if replacement != CANONICAL_TOUCH_BLOCK:
            raise AssertionError("default touch block drifted from canonical source")
        return canonical
    return canonical.replace(CANONICAL_TOUCH_BLOCK, replacement, 1)


def normalized_program_hash(
    proximity_radius: int = DEFAULT_PROXIMITY_RADIUS,
    *,
    root=None,
) -> str:
    source = materialize_rule(proximity_radius, root=root)
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _object_line_distance(item: dict[str, Any], info: dict[str, Any]) -> int:
    distances = []
    for row, col in item["cells"]:
        distances.extend(abs(col - line) for line in info["vcols"])
        distances.extend(abs(row - line) for line in info["hrows"])
    if not distances:
        raise ValueError("input has no marked row or column")
    return min(distances)


def solve(grid, *, proximity_radius: int = DEFAULT_PROXIMITY_RADIUS):
    """Independent Python mirror of one proposed threshold setting."""
    _validate_radius(proximity_radius)
    info = _GENERATOR._analysis(grid)
    if info.get("errors"):
        raise ValueError(
            "invalid edge-line input: " + "; ".join(info["errors"])
        )
    output = [row[:] for row in grid]
    for row in info["hrows"]:
        for col in range(info["width"]):
            output[row][col] = 1
    for col in info["vcols"]:
        for row in range(info["height"]):
            output[row][col] = 1
    for item in info["red_objects"]:
        if _object_line_distance(item, info) <= proximity_radius:
            for row, col in item["cells"]:
                output[row][col] = 1
    return output


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    """Execute one exact materialized program with the included Racket bridge."""
    if not isinstance(program, str) or not program.startswith("(rule!"):
        raise ValueError("program must be materialized Racket rule text")
    info = _GENERATOR._analysis(grid)
    if info.get("errors"):
        raise ValueError(
            "invalid edge-line input: " + "; ".join(info["errors"])
        )
    body = _program_body(program)
    if bridge is None:
        with RacketBridge() as owned:
            owned.define_grid("g", grid)
            return owned.eval_text(body)
    bridge.define_grid("g", grid)
    return bridge.eval_text(body)


def _scene(seed: int, index: int):
    """Build one lawful scene with objects at distances 0, 1, 2, and 4."""
    rng = random.Random(f"{TASK_ID}:{VERSION}:input:{seed}:{index}")
    # The first sixteen indices have distinct base dimensions in four-by-four
    # blocks; object sizes and D4 orientation add further deterministic variety.
    height = 16 + (index % 4)
    width = 19 + ((index // 4) % 4)
    line_col = width // 2 + rng.choice((-1, 0, 1))
    line_col = max(5, min(line_col, width - 8))

    starts = (2, 5, 8, 11)
    heights = tuple(1 + rng.randrange(2) for _ in starts)
    widths = tuple(1 + rng.randrange(3) for _ in starts)
    intersect_left = line_col - rng.randrange(widths[0])
    rectangles = (
        (
            starts[0],
            intersect_left,
            starts[0] + heights[0] - 1,
            intersect_left + widths[0] - 1,
        ),
        (
            starts[1],
            line_col + 1,
            starts[1] + heights[1] - 1,
            line_col + widths[1],
        ),
        (
            starts[2],
            line_col + 2,
            starts[2] + heights[2] - 1,
            line_col + widths[2] + 1,
        ),
        (
            starts[3],
            line_col + 4,
            starts[3] + heights[3] - 1,
            line_col + widths[3] + 3,
        ),
    )
    grid = _GENERATOR._build_grid(
        (height, width),
        (line_col,),
        (),
        rectangles,
    )
    transform = _GENERATOR._TRANSFORMS[(seed + index * 3) % len(_GENERATOR._TRANSFORMS)]
    grid = _GENERATOR._transform(grid, transform)

    info = _GENERATOR._analysis(grid)
    if info.get("errors"):
        raise RuntimeError("constructed invalid proximity scene: " + "; ".join(info["errors"]))
    distances = sorted(_object_line_distance(item, info) for item in info["red_objects"])
    if distances != [0, 1, 2, 4]:
        raise RuntimeError(f"constructed scene lost distance witnesses: {distances}")
    return grid


def distinguishing_inputs(seed: int, count: int):
    """Return deterministic, pairwise-distinct inputs that separate all radii."""
    _validate_seed(seed)
    if type(count) is not int or not 1 <= count <= MAX_EPISODE_PAIRS:
        raise ValueError(
            f"count must be an exact integer in 1..{MAX_EPISODE_PAIRS}"
        )
    grids = [_scene(seed, index) for index in range(count)]
    hashes = [grid_sha256(grid) for grid in grids]
    if len(set(hashes)) != len(hashes):
        raise RuntimeError("deterministic scene family emitted duplicate inputs")
    return grids


def select_proximity_radius(seed: int) -> int:
    _validate_seed(seed)
    return ALLOWED_PROXIMITY_RADII[seed % len(ALLOWED_PROXIMITY_RADII)]


def make_episode(
    seed: int,
    *,
    proximity_radius: int | None = None,
    n_train: int = 3,
    n_test: int = 4,
    root=None,
) -> dict[str, Any]:
    """Build one fixed-setting proposed episode with separate demo/query counts."""
    _validate_seed(seed)
    _validate_count("n_train", n_train)
    _validate_count("n_test", n_test)
    if n_train + n_test > MAX_EPISODE_PAIRS:
        raise ValueError(
            f"pair count may not exceed {MAX_EPISODE_PAIRS}"
        )
    selected = (
        select_proximity_radius(seed)
        if proximity_radius is None
        else proximity_radius
    )
    _validate_radius(selected)

    inputs = distinguishing_inputs(seed, n_train + n_test)
    outputs = {
        radius: [solve(grid, proximity_radius=radius) for grid in inputs]
        for radius in ALLOWED_PROXIMITY_RADII
    }
    pairs = [
        {
            "input": copy.deepcopy(grid),
            "output": copy.deepcopy(output),
            "input_sha256": grid_sha256(grid),
            "output_sha256": grid_sha256(output),
        }
        for grid, output in zip(inputs, outputs[selected], strict=True)
    ]

    rival_rows = []
    ambiguities = []
    for radius in ALLOWED_PROXIMITY_RADII:
        demo_mismatches = [
            index
            for index in range(n_train)
            if outputs[radius][index] != outputs[selected][index]
        ]
        query_mismatches = [
            index
            for index in range(n_test)
            if outputs[radius][n_train + index]
            != outputs[selected][n_train + index]
        ]
        if radius == selected:
            status = "matches_episode"
        elif demo_mismatches:
            status = "refuted_by_demonstrations"
        elif query_mismatches:
            status = "ambiguous_query"
        else:
            status = "matches_episode"
        row = {
            "proximity_radius": radius,
            "racket_sha256": _sha256_text(
                materialize_rule(radius, root=root)
            ),
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": copy.deepcopy(outputs[radius][:n_train]),
            "query_predictions": copy.deepcopy(outputs[radius][n_train:]),
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(copy.deepcopy(row))

    program = materialize_rule(selected, root=root)
    source_path = Path(__file__).resolve()
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": {"proximity_radius": selected},
        "parameter_selection": (
            "one episode-level exact integer selected before input generation"
        ),
        "allowed_proximity_radii": list(ALLOWED_PROXIMITY_RADII),
        "canonical_default": DEFAULT_PROXIMITY_RADIUS,
        "counts": {"demonstrations": n_train, "queries": n_test},
        "input_constraint": (
            "every retained input has red rectangles at perpendicular distances "
            "0, 1, 2, and 4 from a paired marked line"
        ),
        "prototype_sha256": _sha256_bytes(source_path.read_bytes()),
        "selected_generator_sha256": _GENERATOR_SHA256,
        "canonical_source_sha256": CANONICAL_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "racket_source": program,
        "racket_sha256": _sha256_text(program),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return an explicit answer-masked allowlist view of one private episode."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a mapping")
    try:
        public = {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [
                {"input": pair["input"]}
                for pair in episode["test"]
            ],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("episode lacks complete train/test pairs") from error
    return copy.deepcopy(public)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--proximity-radius",
        type=int,
        choices=ALLOWED_PROXIMITY_RADII,
    )
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    episode = make_episode(
        args.seed,
        proximity_radius=args.proximity_radius,
        n_train=args.n_train,
        n_test=args.n_test,
    )
    payload = public_challenge(episode) if args.public else episode
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
