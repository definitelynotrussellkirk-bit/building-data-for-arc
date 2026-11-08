#!/usr/bin/env python3
"""Episode-level portal-phase family for 4cea2727fcf9.

The exact canonical program teleports through the color-4 pair both before and
after the color-3 checkpoint.  This family exposes that timing choice once per
episode while preserving the canonical default byte-for-byte:

* ``always``: canonical behavior.
* ``before_checkpoint``: portals teleport only while the checkpoint flag is false.
* ``after_checkpoint``: portals teleport only after the checkpoint flag is true.

Inputs are matched across settings.  The first two demonstrations are
constructive crossed controls: one makes only the pre-checkpoint portal use
causal, and one makes only the post-checkpoint use causal.  The Python solver is
an independent claim generator; protected Racket remains label authority.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)

TASK_ID = "4cea2727fcf9"
ALLOWED_PHASES = ("always", "before_checkpoint", "after_checkpoint")
DEFAULT_PHASE = "always"
DEFAULT_DEMOS = 2
DEFAULT_QUERIES = 4
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parent
CANONICAL_FILE = HOME / "canonical.rkt"
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_phase(portal_phase: str) -> None:
    if type(portal_phase) is not str or portal_phase not in ALLOWED_PHASES:
        raise ValueError(f"portal_phase must be one of {ALLOWED_PHASES}, got {portal_phase!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_grid(grid, *, name: str = "grid") -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError(f"{name} must be a nonempty rectangular grid")
    width = len(grid[0])
    if len(grid) > 30 or width > 30 or any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError(f"{name} must be rectangular 1..30 with exact colors 0..9")
    return len(grid), width


def canonical_source(*, root: Path = ROOT) -> str:
    """Return the frozen exact source and verify it against this checkout's ledger."""
    source = CANONICAL_FILE.read_text(encoding="utf-8")
    records = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    value = row.get("program_solution")
                    if isinstance(value, str):
                        records.append(value)
    if not records or len(set(records)) != 1:
        raise ValueError("expected one exact selected canonical program")
    if source != records[0]:
        raise ValueError("task-local canonical.rkt differs from selected canonical program")
    return source


def program_for(portal_phase: str = DEFAULT_PHASE, *, root: Path = ROOT) -> str:
    _validate_phase(portal_phase)
    source = canonical_source(root=root)
    if portal_phase == DEFAULT_PHASE:
        return source
    needle = "(define p2 (portal-exit (list nr nc)))"
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches the guarded portal patch")
    if portal_phase == "before_checkpoint":
        replacement = "(define p2 (if (not got) (portal-exit (list nr nc)) (list nr nc)))"
    else:
        replacement = "(define p2 (if got (portal-exit (list nr nc)) (list nr nc)))"
    return source.replace(needle, replacement)


def never_portal_program(*, root: Path = ROOT) -> str:
    """Rival that treats color-4 cells as ordinary walkable cells."""
    source = canonical_source(root=root)
    needle = "(define p2 (portal-exit (list nr nc)))"
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches the guarded portal patch")
    return source.replace(needle, "(define p2 (list nr nc))")


def checkpoint_skip_program(portal_phase: str, *, root: Path = ROOT) -> str:
    """Counterfactual that skips stage A by starting with checkpoint-state true."""
    source = program_for(portal_phase, root=root)
    needle = "(define start-state (list (first start) (second start) (equal? start check)))"
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches the guarded checkpoint patch")
    return source.replace(
        needle,
        "(define start-state (list (first start) (second start) #t))",
    )


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    """Execute one complete rule through protected Racket."""
    _validate_grid(grid)
    owns = bridge is None
    active = RacketBridge() if owns else bridge
    try:
        active.define_grid("g", grid)
        return active.eval_text(f"({wrap_rule(program)} g)")
    finally:
        if owns:
            active.shutdown()


