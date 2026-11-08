#!/usr/bin/env python3
"""Native authoring implementation for the 17de34436a9f rule family.

The hidden episode setting changes the direction in which corner positions are
read around the canvas.  The canonical/default setting is byte-for-byte the
selected Racket authority.  Inputs are matched across settings and include a
substantive boundary-touching 30x30 query.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "17de34436a9f"
ROTATION_SENSES = ("clockwise", "counterclockwise")
DEFAULT_ROTATION_SENSE = "clockwise"
CANONICAL_PROGRAM_SHA256 = (
    "9f94f78b9fd26ca22f06035669600941ff89acb16f31d9e422bb6a645fec6ff3"
)

CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (define (nonzero-cells grid) (filter (lambda (p) (not (= (at grid (first p) (second p)) 0))) (grid-positions grid))) (define (crop-nonzero grid) (let ((cells (nonzero-cells grid))) (if (empty? cells) (list (list 0)) (let* ((bb (bbox-of-cells cells))) (subgrid grid (first bb) (second bb) (third bb) (fourth bb)))))) (define (t13c-transform grid code) (cond ((= code 1) grid) ((= code 2) (rotate-cw grid)) ((= code 3) (rotate-180 grid)) ((= code 4) (rotate-ccw grid)) ((= code 5) (flip-lr grid)) (else grid))) (let* ((h (rows g)) (w (cols g)) (marker-info (first (filter (lambda (entry) (= (at g (first entry) (second entry)) 9)) (list (list 0 0 1) (list 0 (- w 1) 2) (list (- h 1) (- w 1) 3) (list (- h 1) 0 4))))) (work (set-cell g (first marker-info) (second marker-info) 0)) (obj (crop-nonzero work))) (t13c-transform obj (third marker-info)))))"

_CANONICAL_TRANSFORM = "(define (t13c-transform grid code) (cond ((= code 1) grid) ((= code 2) (rotate-cw grid)) ((= code 3) (rotate-180 grid)) ((= code 4) (rotate-ccw grid)) ((= code 5) (flip-lr grid)) (else grid)))"
_COUNTERCLOCKWISE_TRANSFORM = "(define (t13c-transform grid code) (cond ((= code 1) grid) ((= code 2) (rotate-ccw grid)) ((= code 3) (rotate-180 grid)) ((= code 4) (rotate-cw grid)) ((= code 5) (flip-lr grid)) (else grid)))"
if CANONICAL_PROGRAM.count(_CANONICAL_TRANSFORM) != 1:
    raise RuntimeError("canonical transform fragment is not unique")
COUNTERCLOCKWISE_PROGRAM = CANONICAL_PROGRAM.replace(
    _CANONICAL_TRANSFORM, _COUNTERCLOCKWISE_TRANSFORM
)
if hashlib.sha256(CANONICAL_PROGRAM.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256:
    raise RuntimeError("embedded canonical program bytes drifted")

# (input height, input width, marker corner, body bbox height, body bbox width)
# The first two demonstrations teach every corner used by the four queries.
# Later demonstrations add the remaining branches without changing queries.
DEMO_PROFILES = (
    (12, 14, "tr", 7, 8),
    (14, 15, "br", 8, 9),
    (11, 13, "tl", 6, 7),
    (15, 16, "bl", 9, 10),
    (18, 20, "tr", 12, 13),
    (20, 18, "bl", 13, 11),
)
QUERY_PROFILES = (
    (16, 19, "tr", 10, 12),
    (22, 25, "br", 16, 18),
    (27, 23, "br", 21, 17),
    (30, 30, "tr", 26, 24),
)

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CORNER_TURNS = {
    "clockwise": {"tl": 0, "tr": 1, "br": 2, "bl": 3},
    "counterclockwise": {"tl": 0, "tr": 3, "br": 2, "bl": 1},
}


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_setting(rotation_sense: Any) -> str:
    if type(rotation_sense) is not str or rotation_sense not in ROTATION_SENSES:
        raise ValueError(
            f"rotation_sense must be one of {ROTATION_SENSES}, got {rotation_sense!r}"
        )
    return rotation_sense


def _validate_count(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program_for(rotation_sense: str) -> str:
    rotation_sense = _validate_setting(rotation_sense)
    return (
        CANONICAL_PROGRAM
        if rotation_sense == "clockwise"
        else COUNTERCLOCKWISE_PROGRAM
    )


def _digest_int(seed: int, split: str, index: int, salt: int) -> int:
    payload = f"{TASK_ID}|{seed}|{split}|{index}|{salt}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _turn_clockwise(matrix: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*matrix[::-1], strict=True)]


def _rotated(matrix: list[list[int]], turns: int) -> list[list[int]]:
    result = copy.deepcopy(matrix)
    for _ in range(turns % 4):
        result = _turn_clockwise(result)
    return result


def _shape_lengths(
    seed: int, split: str, index: int, height: int, width: int
) -> tuple[int, ...]:
    """Construct a dense connected row-convex body with four distinct rotations."""
    for attempt in range(64):
        lengths = [
            1 + _digest_int(seed, split, index, 1000 + attempt * 100 + row) % width
            for row in range(height)
        ]
        # Exact bbox, visible irregularity, and a non-palindromic endpoint pair.
        lengths[1] = width
        lengths[0] = max(2, min(width - 1, width // 3 + 1))
        lengths[-1] = max(1, min(width - 2, width // 4 + (attempt % 2)))
        lengths[height // 2] = max(lengths[height // 2], width // 2 + 1)
        mask = [[1 if col < lengths[row] else 0 for col in range(width)]
                for row in range(height)]
        orbit = {
            json.dumps(_rotated(mask, turns), separators=(",", ":"))
            for turns in range(4)
        }
        if len(orbit) == 4:
            return tuple(lengths)
    raise RuntimeError("failed to construct an asymmetric body within bounded attempts")


def _marker_position(corner: str, height: int, width: int) -> tuple[int, int]:
    return {
        "tl": (0, 0),
        "tr": (0, width - 1),
        "br": (height - 1, width - 1),
        "bl": (height - 1, 0),
    }[corner]


def _opposite_origin(
    corner: str, height: int, width: int, body_h: int, body_w: int
) -> tuple[int, int]:
    return {
        "tl": (height - body_h, width - body_w),
        "tr": (height - body_h, 0),
        "br": (0, 0),
        "bl": (0, width - body_w),
    }[corner]


def make_input(seed: int, *, split: str, index: int) -> list[list[int]]:
    seed = _validate_seed(seed)
    if split not in {"demo", "query"}:
        raise ValueError("split must be 'demo' or 'query'")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    if index >= len(profiles):
        raise ValueError(f"{split} index {index} exceeds the supported profiles")
    height, width, corner, body_h, body_w = profiles[index]
    lengths = _shape_lengths(seed, split, index, body_h, body_w)
    row0, col0 = _opposite_origin(corner, height, width, body_h, body_w)
    marker_row, marker_col = _marker_position(corner, height, width)
    color = 1 + _digest_int(seed, split, index, 7) % 8

    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[marker_row][marker_col] = 9
    for row, length in enumerate(lengths):
        for col in range(length):
            grid[row0 + row][col0 + col] = color

    facts = analyze_input(grid)
    if facts["bbox_height"] != body_h or facts["bbox_width"] != body_w:
        raise AssertionError("constructed body bbox differs from its profile")
    return grid


def analyze_input(grid: Any) -> dict[str, Any]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC colors 0..9")
    height = len(grid)
    marker_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    if len(marker_cells) != 1:
        raise ValueError("input needs exactly one color-9 marker")
    corners = {
        (0, 0): "tl",
        (0, width - 1): "tr",
        (height - 1, width - 1): "br",
        (height - 1, 0): "bl",
    }
    if marker_cells[0] not in corners:
        raise ValueError("the marker must occupy a corner")

    body = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 9)
    ]
    if not body:
        raise ValueError("input needs a nonempty body")
    colors = {value for _, _, value in body}
    if len(colors) != 1:
        raise ValueError("the body must use exactly one nonzero non-9 color")
    positions = {(row, col) for row, col, _ in body}
    reached = {next(iter(positions))}
    frontier = list(reached)
    while frontier:
        row, col = frontier.pop()
        for d_row, d_col in _NEIGHBORS:
            neighbor = (row + d_row, col + d_col)
            if neighbor in positions and neighbor not in reached:
                reached.add(neighbor)
                frontier.append(neighbor)
    if reached != positions:
        raise ValueError("the body must be 4-connected")
    marker_row, marker_col = marker_cells[0]
    if any(
        max(abs(row - marker_row), abs(col - marker_col)) <= 1
        for row, col in positions
    ):
        raise ValueError("the body must be separated from the marker")

    min_row = min(row for row, _ in positions)
    max_row = max(row for row, _ in positions)
    min_col = min(col for _, col in positions)
    max_col = max(col for _, col in positions)
    return {
        "height": height,
        "width": width,
        "marker_corner": corners[marker_cells[0]],
        "marker_position": marker_cells[0],
        "body_color": next(iter(colors)),
        "body_positions": positions,
        "body_size": len(positions),
        "bbox": [min_row, min_col, max_row, max_col],
        "bbox_height": max_row - min_row + 1,
        "bbox_width": max_col - min_col + 1,
        "touches_boundary": any(
            row in {0, height - 1} or col in {0, width - 1}
            for row, col in positions
        ),
    }


def _body_crop(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze_input(grid)
    min_row, min_col, max_row, max_col = facts["bbox"]
    return [
        [grid[row][col] for col in range(min_col, max_col + 1)]
        for row in range(min_row, max_row + 1)
    ]


def intermediate_turns(grid: list[list[int]], rotation_sense: str) -> int:
    rotation_sense = _validate_setting(rotation_sense)
    corner = analyze_input(grid)["marker_corner"]
    return _CORNER_TURNS[rotation_sense][corner]


def apply_python(
    grid: list[list[int]], rotation_sense: str
) -> list[list[int]]:
    turns = intermediate_turns(grid, rotation_sense)
    return _rotated(_body_crop(grid), turns)


def _apply_fixed(grid: list[list[int]], turns: int) -> list[list[int]]:
    return _rotated(_body_crop(grid), turns)


def _apply_corner_override(
    grid: list[list[int]], rotation_sense: str, corner: str, turns: int
) -> list[list[int]]:
    facts = analyze_input(grid)
    actual = (
        turns
        if facts["marker_corner"] == corner
        else _CORNER_TURNS[rotation_sense][facts["marker_corner"]]
    )
    return _rotated(_body_crop(grid), actual)


def _apply_keep_marker(
    grid: list[list[int]], rotation_sense: str
) -> list[list[int]]:
    facts = analyze_input(grid)
    cells = [
        (row, col)
        for row in range(facts["height"])
        for col in range(facts["width"])
        if grid[row][col] != 0
    ]
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)
    crop = [
        [grid[row][col] for col in range(min_col, max_col + 1)]
        for row in range(min_row, max_row + 1)
    ]
    return _rotated(crop, _CORNER_TURNS[rotation_sense][facts["marker_corner"]])


def _rivals(rotation_sense: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    rotation_sense = _validate_setting(rotation_sense)
    other = next(value for value in ROTATION_SENSES if value != rotation_sense)
    return {
        f"declared_setting:{other}": lambda grid: apply_python(grid, other),
        "fixed_identity": lambda grid: _apply_fixed(grid, 0),
        "fixed_clockwise": lambda grid: _apply_fixed(grid, 1),
        "fixed_half_turn": lambda grid: _apply_fixed(grid, 2),
        "fixed_counterclockwise": lambda grid: _apply_fixed(grid, 3),
        "bottom_right_identity_clockwise": lambda grid: _apply_corner_override(
            grid, "clockwise", "br", 0
        ),
        "bottom_right_identity_counterclockwise": lambda grid: _apply_corner_override(
            grid, "counterclockwise", "br", 0
        ),
        "bottom_left_identity_clockwise": lambda grid: _apply_corner_override(
            grid, "clockwise", "bl", 0
        ),
        "bottom_left_identity_counterclockwise": lambda grid: _apply_corner_override(
            grid, "counterclockwise", "bl", 0
        ),
        f"keep_marker:{rotation_sense}": lambda grid: _apply_keep_marker(
            grid, rotation_sense
        ),
    }


def teaching_certificate(
    episode: dict[str, Any], rotation_sense: str
) -> dict[str, Any]:
    rotation_sense = _validate_setting(rotation_sense)
    demos = episode.get("train")
    queries = episode.get("test")
    if type(demos) is not list or type(queries) is not list or not demos or not queries:
        raise ValueError("episode must contain nonempty train/test lists")

    declared_setting_survivors = [
        setting
        for setting in ROTATION_SENSES
        if all(
            apply_python(pair["input"], setting) == pair["output"]
            for pair in demos
        )
    ]
    surviving_rivals: list[str] = []
    query_changing_survivors: list[str] = []
    refutations: dict[str, list[int]] = {}
    for name, rival in _rivals(rotation_sense).items():
        mismatches = [
            index
            for index, pair in enumerate(demos)
            if rival(pair["input"]) != pair["output"]
        ]
        refutations[name] = mismatches
        if not mismatches:
            surviving_rivals.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in queries):
                query_changing_survivors.append(name)
    return {
        "declared_setting_survivors": declared_setting_survivors,
        "surviving_rivals": surviving_rivals,
        "query_changing_survivors": query_changing_survivors,
        "demo_refutation_indices": refutations,
        "demos_checked": len(demos),
        "queries_checked": len(queries),
        "scope": "Finite declared settings and named shortcut rivals only.",
    }


def generate_episode(
    seed: int,
    *,
    rotation_sense: str,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _validate_seed(seed)
    rotation_sense = _validate_setting(rotation_sense)
    demos = _validate_count(demos, 2, 6, "demos")
    queries = _validate_count(queries, 1, 4, "queries")

    train = []
    for index in range(demos):
        grid = make_input(seed, split="demo", index=index)
        train.append({"input": grid, "output": apply_python(grid, rotation_sense)})
    test = []
    for index in range(queries):
        grid = make_input(seed, split="query", index=index)
        test.append({"input": grid, "output": apply_python(grid, rotation_sense)})

    identities = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in train + test
    ]
    if len(identities) != len(set(identities)):
        raise AssertionError("episode contains duplicate inputs")
    episode = {
        "schema": "17de34436a9f-parametric-episode-v1",
        "train": train,
        "test": test,
        "program_solution": program_for(rotation_sense),
        "settings": {"rotation_sense": rotation_sense},
        "seed": seed,
    }
    certificate = teaching_certificate(episode, rotation_sense)
    if certificate["declared_setting_survivors"] != [rotation_sense]:
        raise AssertionError("demonstrations do not uniquely identify the setting")
    if certificate["query_changing_survivors"]:
        raise AssertionError(
            "a named shortcut fits the demonstrations and changes a query: "
            + ", ".join(certificate["query_changing_survivors"])
        )
    episode["teaching_certificate"] = certificate
    return episode


def _racket_apply(bridge: Any, program: str, grid: list[list[int]]) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def write_evidence(out: Path, *, seed: int = 1701) -> dict[str, Any]:
    """Write a compact source-bound authoring sample with protected Racket labels."""
    from arc_repl.racket_bridge import RacketBridge

    seed = _validate_seed(seed)
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    public_dir = out / "public"
    private_dir = out / "private"
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)

    rows = []
    public_ids: set[str] = set()
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        runtime_identity = bridge.runtime_identity
        if runtime_identity.get("backend") != "racket" or runtime_identity.get("protected") is not True:
            raise RuntimeError("evidence requires protected Racket")
        for setting in ROTATION_SENSES:
            episode = generate_episode(
                seed, rotation_sense=setting, demos=3, queries=4
            )
            for split in ("train", "test"):
                for pair in episode[split]:
                    observed = _racket_apply(
                        bridge, episode["program_solution"], pair["input"]
                    )
                    if observed != pair["output"]:
                        raise AssertionError(
                            f"Racket/Python label mismatch for {setting}/{split}"
                        )
                    pair["output"] = observed
            certificate = teaching_certificate(episode, setting)
            if certificate["query_changing_survivors"]:
                raise AssertionError("retained lesson has a named ambiguity")

            visible = public_challenge_bytes(episode)
            public_id = public_challenge_id(episode)
            if public_id in public_ids:
                raise AssertionError("duplicate visible challenge")
            public_ids.add(public_id)
            public_path = public_dir / f"{public_id}.json"
            public_path.write_bytes(visible)
            private_path = private_dir / f"{setting}.json"
            private_path.write_text(
                json.dumps(episode, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            rows.append(
                {
                    "rotation_sense": setting,
                    "seed": seed,
                    "program_sha256": hashlib.sha256(
                        episode["program_solution"].encode()
                    ).hexdigest(),
                    "public_id": public_id,
                    "public_path": public_path.relative_to(out).as_posix(),
                    "private_path": private_path.relative_to(out).as_posix(),
                    "input_sizes": [
                        [len(pair["input"]), len(pair["input"][0])]
                        for pair in episode["train"] + episode["test"]
                    ],
                    "body_sizes": [
                        analyze_input(pair["input"])["body_size"]
                        for pair in episode["train"] + episode["test"]
                    ],
                    "certificate": certificate,
                }
            )

    # Bounded Python-only attack across seeds; Racket labels above and native
    # qualification independently execute the retained/fresh jobs.
    sweep_failures = []
    for sweep_seed in range(32):
        for setting in ROTATION_SENSES:
            for demo_count in range(2, 7):
                episode = generate_episode(
                    sweep_seed, rotation_sense=setting, demos=demo_count, queries=4
                )
                certificate = teaching_certificate(episode, setting)
                if (
                    certificate["declared_setting_survivors"] != [setting]
                    or certificate["query_changing_survivors"]
                ):
                    sweep_failures.append(
                        {
                            "seed": sweep_seed,
                            "rotation_sense": setting,
                            "demos": demo_count,
                            "certificate": certificate,
                        }
                    )

    two_demos = generate_episode(
        seed, rotation_sense="clockwise", demos=2, queries=4
    )
    one_query = generate_episode(
        seed, rotation_sense="clockwise", demos=3, queries=1
    )
    four_queries = generate_episode(
        seed, rotation_sense="clockwise", demos=3, queries=4
    )
    six_demos = generate_episode(
        seed, rotation_sense="clockwise", demos=6, queries=4
    )
    prefix_stable = (
        one_query["train"] == four_queries["train"]
        and one_query["test"] == four_queries["test"][:1]
        and two_demos["train"] == four_queries["train"][:2]
        and two_demos["test"] == four_queries["test"]
        and six_demos["train"][:3] == four_queries["train"]
        and six_demos["test"] == four_queries["test"]
    )
    if not prefix_stable or sweep_failures:
        raise AssertionError("bounded prefix/teaching audit failed")

    stress = four_queries["test"][3]["input"]
    stress_facts = analyze_input(stress)
    report = {
        "schema": "17de34436a9f-parametric-authoring-evidence-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "parameter": {
            "name": "rotation_sense",
            "values": list(ROTATION_SENSES),
            "default": DEFAULT_ROTATION_SENSE,
            "chosen_once_per_episode": True,
        },
        "episodes": rows,
        "racket": {
            key: runtime_identity[key]
            for key in runtime_identity
            if key
            in {
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            }
        },
        "racket_label_count": 2 * (3 + 4),
        "bounded_self_audit": {
            "seeds": 32,
            "settings": len(ROTATION_SENSES),
            "demo_counts": [2, 3, 4, 5, 6],
            "episodes": 32 * len(ROTATION_SENSES) * 5,
            "query_changing_named_survivors": 0,
            "failures": sweep_failures,
            "limits": "Finite named rivals and deterministic sampler seeds only.",
        },
        "count_independence": {
            "demos_supported": [2, 6],
            "queries_supported": [1, 4],
            "prefix_stable": prefix_stable,
        },
        "stress_30x30": {
            "input_size": [len(stress), len(stress[0])],
            "body_size": stress_facts["body_size"],
            "body_bbox": [stress_facts["bbox_height"], stress_facts["bbox_width"]],
            "touches_boundary": stress_facts["touches_boundary"],
            "marker_corner": stress_facts["marker_corner"],
        },
        "sequential_dependency": {
            "step_a": "Read the input marker corner and map it through the episode's rotation sense.",
            "intermediate": "An input-dependent quarter-turn count in {0,1,2,3}.",
            "step_b": "Remove the marker, crop the body, and rotate that crop by the derived turn count.",
            "why_b_depends_on_a": "The final orientation cannot be selected until the marker-derived turn count is known.",
            "candidate_witness": {"seed": seed, "split": "query", "index": 3},
        },
        "public_projection": "reviewer_support.public_challenge_bytes/public_challenge_id",
        "training_admitted": False,
    }
    (out / "report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1701)
    args = parser.parse_args()
    report = write_evidence(args.out, seed=args.seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": len(report["episodes"]),
                "racket_label_count": report["racket_label_count"],
                "bounded_self_audit": report["bounded_self_audit"]["episodes"],
                "stress_30x30": report["stress_30x30"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
