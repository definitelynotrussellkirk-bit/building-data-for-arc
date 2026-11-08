#!/usr/bin/env python3
"""Proposed episode-fixed rule variant for ARC task 42f19ef6d600.

This prototype leaves the production generator and canonical rule untouched.
It varies one hidden episode parameter, ``branch_map``:

* ``canonical``: solid square-bbox objects get complete exterior side strips;
  non-solid square-bbox objects get eight axial corner-adjacent marks.
* ``swapped``: the two mark geometries exchange branches.

Every retained label is produced by the protected Racket bridge.  A separate
Python implementation is used only as a parity check and verifier.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "42f19ef6d600"
SCHEMA = "arcpuzzles-42f19ef6d600-parametric-private-v1"
PROTOTYPE_STATUS = "proposed"
BRANCH_MAPS = ("canonical", "swapped")
CANONICAL_DEFAULT = "canonical"
DEMO_PROFILES = ("solid_square", "hollow_square", "mixed_solid_hollow", "blocked_marks")
QUERY_PROFILES = (
    "size_six_hollow",
    "nonsquare_decoys",
    "same_color_nested",
    "edge_clipped",
    "irregular_square",
    "three_squares",
    "four_squares",
    "solid_square",
)
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_ROOT = find_root(__file__)


CANONICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (bg 7)
                (objs (objects g bg)))
           (reduce (lambda (acc obj)
                     (let* ((bb (obj-bbox obj))
                            (r1 (first bb))
                            (c1 (second bb))
                            (r2 (third bb))
                            (c2 (fourth bb))
                            (bh (+ 1 (- r2 r1)))
                            (bw (+ 1 (- c2 c1)))
                            (solid (= (obj-size obj) (* bh bw)))
                            (marks (if solid
                                       (append (map (lambda (c) (list (- r1 1) c))
                                                    (range c1 (+ c2 1)))
                                               (map (lambda (c) (list (+ r2 1) c))
                                                    (range c1 (+ c2 1)))
                                               (map (lambda (r) (list r (- c1 1)))
                                                    (range r1 (+ r2 1)))
                                               (map (lambda (r) (list r (+ c2 1)))
                                                    (range r1 (+ r2 1))))
                                       (list (list (- r1 1) c1)
                                             (list (- r1 1) c2)
                                             (list (+ r2 1) c1)
                                             (list (+ r2 1) c2)
                                             (list r1 (- c1 1))
                                             (list r2 (- c1 1))
                                             (list r1 (+ c2 1))
                                             (list r2 (+ c2 1))))))
                       (if (and (= bh bw) (>= bh 2))
                           (reduce (lambda (a p)
                                     (let* ((r (first p))
                                            (c (second p)))
                                       (if (and
                                             (>= r 0)
                                             (< r h)
                                             (>= c 0)
                                             (< c w)
                                             (= (at g r c) bg))
                                           (set-cell a r c 2)
                                           a)))
                                   acc
                                   marks)
                           acc)))
                   g
                   objs))))"""