def _positions(grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _portal_active(portal_phase: str, got_checkpoint: bool) -> bool:
    return (
        portal_phase == "always"
        or (portal_phase == "before_checkpoint" and not got_checkpoint)
        or (portal_phase == "after_checkpoint" and got_checkpoint)
    )


def _solve_states(grid, *, portal_phase: str, require_checkpoint: bool = True):
    """Mirror the exact state/neighbor order of the selected Racket BFS."""
    _validate_phase(portal_phase)
    h, w = _validate_grid(grid)
    starts, goals, checks, portals = (
        _positions(grid, 1),
        _positions(grid, 2),
        _positions(grid, 3),
        _positions(grid, 4),
    )
    if len(starts) != 1 or len(goals) != 1 or len(checks) != 1 or len(portals) not in (0, 2):
        raise ValueError("input needs one start/goal/checkpoint and zero or two portals")
    start, goal, check = starts[0], goals[0], checks[0]

    def portal_exit(point: tuple[int, int], got: bool) -> tuple[int, int]:
        if _portal_active(portal_phase, got) and point in portals:
            other = [candidate for candidate in portals if candidate != point]
            return other[0] if other else point
        return point

    initial_got = True if not require_checkpoint else start == check
    initial = (start[0], start[1], initial_got)
    queue = deque([initial])
    previous: dict[tuple[int, int, bool], tuple[int, int, bool] | None] = {initial: None}
    end = None
    while queue:
        r, c, got = queue.popleft()
        if (r, c) == goal and (got or not require_checkpoint):
            end = (r, c, got)
            break
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 8:
                continue
            pr, pc = portal_exit((nr, nc), got)
            new_got = got or grid[nr][nc] == 3
            state = (pr, pc, new_got)
            if state not in previous:
                previous[state] = (r, c, got)
                queue.append(state)
    if end is None:
        return []
    states = []
    current = end
    while current is not None:
        states.append(current)
        current = previous[current]
    states.reverse()
    return states


def python_mirror(grid, *, portal_phase: str = DEFAULT_PHASE, require_checkpoint: bool = True):
    """Independent deterministic label claim matching the Racket renderer."""
    states = _solve_states(
        grid,
        portal_phase=portal_phase,
        require_checkpoint=require_checkpoint,
    )
    out = copy.deepcopy(grid)
    for r, c, _ in states:
        if out[r][c] == 0:
            out[r][c] = 7
    return out


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return [row[:] for row in grid[::-1]]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _base_scene(profile: str, h: int, w: int):
    if profile not in {"pre", "post"}:
        raise ValueError("profile must be pre or post")
    if h < 9 or w < 12:
        raise ValueError("scene dimensions must be at least 9x12")
    grid = [[0 for _ in range(w)] for _ in range(h)]
    if profile == "pre":
        placements = (
            (1, 1, 1),
            (1, w - 2, 3),
            (h - 2, w // 2, 2),
            (1, 2, 4),
            (1, w - 3, 4),
        )
    else:
        placements = (
            (1, 1, 1),
            (1, 3, 3),
            (h - 2, w - 2, 2),
            (2, 3, 4),
            (h - 3, w - 2, 4),
        )
    for r, c, value in placements:
        if grid[r][c] != 0:
            raise ValueError("scene anchor collision")
        grid[r][c] = value
    return grid


def _decorate(grid, rng: random.Random, *, stress: bool) -> None:
    """Add spread-out boundary and interior walls, then let semantic filters decide."""
    h, w = len(grid), len(grid[0])
    # Boundary contacts are distractors, not a padded empty frame.
    for c in range(rng.randrange(3)):
        if grid[0][c] == 0:
            grid[0][c] = 8
    for c in range(rng.randrange(2), w, 4):
        if grid[h - 1][c] == 0:
            grid[h - 1][c] = 8
    for r in range(rng.randrange(3), h, 4):
        if grid[r][0] == 0:
            grid[r][0] = 8
    for r in range(rng.randrange(2), h, 5):
        if grid[r][w - 1] == 0:
            grid[r][w - 1] = 8

    density = 0.16 if stress else 0.085
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 and rng.random() < density:
                grid[r][c] = 8


def _profile_ok(grid, profile: str) -> bool:
    outputs = {phase: python_mirror(grid, portal_phase=phase) for phase in ALLOWED_PHASES}
    if any(output == grid for output in outputs.values()):
        return False
    if profile == "pre":
        relation = outputs["always"] == outputs["before_checkpoint"] != outputs["after_checkpoint"]
        # The first demo must also refute skipping the checkpoint stage.
        relation = relation and all(
            outputs[phase]
            != python_mirror(grid, portal_phase=phase, require_checkpoint=False)
            for phase in ALLOWED_PHASES
        )
        return relation
    return outputs["always"] == outputs["after_checkpoint"] != outputs["before_checkpoint"]


def _scene_rng(seed: int, index: int, attempt: int) -> random.Random:
    material = f"portal-phase-v2|{seed}|{index}|{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def make_scene(
    seed: int,
    index: int,
    *,
    profile: str,
    h: int,
    w: int,
    stress: bool = False,
):
    _validate_seed(seed)
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    for attempt in range(512):
        rng = _scene_rng(seed, index, attempt)
        grid = _base_scene(profile, h, w)
        transform = rng.randrange(4)
        if transform == 1:
            grid = _flip_lr(grid)
        elif transform == 2:
            grid = _flip_ud(grid)
        elif transform == 3:
            grid = _rotate_180(grid)
        _decorate(grid, rng, stress=stress)
        if not _profile_ok(grid, profile):
            continue
        if stress:
            walls = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
            if (
                len(walls) < 90
                or len({r for r, _ in walls}) < 20
                or len({c for _, c in walls}) < 20
                or not any(r in (0, h - 1) for r, _ in walls)
                or not any(c in (0, w - 1) for _, c in walls)
            ):
                continue
        return grid
    raise ValueError(
        f"could not construct a {profile} portal-phase scene for seed={seed}, index={index}, shape={h}x{w}"
    )


_DEMO_SHAPES = ((9, 12), (10, 14), (11, 15), (12, 16), (13, 17), (14, 18))
_QUERY_SHAPES = ((15, 19), (19, 23), (24, 27), (30, 30))


def grid_sha256(grid) -> str:
    _validate_grid(grid)
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def make_episode(
    seed: int,
    *,
    portal_phase: str = DEFAULT_PHASE,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
):
    _validate_seed(seed)
    _validate_phase(portal_phase)
    _validate_counts(demos, queries)
    inputs = []
    profiles = []
    for index in range(demos):
        profile = "pre" if index % 2 == 0 else "post"
        h, w = _DEMO_SHAPES[index]
        inputs.append(make_scene(seed, index, profile=profile, h=h, w=w))
        profiles.append(profile)
    for query_index, (h, w) in enumerate(_QUERY_SHAPES):
        profile = "pre" if query_index % 2 == 0 else "post"
        inputs.append(
            make_scene(
                seed,
                100 + query_index,
                profile=profile,
                h=h,
                w=w,
                stress=query_index == 3,
            )
        )
        profiles.append(profile)
    hashes = [grid_sha256(grid) for grid in inputs]
    if len(hashes) != len(set(hashes)):
        raise ValueError("episode inputs must be distinct")

    pairs = [
        {"input": grid, "output": python_mirror(grid, portal_phase=portal_phase)}
        for grid in inputs
    ]
    train, test = pairs[:demos], pairs[demos:]
    rivals = []
    for rival in ALLOWED_PHASES:
        if rival == portal_phase:
            continue
        mismatches = [
            i
            for i, pair in enumerate(train)
            if python_mirror(pair["input"], portal_phase=rival) != pair["output"]
        ]
        rivals.append(
            {
                "portal_phase": rival,
                "status": "refuted_by_demonstrations" if mismatches else "survived",
                "demonstration_mismatch_indices": mismatches,
            }
        )
    ambiguities = [row["portal_phase"] for row in rivals if not row["demonstration_mismatch_indices"]]
    if ambiguities:
        raise ValueError(f"teaching construction left phase rivals alive: {ambiguities}")
    program = program_for(portal_phase, root=root)
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"portal_phase": portal_phase},
        "selection_scope": "once_per_episode",
        "train": train,
        "test": test,
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "parameter_rivals": rivals,
        "ambiguities": [],
        "scene_profiles": profiles,
    }


def generate_claims(seed: int, *, portal_phase: str, demos: int, queries: int, root: Path = ROOT):
    episode = make_episode(
        seed,
        portal_phase=portal_phase,
        demos=demos,
        queries=queries,
        root=root,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program"],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(_public_challenge_bytes(episode))


def public_id(episode: dict[str, Any]) -> str:
    return _public_challenge_id(episode)


def first_turn_bytes(episode: dict[str, Any]) -> bytes:
    if not isinstance(episode, dict) or not episode.get("train") or not episode.get("test"):
        raise ValueError("episode needs demonstrations and queries")
    first = {"train": episode["train"], "test": [episode["test"][0]]}
    return _public_challenge_bytes(first)


def checkpoint_coordinate(grid) -> tuple[int, int]:
    checks = _positions(grid, 3)
    if len(checks) != 1:
        raise ValueError("expected exactly one checkpoint")
    return checks[0]
