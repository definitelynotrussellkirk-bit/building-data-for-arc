#!/usr/bin/env python3
"""Proposed episode-level path-policy parameter for ARC family cb227835.

This module is deliberately task-local and unapproved.  The canonical
``both`` setting returns the exact ledger Racket source.  The two alternatives
remove exactly one guarded sibling loop from that source, so all labels remain
Racket-authoritative while the underlying endpoint/path reasoning is shared.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)


TASK_ID = "db63430eeffa"
ROOT = find_root(__file__)
PATH_POLICIES = ("both", "diagonal_first", "straight_first")
DEFAULT_PATH_POLICY = "both"
DEFAULT_DEMONSTRATION_COUNT = 3
MIN_DEMONSTRATION_COUNT = 2
MAX_DEMONSTRATION_COUNT = 6
DEFAULT_QUERY_COUNT = 4
PROTOTYPE_VERSION = "2.0.0"
CANONICAL_SOURCE_SHA256 = (
    "738576fedc01cbcd29e0e5a381777ed10929461bca3c60994cee0a3fb4010c46"
)
SEQUENTIAL_STEP_A = (
    "read the ordered color-8 endpoints and decompose their signed delta"
)
SEQUENTIAL_INTERMEDIATE = (
    "ordered endpoints, signed row/column deltas, row/column step signs, "
    "diagonal_steps, straight_steps, and major_is_row"
)
SEQUENTIAL_STEP_B = (
    "draw the selected diagonal/straight segment order using that decomposition"
)
SEQUENTIAL_WHY = (
    "B needs the endpoint-derived step signs, diagonal/straight lengths, "
    "and major axis; flipping only major_is_row changes the protected "
    "Racket output."
)

# Exact sibling expressions from the canonical program.  Source derivation is
# intentionally guarded by both the full-source hash and unique block counts.
DIAGONAL_FIRST_BLOCK = """(let loop1
                  ((rr r1) (cc c1) (step 0))
                  (cond
                    ((< step d-steps) (hash-set! path (list rr cc) #t)
                      (loop1 (+ rr sr) (+ cc sc) (+ step 1)))
                    (else (let loop2
                               ((rr rr) (cc cc) (step 0))
                               (cond
                                 ((< step s-steps) (hash-set! path (list rr cc) #t)
                                   (cond
                                     (major-is-r (loop2 (+ rr sr) cc (+ step 1)))
                                     (else (loop2 rr (+ cc sc) (+ step 1)))))
                                 (else (hash-set! path (list rr cc) #t)))))))"""

STRAIGHT_FIRST_BLOCK = """(let loop1
                  ((rr r1) (cc c1) (step 0))
                  (cond
                    ((< step s-steps) (hash-set! path (list rr cc) #t)
                      (cond
                        (major-is-r (loop1 (+ rr sr) cc (+ step 1)))
                        (else (loop1 rr (+ cc sc) (+ step 1)))))
                    (else (let loop2
                               ((rr rr) (cc cc) (step 0))
                               (cond
                                 ((< step d-steps) (hash-set! path (list rr cc) #t)
                                   (loop2 (+ rr sr) (+ cc sc) (+ step 1)))
                                 (else (hash-set! path (list rr cc) #t)))))))"""

DIAGONAL_FIRST_BLOCK_SHA256 = hashlib.sha256(
    DIAGONAL_FIRST_BLOCK.encode("utf-8")
).hexdigest()
STRAIGHT_FIRST_BLOCK_SHA256 = hashlib.sha256(
    STRAIGHT_FIRST_BLOCK.encode("utf-8")
).hexdigest()


def _validate_path_policy(path_policy: str) -> None:
    if type(path_policy) is not str or path_policy not in PATH_POLICIES:
        raise ValueError(
            f"path_policy must be one of {PATH_POLICIES}, got {path_policy!r}"
        )


def canonical_program(*, root: Path | None = None) -> str:
    """Return the one exact canonical Racket program from the local ledger."""
    active_root = ROOT if root is None else Path(root)
    matches: list[str] = []
    with canonical_path(active_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError(f"canonical record for {TASK_ID} lacks program_solution")
                matches.append(source)
    if not matches:
        raise ValueError(f"no canonical record found for {TASK_ID}")
    if len(set(matches)) != 1:
        raise ValueError(f"canonical variants for {TASK_ID} disagree on program_solution")
    return matches[0]


def derive_program(source: str, path_policy: str) -> str:
    """Derive one policy program from the exact canonical source."""
    _validate_path_policy(path_policy)
    if type(source) is not str:
        raise ValueError("canonical source must be text")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if digest != CANONICAL_SOURCE_SHA256:
        raise ValueError(
            "canonical source hash drifted; refusing unreviewed Racket derivation"
        )
    if source.count(DIAGONAL_FIRST_BLOCK) != 1:
        raise ValueError("canonical source does not contain one guarded diagonal-first loop")
    if source.count(STRAIGHT_FIRST_BLOCK) != 1:
        raise ValueError("canonical source does not contain one guarded straight-first loop")
    if path_policy == "both":
        return source
    if path_policy == "diagonal_first":
        return source.replace(STRAIGHT_FIRST_BLOCK, "", 1)
    return source.replace(DIAGONAL_FIRST_BLOCK, "", 1)


def program_for(path_policy: str = DEFAULT_PATH_POLICY, *, root: Path | None = None) -> str:
    """Materialize exact Racket for one proposed episode-level path policy."""
    return derive_program(canonical_program(root=root), path_policy)


def evaluate_racket(
    program: str,
    grid: list[list[int]],
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Evaluate a complete ``(rule! ...)`` program against one grid in Racket."""
    normalized = normalize_grid(grid)
    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    assert active is not None
    try:
        active.define_grid("g", normalized)
        result = active.eval_text(f"({strip_rule_wrapper(program)} g)")
        return normalize_grid(result)
    finally:
        if owns_bridge:
            active.shutdown()


_GENERATOR, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)

_DIFFICULTIES = ("easy", "medium", "hard")

# The first two demonstrations deliberately occupy opposite sides of four
# plausible shortcut features: orientation, major axis, border contact and
# scale.  This makes the minimum two-demo lesson identify the fixed policy
# against the declared conditional rivals.  Queries use an independent stream
# and include both the 7x7 and 30x30 supported boundaries.
_DEMONSTRATION_PROFILES = (
    # h, w, row gap, col gap, orientation, row anchor, column anchor
    (30, 30, 23, 8, "left_to_right", "top", "left"),
    (7, 7, 2, 4, "right_to_left", "interior", "interior"),
    (16, 18, 13, 5, "right_to_left", "bottom", "right"),
    (15, 18, 5, 14, "left_to_right", "interior", "left"),
    (13, 15, 10, 4, "left_to_right", "bottom", "interior"),
    (14, 15, 4, 11, "right_to_left", "top", "right"),
)
_QUERY_PROFILES = (
    (8, 10, 2, 7, "right_to_left", "top", "right"),
    (18, 17, 14, 5, "left_to_right", "bottom", "left"),
    (23, 28, 9, 16, "left_to_right", "interior", "interior"),
    (30, 30, 17, 26, "right_to_left", "bottom", "left"),
)
_ANCHORS = {"top", "bottom", "left", "right", "interior"}
MAJOR_AXIS_BINDING = "(major-is-r (> adr adc))"
WRONG_MAJOR_AXIS_BINDING = "(major-is-r (< adr adc))"



def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demonstration_count: int, query_count: int) -> None:
    if (
        type(demonstration_count) is not int
        or not MIN_DEMONSTRATION_COUNT
        <= demonstration_count
        <= MAX_DEMONSTRATION_COUNT
    ):
        raise ValueError(
            "demonstration_count must be an exact integer in 2..6"
        )
    if type(query_count) is not int or query_count != DEFAULT_QUERY_COUNT:
        raise ValueError("query_count must be the exact integer 4")


def _validate_difficulty(difficulty: str) -> None:
    if type(difficulty) is not str or difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")


def select_path_policy(seed: int) -> str:
    """Select one hidden policy from an episode-only deterministic stream."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:path-policy:{seed}".encode()).digest()
    return PATH_POLICIES[digest[0] % len(PATH_POLICIES)]


def _derived_seed(seed: int, stream: str, index: int, difficulty: str) -> int:
    payload = (
        f"{TASK_ID}:parametric-input:{difficulty}:{stream}:{seed}:{index}"
    ).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _grid_sha256(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _interior_anchor(limit: int, gap: int, token: int) -> int:
    low = 1
    high = limit - gap - 2
    if high < low:
        raise ValueError(
            f"profile {limit=} {gap=} has no placement with both endpoints interior"
        )
    return low + token % (high - low + 1)


def _axis_anchor(
    limit: int,
    gap: int,
    anchor: str,
    token: int,
    *,
    low_name: str,
    high_name: str,
) -> int:
    if anchor == low_name:
        return 0
    if anchor == high_name:
        return limit - gap - 1
    if anchor == "interior":
        return _interior_anchor(limit, gap, token)
    raise ValueError(f"unsupported {anchor=}")


def _build_profile_grid(
    seed: int,
    stream: str,
    index: int,
    difficulty: str,
    profile: tuple[int, int, int, int, str, str, str],
) -> dict[str, Any]:
    h, w, row_gap, col_gap, orientation, row_anchor, col_anchor = profile
    if not (7 <= h <= 30 and 7 <= w <= 30):
        raise ValueError("parametric profiles must stay in the 7..30 envelope")
    if not (2 <= row_gap < h and 2 <= col_gap < w and row_gap != col_gap):
        raise ValueError("parametric profiles need unequal row/column gaps >=2")
    if orientation not in {"left_to_right", "right_to_left"}:
        raise ValueError(f"unsupported orientation: {orientation}")
    if row_anchor not in _ANCHORS or col_anchor not in _ANCHORS:
        raise ValueError("unsupported profile anchor")

    token = _derived_seed(seed, stream, index, difficulty)
    r1 = _axis_anchor(
        h,
        row_gap,
        row_anchor,
        token,
        low_name="top",
        high_name="bottom",
    )
    left = _axis_anchor(
        w,
        col_gap,
        col_anchor,
        token >> 17,
        low_name="left",
        high_name="right",
    )
    r2 = r1 + row_gap
    if orientation == "left_to_right":
        c1, c2 = left, left + col_gap
    else:
        c1, c2 = left + col_gap, left

    grid = [[0 for _ in range(w)] for _ in range(h)]
    grid[r1][c1] = 8
    grid[r2][c2] = 8
    digest = _grid_sha256(grid)
    return {
        "grid": grid,
        "input_sha256": digest,
        "input_seed": token,
        "sample_index": index,
        "stream": stream,
        "geometry": {
            "grid_h": h,
            "grid_w": w,
            "row_gap": row_gap,
            "col_gap": col_gap,
            "orientation": orientation,
            "row_anchor": row_anchor,
            "col_anchor": col_anchor,
        },
    }


def _sample_inputs(
    seed: int,
    demonstration_count: int,
    query_count: int,
    difficulty: str,
) -> list[dict[str, Any]]:
    """Build prefix-stable demonstrations and an independent four-query stream."""
    demonstrations = [
        _build_profile_grid(
            seed,
            "demonstration",
            index,
            difficulty,
            _DEMONSTRATION_PROFILES[index],
        )
        for index in range(demonstration_count)
    ]
    queries = [
        _build_profile_grid(
            seed,
            "query",
            index,
            difficulty,
            _QUERY_PROFILES[index],
        )
        for index in range(query_count)
    ]
    rows = demonstrations + queries
    digests = [row["input_sha256"] for row in rows]
    if len(digests) != len(set(digests)):
        raise RuntimeError("parametric profile schedule emitted duplicate inputs")
    return rows


def _endpoint_features(grid: list[list[int]]) -> dict[str, bool]:
    normalized = normalize_grid(grid)
    h, w = len(normalized), len(normalized[0])
    endpoints = [
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value == 8
    ]
    if len(endpoints) != 2:
        raise ValueError("feature audit requires exactly two color-8 endpoints")
    (r1, c1), (r2, c2) = endpoints
    row_gap, col_gap = abs(r2 - r1), abs(c2 - c1)
    return {
        "orientation_left_to_right": c1 < c2,
        "major_axis_row": row_gap > col_gap,
        "border_contact": any(
            row in {0, h - 1} or col in {0, w - 1}
            for row, col in endpoints
        ),
        "large_grid": max(h, w) >= 16,
    }


def _shortcut_rivals(
    selected: str,
    grids: list[list[list[int]]],
    outputs: dict[str, list[list[list[int]]]],
    demonstration_count: int,
    query_count: int,
) -> list[dict[str, Any]]:
    selected_index = PATH_POLICIES.index(selected)
    fallback = PATH_POLICIES[(selected_index + 1) % len(PATH_POLICIES)]
    features = [_endpoint_features(grid) for grid in grids]
    rows: list[dict[str, Any]] = []
    for feature in (
        "orientation_left_to_right",
        "major_axis_row",
        "border_contact",
        "large_grid",
    ):
        for selected_when in (False, True):
            predicted = [
                outputs[selected][index]
                if values[feature] is selected_when
                else outputs[fallback][index]
                for index, values in enumerate(features)
            ]
            demo_mismatches = [
                index
                for index in range(demonstration_count)
                if predicted[index] != outputs[selected][index]
            ]
            query_mismatches = [
                index
                for index in range(query_count)
                if predicted[demonstration_count + index]
                != outputs[selected][demonstration_count + index]
            ]
            if not demo_mismatches:
                raise RuntimeError(
                    f"minimum demonstrations fail to refute {feature=} "
                    f"{selected_when=}"
                )
            if not query_mismatches:
                raise RuntimeError(
                    f"queries do not expose the consequence of {feature=} "
                    f"{selected_when=}"
                )
            rows.append(
                {
                    "name": f"conditional_{feature}_{str(selected_when).lower()}",
                    "feature": feature,
                    "selected_when_feature": selected_when,
                    "fallback_path_policy": fallback,
                    "status": "refuted_by_demonstrations",
                    "demonstration_mismatch_indices": demo_mismatches,
                    "query_mismatch_indices": query_mismatches,
                }
            )
    return rows



def build_episode(
    seed: int,
    path_policy: str | None = None,
    *,
    difficulty: str = "medium",
    demonstration_count: int = DEFAULT_DEMONSTRATION_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one private proposed episode with every label executed in Racket."""
    _validate_seed(seed)
    _validate_counts(demonstration_count, query_count)
    _validate_difficulty(difficulty)
    selected = select_path_policy(seed) if path_policy is None else path_policy
    _validate_path_policy(selected)
    active_root = ROOT if root is None else Path(root)

    samples = _sample_inputs(
        seed, demonstration_count, query_count, difficulty
    )
    programs = {
        policy: program_for(policy, root=active_root)
        for policy in PATH_POLICIES
    }
    outputs: dict[str, list[list[list[int]]]] = {
        policy: [] for policy in PATH_POLICIES
    }

    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    assert active is not None
    try:
        for sample in samples:
            for policy in PATH_POLICIES:
                outputs[policy].append(
                    evaluate_racket(programs[policy], sample["grid"], bridge=active)
                )
    finally:
        if owns_bridge:
            active.shutdown()

    for index in range(len(samples)):
        serialized = {
            json.dumps(outputs[policy][index], separators=(",", ":"))
            for policy in PATH_POLICIES
        }
        if len(serialized) != len(PATH_POLICIES):
            raise RuntimeError(
                f"sample {index} does not distinguish all path policies"
            )

    all_pairs = [
        {"input": sample["grid"], "output": outputs[selected][index]}
        for index, sample in enumerate(samples)
    ]
    rivals = []
    for rival in PATH_POLICIES:
        if rival == selected:
            continue
        demonstration_mismatches = [
            index
            for index in range(demonstration_count)
            if outputs[selected][index] != outputs[rival][index]
        ]
        query_mismatches = [
            index
            for index in range(query_count)
            if outputs[selected][demonstration_count + index]
            != outputs[rival][demonstration_count + index]
        ]
        if not demonstration_mismatches:
            raise RuntimeError(
                f"demonstrations do not refute path-policy rival {rival}"
            )
        if len(query_mismatches) != query_count:
            raise RuntimeError(
                f"not every query distinguishes path-policy rival {rival}"
            )
        rivals.append(
            {
                "path_policy": rival,
                "status": "refuted_by_demonstrations",
                "demonstration_mismatch_indices": demonstration_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )

    shortcut_rivals = _shortcut_rivals(
        selected,
        [sample["grid"] for sample in samples],
        outputs,
        demonstration_count,
        query_count,
    )

    selected_program = programs[selected]
    try:
        source_path = str(GENERATOR_PATH.relative_to(active_root))
    except ValueError:
        source_path = str(GENERATOR_PATH)
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {"path_policy": selected},
        "selection_scope": "once_per_episode",
        "seed": seed,
        "difficulty": difficulty,
        "demonstration_count": demonstration_count,
        "query_count": query_count,
        "train": all_pairs[:demonstration_count],
        "test": all_pairs[demonstration_count:],
        "program": selected_program,
        "program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
        "programs_sha256": {
            policy: hashlib.sha256(program.encode()).hexdigest()
            for policy, program in programs.items()
        },
        "parameter_rivals": rivals,
        "shortcut_rivals": shortcut_rivals,
        "ambiguities": [],
        "sampling": [
            {
                key: sample[key]
                for key in (
                    "input_sha256",
                    "input_seed",
                    "sample_index",
                    "stream",
                    "geometry",
                )
            }
            for sample in samples
        ],
        "racket_evaluation_count": len(samples) * len(PATH_POLICIES),
        "input_constraints": {
            "endpoint_count": 2,
            "endpoint_color": 8,
            "background_color": 0,
            "minimum_row_gap": 2,
            "minimum_col_gap": 2,
            "row_and_col_gaps_must_differ": True,
            "reason": "all three path policies must produce distinct labels",
        },
        "source": {
            "generator_path": source_path,
            "generator_sha256": GENERATOR_SHA256,
            "canonical_program_sha256": CANONICAL_SOURCE_SHA256,
        },
    }


def verify_episode(
    episode: dict[str, Any],
    *,
    root: Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Re-execute a private episode under every rival and report invariants."""
    errors: list[str] = []
    if not isinstance(episode, dict):
        raise ValueError("episode must be a mapping")
    try:
        selected = episode["parameters"]["path_policy"]
    except (KeyError, TypeError) as exc:
        raise ValueError("episode is missing parameters.path_policy") from exc
    _validate_path_policy(selected)
    active_root = ROOT if root is None else Path(root)
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    pairs = train + test
    serialized_inputs: set[str] = set()
    for index, pair in enumerate(pairs):
        try:
            grid = normalize_grid(pair["input"])
            output = normalize_grid(pair["output"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"pair {index} malformed: {exc}")
            continue
        digest = json.dumps(grid, separators=(",", ":"))
        if digest in serialized_inputs:
            errors.append(f"pair {index} duplicates an earlier input")
        serialized_inputs.add(digest)
        if output != pair["output"]:
            errors.append(f"pair {index} output is not normalized")

    programs = {
        policy: program_for(policy, root=active_root)
        for policy in PATH_POLICIES
    }
    outputs: dict[str, list[list[list[int]]]] = {
        policy: [] for policy in PATH_POLICIES
    }
    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    assert active is not None
    try:
        for pair in pairs:
            grid = normalize_grid(pair["input"])
            for policy in PATH_POLICIES:
                outputs[policy].append(
                    evaluate_racket(programs[policy], grid, bridge=active)
                )
    finally:
        if owns_bridge:
            active.shutdown()

    for index, pair in enumerate(pairs):
        expected = normalize_grid(pair["output"])
        if outputs[selected][index] != expected:
            errors.append(f"pair {index} label disagrees with selected Racket program")
        if len({
            json.dumps(outputs[policy][index], separators=(",", ":"))
            for policy in PATH_POLICIES
        }) != len(PATH_POLICIES):
            errors.append(f"pair {index} does not distinguish all path policies")

    for rival in PATH_POLICIES:
        if rival == selected:
            continue
        demo_mismatches = [
            index
            for index in range(len(train))
            if outputs[selected][index] != outputs[rival][index]
        ]
        query_mismatches = [
            index
            for index in range(len(test))
            if outputs[selected][len(train) + index]
            != outputs[rival][len(train) + index]
        ]
        if not demo_mismatches:
            errors.append(f"demonstrations do not refute rival {rival}")
        if len(query_mismatches) != len(test):
            errors.append(f"some queries do not distinguish rival {rival}")

    shortcut_rows = _shortcut_rivals(
        selected,
        [normalize_grid(pair["input"]) for pair in pairs],
        outputs,
        len(train),
        len(test),
    )
    shortcut_survivors = [
        row["name"]
        for row in shortcut_rows
        if not row["demonstration_mismatch_indices"]
    ]
    if shortcut_survivors:
        errors.append(
            "declared shortcut rivals survive demonstrations: "
            + ", ".join(shortcut_survivors)
        )
    if episode.get("shortcut_rivals") != shortcut_rows:
        errors.append("stored shortcut-rival certificate differs from recomputation")

    if episode.get("program") != programs[selected]:
        errors.append("private program is not the selected exact Racket source")
    if episode.get("selection_scope") != "once_per_episode":
        errors.append("selection_scope is not once_per_episode")
    return {
        "schema": "arcpuzzles-parametric-episode-verification-v1",
        "task_id": TASK_ID,
        "path_policy": selected,
        "pair_count": len(pairs),
        "demonstration_count": len(train),
        "query_count": len(test),
        "racket_evaluation_count": len(pairs) * len(PATH_POLICIES),
        "shortcut_survivors": shortcut_survivors,
        "errors": errors,
        "passed": not errors,
    }


def path_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    """Return the input-dependent decomposition consumed by path drawing."""
    normalized = normalize_grid(grid)
    endpoints = [
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value == 8
    ]
    if len(endpoints) != 2:
        raise ValueError("path decomposition requires exactly two color-8 endpoints")
    (r1, c1), (r2, c2) = endpoints
    dr, dc = r2 - r1, c2 - c1
    if abs(dr) < 2 or abs(dc) < 2 or abs(dr) == abs(dc):
        raise ValueError("witness input needs unequal row/column gaps of at least two")
    return {
        "ordered_endpoints": [[r1, c1], [r2, c2]],
        "dr": dr,
        "dc": dc,
        "row_step": 1 if dr > 0 else -1,
        "col_step": 1 if dc > 0 else -1,
        "diagonal_steps": min(abs(dr), abs(dc)),
        "straight_steps": abs(abs(dr) - abs(dc)),
        "major_is_row": abs(dr) > abs(dc),
    }


def wrong_major_axis_program(
    path_policy: str = DEFAULT_PATH_POLICY,
    *,
    root: Path | None = None,
) -> str:
    """Flip only the A-stage major-axis intermediate in exact Racket source."""
    source = program_for(path_policy, root=root)
    if source.count(MAJOR_AXIS_BINDING) != 1:
        raise ValueError("selected program lacks one guarded major-axis binding")
    return source.replace(MAJOR_AXIS_BINDING, WRONG_MAJOR_AXIS_BINDING, 1)


def build_sequential_dependency_witness(
    grid: list[list[int]],
    path_policy: str = DEFAULT_PATH_POLICY,
    *,
    root: Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Execute a protected wrong-intermediate witness for the A→B dependency."""
    _validate_path_policy(path_policy)
    normalized = normalize_grid(grid)
    intermediate = path_intermediate(normalized)
    selected_program = program_for(path_policy, root=root)
    wrong_program = wrong_major_axis_program(path_policy, root=root)

    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    assert active is not None
    try:
        correct = evaluate_racket(selected_program, normalized, bridge=active)
        wrong = evaluate_racket(wrong_program, normalized, bridge=active)
        runtime_identity = dict(active.runtime_identity)
    finally:
        if owns_bridge:
            active.shutdown()
    differing_cells = [
        [row, col]
        for row in range(len(correct))
        for col in range(len(correct[0]))
        if correct[row][col] != wrong[row][col]
    ]
    if not differing_cells:
        raise RuntimeError("flipped major-axis intermediate did not change the output")
    wrong_intermediate = dict(intermediate)
    wrong_intermediate["major_is_row"] = not intermediate["major_is_row"]
    return {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "task_id": TASK_ID,
        "setting": {"path_policy": path_policy},
        "step_a": SEQUENTIAL_STEP_A,
        "intermediate": intermediate,
        "wrong_intermediate": wrong_intermediate,
        "step_b": SEQUENTIAL_STEP_B,
        "why_b_depends_on_a": SEQUENTIAL_WHY,
        "input": normalized,
        "correct_program": selected_program,
        "correct_program_sha256": hashlib.sha256(
            selected_program.encode("utf-8")
        ).hexdigest(),
        "wrong_intermediate_program": wrong_program,
        "wrong_intermediate_program_sha256": hashlib.sha256(
            wrong_program.encode("utf-8")
        ).hexdigest(),
        "correct_output": correct,
        "wrong_intermediate_output": wrong,
        "differing_cell_count": len(differing_cells),
        "differing_cells": differing_cells,
        "racket": runtime_identity,
    }


def build_admission_witness(
    detailed_witness: dict[str, Any], source_binding: dict[str, Any]
) -> dict[str, Any]:
    """Project a protected detailed witness into the native replay contract."""
    if not isinstance(detailed_witness, dict):
        raise TypeError("detailed_witness must be an object")
    if detailed_witness.get("schema") != "arcpuzzles-sequential-dependency-witness-v1":
        raise ValueError("detailed witness has the wrong schema")
    if not isinstance(source_binding, dict) or source_binding.get("task_id") != TASK_ID:
        raise ValueError("source_binding must name this task")
    if detailed_witness.get("racket", {}).get("protected") is not True:
        raise ValueError("detailed witness is not protected-Racket evidence")

    required = (
        "setting",
        "input",
        "intermediate",
        "wrong_intermediate",
        "correct_program",
        "wrong_intermediate_program",
        "correct_output",
        "wrong_intermediate_output",
        "differing_cell_count",
    )
    missing = [name for name in required if name not in detailed_witness]
    if missing:
        raise ValueError(f"detailed witness is missing: {', '.join(missing)}")
    if detailed_witness["correct_output"] == detailed_witness["wrong_intermediate_output"]:
        raise ValueError("counterfactual witness does not change the final output")
    if any(
        type(detailed_witness[name]) is not str or not detailed_witness[name].strip()
        for name in ("correct_program", "wrong_intermediate_program")
    ):
        raise ValueError("counterfactual witness programs must be nonempty text")

    # A JSON round trip makes the artifact independent of later caller mutation
    # while retaining the exact values hashed by native qualification.
    binding_copy = json.loads(
        json.dumps(
            source_binding,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    case = {
        "input": detailed_witness["input"],
        "settings": detailed_witness["setting"],
        "intermediate_value": detailed_witness["intermediate"],
        "counterfactual_intermediate_value": detailed_witness["wrong_intermediate"],
        "ablation": "wrong_intermediate",
        "program": detailed_witness["correct_program"],
        "counterfactual_program": detailed_witness["wrong_intermediate_program"],
        "output": detailed_witness["correct_output"],
        "counterfactual_output": detailed_witness["wrong_intermediate_output"],
        "differing_cell_count": detailed_witness["differing_cell_count"],
    }
    return {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "task_id": TASK_ID,
        "source_binding": binding_copy,
        "racket": {"backend": "racket", "protected": True},
        "step_a": SEQUENTIAL_STEP_A,
        "intermediate": SEQUENTIAL_INTERMEDIATE,
        "step_b": SEQUENTIAL_STEP_B,
        "why_b_depends_on_a": SEQUENTIAL_WHY,
        "cases": [case],
        "limits": (
            "One bounded authored wrong-intermediate counterfactual; this is not "
            "a universal proof of algorithmic depth."
        ),
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    """Canonical bytes of visible demonstrations and answer-free queries."""
    return _public_challenge_bytes(episode)


def public_id(episode: dict[str, Any]) -> str:
    """Opaque content ID derived only from public bytes."""
    return _public_challenge_id(episode)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project a private episode to its public ARC challenge."""
    return json.loads(public_bytes(episode))


def public_filename(episode: dict[str, Any]) -> str:
    """Return a setting/seed-free content-derived public filename."""
    return f"challenge-{public_id(episode)}.json"


def write_public_batch(
    episodes: Iterable[dict[str, Any]],
    destination: Path,
) -> list[Path]:
    """Write a sorted public-only batch, rejecting duplicate visible content."""
    rows = []
    seen: set[str] = set()
    for episode in episodes:
        identifier = public_id(episode)
        if identifier in seen:
            raise ValueError(f"duplicate visible challenge payload: {identifier}")
        seen.add(identifier)
        rows.append((identifier, public_bytes(episode)))
    if not rows:
        raise ValueError("at least one episode is required")
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"public destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    paths = []
    for identifier, payload in sorted(rows):
        path = destination / f"challenge-{identifier}.json"
        path.write_bytes(payload)
        paths.append(path)
    return paths