SWAPPED_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (bg 7)
                (objs (objects g bg)))
           (reduce (lambda (acc obj)
                     (let* ((bb (obj-bbox obj))
                            (r1 (first bb))
                            (c1 (second bb))
                            (r2 (third bb))
                            (c2 (fourth bb))
                            (bh (+ 1 (- r2 r1)))
                            (bw (+ 1 (- c2 c1)))
                            (solid (= (obj-size obj) (* bh bw)))
                            (marks (if solid
                                       (list (list (- r1 1) c1)
                                             (list (- r1 1) c2)
                                             (list (+ r2 1) c1)
                                             (list (+ r2 1) c2)
                                             (list r1 (- c1 1))
                                             (list r2 (- c1 1))
                                             (list r1 (+ c2 1))
                                             (list r2 (+ c2 1)))
                                       (append (map (lambda (c) (list (- r1 1) c))
                                                    (range c1 (+ c2 1)))
                                               (map (lambda (c) (list (+ r2 1) c))
                                                    (range c1 (+ c2 1)))
                                               (map (lambda (r) (list r (- c1 1)))
                                                    (range r1 (+ r2 1)))
                                               (map (lambda (r) (list r (+ c2 1)))
                                                    (range r1 (+ r2 1)))))))
                       (if (and (= bh bw) (>= bh 2))
                           (reduce (lambda (a p)
                                     (let* ((r (first p))
                                            (c (second p)))
                                       (if (and
                                             (>= r 0)
                                             (< r h)
                                             (>= c 0)
                                             (< c w)
                                             (= (at g r c) bg))
                                           (set-cell a r c 2)
                                           a)))
                                   acc
                                   marks)
                           acc)))
                   g
                   objs))))"""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value))


def _normalized_rule_hash(source: str) -> str:
    return _sha256_bytes(" ".join(source.split()).encode())[:12]


def _validate_branch_map(branch_map: str) -> str:
    if branch_map not in BRANCH_MAPS:
        raise ValueError(f"branch_map must be one of {BRANCH_MAPS}, got {branch_map!r}")
    return branch_map


def _validate_counts(demo_count: int, query_count: int) -> None:
    if type(demo_count) is not int or not 2 <= demo_count <= len(DEMO_PROFILES):
        raise ValueError(f"demo_count must be an integer in 2..{len(DEMO_PROFILES)}")
    if type(query_count) is not int or not 4 <= query_count <= len(QUERY_PROFILES):
        raise ValueError(f"query_count must be an integer in 4..{len(QUERY_PROFILES)}")


def racket_program(branch_map: str) -> str:
    """Return the exact Racket program for one episode setting."""
    _validate_branch_map(branch_map)
    return CANONICAL_PROGRAM if branch_map == "canonical" else SWAPPED_PROGRAM


def _normalize_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    rows: list[list[int]] = []
    width = None
    for row in grid:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError("grid rows must be nonempty lists")
        values = list(row)
        if width is None:
            width = len(values)
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in values):
            raise ValueError("grid cells must be integer ARC colors 0..9")
        rows.append(values)
    if any(value == 2 for row in rows for value in row):
        raise ValueError("input color 2 is reserved for output marks")
    return rows


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 7 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in _DIRS:
                    nr, nc = current_row + dr, current_col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            obj_height, obj_width = r2 - r1 + 1, c2 - c1 + 1
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "height": obj_height,
                    "width": obj_width,
                    "solid": len(cells) == obj_height * obj_width,
                }
            )
    return result


def _marks(obj: dict[str, Any], style: str) -> tuple[tuple[int, int], ...]:
    r1, c1, r2, c2 = obj["r1"], obj["c1"], obj["r2"], obj["c2"]
    if style == "side_strips":
        return tuple(
            [(r1 - 1, col) for col in range(c1, c2 + 1)]
            + [(r2 + 1, col) for col in range(c1, c2 + 1)]
            + [(row, c1 - 1) for row in range(r1, r2 + 1)]
            + [(row, c2 + 1) for row in range(r1, r2 + 1)]
        )
    if style == "corner_marks":
        return (
            (r1 - 1, c1),
            (r1 - 1, c2),
            (r2 + 1, c1),
            (r2 + 1, c2),
            (r1, c1 - 1),
            (r2, c1 - 1),
            (r1, c2 + 1),
            (r2, c2 + 1),
        )
    raise ValueError(f"unknown mark style {style!r}")


def _apply_styles(grid: Any, solid_style: str, nonsolid_style: str) -> list[list[int]]:
    source = _normalize_grid(grid)
    height, width = len(source), len(source[0])
    output = copy.deepcopy(source)
    for obj in _objects(source):
        if obj["height"] != obj["width"] or obj["height"] < 2:
            continue
        style = solid_style if obj["solid"] else nonsolid_style
        for row, col in _marks(obj, style):
            if 0 <= row < height and 0 <= col < width and source[row][col] == 7:
                output[row][col] = 2
    return output


def python_apply(grid: Any, branch_map: str) -> list[list[int]]:
    """Independent Python mirror used for parity checks, not label authority."""
    _validate_branch_map(branch_map)
    if branch_map == "canonical":
        return _apply_styles(grid, "side_strips", "corner_marks")
    return _apply_styles(grid, "corner_marks", "side_strips")


def _rival_output(grid: Any, rival: str) -> list[list[int]]:
    if rival == "always_side_strips":
        return _apply_styles(grid, "side_strips", "side_strips")
    if rival == "always_corner_marks":
        return _apply_styles(grid, "corner_marks", "corner_marks")
    raise ValueError(f"unknown rival {rival!r}")


def _execute_racket(program: str, inputs: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    bridge = RacketBridge()
    try:
        bridge.eval_text(f"(define __parametric_rule {wrap_rule(program)})")
        outputs: list[list[list[int]]] = []
        for index, grid in enumerate(inputs):
            name = f"__parametric_input_{index}"
            bridge.define_grid(name, grid)
            output = bridge.eval_text(f"(__parametric_rule {name})")
            outputs.append([[int(value) for value in row] for row in output])
        return outputs
    finally:
        bridge.shutdown()


def _derive_int(seed: int, split: str, index: int, profile: str) -> int:
    payload = f"{TASK_ID}|{seed}|{split}|{index}|{profile}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0x7FFFFFFF


def _sample_inputs(seed: int, demo_count: int, query_count: int) -> tuple[list[dict], list[dict], str]:
    module, _source_path, generator_sha256 = load_selected_generator(TASK_ID, root=_ROOT)
    rows: dict[str, list[dict]] = {"train": [], "test": []}
    schedule = {
        "train": DEMO_PROFILES[:demo_count],
        "test": QUERY_PROFILES[:query_count],
    }
    seen: set[bytes] = set()
    for split, profiles in schedule.items():
        for index, profile in enumerate(profiles):
            pair_seed = _derive_int(seed, split, index, profile)
            sample_index = _derive_int(seed ^ 0x42F19EF6, split, index, profile)
            grid = module.generate(
                pair_seed,
                sample_index,
                difficulty="medium",
                scene_profile=profile,
            )
            key = _canonical_json(grid)
            if key in seen:
                raise RuntimeError(f"duplicate input generated for profile {profile}")
            seen.add(key)
            rows[split].append(
                {
                    "profile": profile,
                    "sample_index": sample_index,
                    "input": copy.deepcopy(grid),
                }
            )
    return rows["train"], rows["test"], generator_sha256


def _verification_summary(train: list[dict], test: list[dict]) -> dict[str, Any]:
    pairs = train + test
    input_keys = [_canonical_json(pair["input"]) for pair in pairs]
    rivals = {}
    for rival in ("always_side_strips", "always_corner_marks"):
        rejected = [
            index
            for index, pair in enumerate(train)
            if _rival_output(pair["input"], rival) != pair["output"]
        ]
        rivals[rival] = {"rejected_by_demo_indices": rejected}
    return {
        "racket_pairs": len(pairs),
        "python_parity_pairs": len(pairs),
        "all_inputs_distinct": len(set(input_keys)) == len(input_keys),
        "rivals": rivals,
    }


def build_episode(
    seed: int,
    branch_map: str,
    demo_count: int = 4,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private episode and label every pair with protected Racket."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    _validate_branch_map(branch_map)
    _validate_counts(demo_count, query_count)
    train, test, generator_sha256 = _sample_inputs(seed, demo_count, query_count)
    program = racket_program(branch_map)
    pairs = train + test
    racket_outputs = _execute_racket(program, [pair["input"] for pair in pairs])
    for pair, output in zip(pairs, racket_outputs):
        python_output = python_apply(pair["input"], branch_map)
        if output != python_output:
            raise RuntimeError(f"Racket/Python parity failure for profile {pair['profile']}")
        pair["output"] = output
        pair["output_sha256"] = _sha256_json(output)

    verification = _verification_summary(train, test)
    if not verification["all_inputs_distinct"]:
        raise RuntimeError("episode contains duplicate inputs")
    for rival, receipt in verification["rivals"].items():
        if not receipt["rejected_by_demo_indices"]:
            raise RuntimeError(f"demonstrations do not reject {rival}")

    episode = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "prototype_status": PROTOTYPE_STATUS,
        "parameter": {
            "name": "branch_map",
            "value": branch_map,
            "allowed_values": list(BRANCH_MAPS),
            "canonical_default": CANONICAL_DEFAULT,
        },
        "seed": seed,
        "demo_count": demo_count,
        "query_count": query_count,
        "program": program,
        "program_sha256": _sha256_bytes(program.encode()),
        "program_normalized_hash": _normalized_rule_hash(program),
        "generator_source_sha256": generator_sha256,
        "prototype_source_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        "train": train,
        "test": test,
        "verification": verification,
    }
    return episode


def _expected_pair_keys() -> set[str]:
    return {"profile", "sample_index", "input", "output", "output_sha256"}


def verify_episode(episode: Any) -> dict[str, Any]:
    """Re-execute and validate one private episode; raise on any mismatch."""
    if not isinstance(episode, dict):
        raise ValueError("private episode must be an object")
    if episode.get("schema") != SCHEMA or episode.get("task_id") != TASK_ID:
        raise ValueError("private episode schema/task mismatch")
    if episode.get("prototype_status") != PROTOTYPE_STATUS:
        raise ValueError("prototype status mismatch")
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict):
        raise ValueError("missing parameter declaration")
    branch_map = parameter.get("value")
    _validate_branch_map(branch_map)
    expected_parameter = {
        "name": "branch_map",
        "value": branch_map,
        "allowed_values": list(BRANCH_MAPS),
        "canonical_default": CANONICAL_DEFAULT,
    }
    if parameter != expected_parameter:
        raise ValueError("parameter declaration mismatch")
    seed = episode.get("seed")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    demo_count, query_count = episode.get("demo_count"), episode.get("query_count")
    _validate_counts(demo_count, query_count)
    train, test = episode.get("train"), episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("train/test must be lists")
    if len(train) != demo_count or len(test) != query_count:
        raise ValueError("declared demo/query counts do not match pairs")
    expected_train, expected_test, generator_sha256 = _sample_inputs(
        seed, demo_count, query_count
    )
    for actual, expected in zip(train + test, expected_train + expected_test):
        provenance = {
            "profile": actual.get("profile") if isinstance(actual, dict) else None,
            "sample_index": actual.get("sample_index") if isinstance(actual, dict) else None,
            "input": actual.get("input") if isinstance(actual, dict) else None,
        }
        if provenance != expected:
            raise ValueError("pair sampler provenance mismatch")
    pairs = train + test
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != _expected_pair_keys():
            raise ValueError("private pair fields mismatch or contain pair-level parameters")
        _normalize_grid(pair["input"])
        if pair["output_sha256"] != _sha256_json(pair["output"]):
            raise ValueError("stored output hash mismatch")

    program = racket_program(branch_map)
    if episode.get("program") != program:
        raise ValueError("program does not match branch_map")
    if episode.get("program_sha256") != _sha256_bytes(program.encode()):
        raise ValueError("program SHA-256 mismatch")
    if episode.get("program_normalized_hash") != _normalized_rule_hash(program):
        raise ValueError("program normalized hash mismatch")
    if episode.get("generator_source_sha256") != generator_sha256:
        raise ValueError("generator source hash mismatch")
    if episode.get("prototype_source_sha256") != _sha256_bytes(Path(__file__).read_bytes()):
        raise ValueError("prototype source hash mismatch")

    input_keys = [_canonical_json(pair["input"]) for pair in pairs]
    if len(set(input_keys)) != len(input_keys):
        raise ValueError("episode inputs are not distinct")
    racket_outputs = _execute_racket(program, [pair["input"] for pair in pairs])
    for pair, output in zip(pairs, racket_outputs):
        if output != pair["output"]:
            raise ValueError(f"stored output is not the Racket label for profile {pair['profile']}")
        if python_apply(pair["input"], branch_map) != output:
            raise ValueError(f"Python parity mismatch for profile {pair['profile']}")

    expected_verification = _verification_summary(train, test)
    if episode.get("verification") != expected_verification:
        raise ValueError("verification summary mismatch")
    for rival, receipt in expected_verification["rivals"].items():
        if not receipt["rejected_by_demo_indices"]:
            raise ValueError(f"demonstrations do not reject {rival}")
    return {
        "ok": True,
        "branch_map": branch_map,
        "racket_pairs": len(pairs),
        "public_id": public_id(public_projection(episode)),
    }


def public_projection(private_episode: Any) -> dict[str, Any]:
    """Return only visible demonstrations and query inputs."""
    if not isinstance(private_episode, dict):
        raise ValueError("private episode must be an object")
    train = private_episode.get("train")
    test = private_episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("private episode is missing train/test pairs")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in test],
    }


def public_id(public_episode: Any) -> str:
    """Return the opaque ID derived from the exact standardized public bytes."""
    return public_challenge_id(public_episode)


def write_public_challenge(path: Path, public_episode: Any, *, force: bool) -> None:
    """Write exactly ``reviewer_support.public_challenge_bytes``."""
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {path}; pass --force explicitly")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(public_challenge_bytes(public_episode))


def verify_public_projection(private_episode: Any, public_episode: Any) -> dict[str, Any]:
    """Reject any public artifact that differs from the label-safe projection."""
    expected = public_projection(private_episode)
    if public_episode != expected:
        raise ValueError("public artifact differs from visible-only projection")
    if any(set(pair) != {"input"} for pair in public_episode["test"]):
        raise ValueError("public query labels leaked")
    return {"ok": True, "public_id": public_id(expected)}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {path}; pass --force explicitly")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="build private/public episode files")
    generate.add_argument("--branch-map", required=True, choices=BRANCH_MAPS)
    generate.add_argument("--seed", required=True, type=int)
    generate.add_argument("--demos", type=int, default=4)
    generate.add_argument("--queries", type=int, default=4)
    generate.add_argument("--private-out", required=True, type=Path)
    generate.add_argument("--public-dir", required=True, type=Path)
    generate.add_argument("--force", action="store_true")

    verify = subparsers.add_parser("verify", help="re-execute a private episode and optional public file")
    verify.add_argument("--private", required=True, type=Path)
    verify.add_argument("--public", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "generate":
        episode = build_episode(args.seed, args.branch_map, args.demos, args.queries)
        public = public_projection(episode)
        challenge_id = public_id(public)
        public_path = args.public_dir / f"challenge-{challenge_id}.json"
        for path in (args.private_out, public_path):
            if path.exists() and not args.force:
                raise FileExistsError(f"refusing to overwrite {path}; pass --force explicitly")
        _write_json(args.private_out, episode, force=args.force)
        write_public_challenge(public_path, public, force=args.force)
        print(
            json.dumps(
                {
                    "private": str(args.private_out),
                    "public": str(public_path),
                    "public_id": challenge_id,
                    "program_sha256": episode["program_sha256"],
                    "racket_pairs": episode["verification"]["racket_pairs"],
                },
                sort_keys=True,
            )
        )
        return 0

    private = _read_json(args.private)
    receipt = {"private": verify_episode(private)}
    if args.public is not None:
        receipt["public"] = verify_public_projection(private, _read_json(args.public))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
