"""Exact-pass midpoint cascade prototype for ``fe54bfae4cee``.

The canonical setting applies the original midpoint rule once.  The alternate
setting applies that exact rule twice.  Inputs contain depth-three zig-zag
chains, so demonstrations distinguish one pass, two passes, and an unbounded
closure shortcut while preserving the original equal-endpoint reasoning.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from typing import Callable

TASK_ID = "fe54bfae4cee"

CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (let ((after-h (for*/fold ((out g)) ((r (in-range (rows g))) (c (in-range (- (cols g) 2)))) (if (and (not (= (at g r c) 0)) (= (at g r c) (at g r (+ c 2))) (= (at g r (+ c 1)) 0)) (set-cell out r (+ c 1) (at g r c)) out)))) (for*/fold ((out after-h)) ((r (in-range (- (rows g) 2))) (c (in-range (cols g)))) (if (and (not (= (at g r c) 0)) (= (at g r c) (at g (+ r 2) c)) (= (at g (+ r 1) c) 0)) (set-cell out (+ r 1) c (at g r c)) out)))))"


def _pass_expression(source: str) -> str:
    """Return the canonical pass body with ``source`` as its read-only input."""
    if not source.isidentifier():
        raise ValueError("source must be a simple identifier")
    return (
        f"(let ((dummy 0)) (let ((after-h (for*/fold ((out {source})) "
        f"((r (in-range (rows {source}))) (c (in-range (- (cols {source}) 2)))) "
        f"(if (and (not (= (at {source} r c) 0)) "
        f"(= (at {source} r c) (at {source} r (+ c 2))) "
        f"(= (at {source} r (+ c 1)) 0)) "
        f"(set-cell out r (+ c 1) (at {source} r c)) out)))) "
        f"(for*/fold ((out after-h)) "
        f"((r (in-range (- (rows {source}) 2))) (c (in-range (cols {source})))) "
        f"(if (and (not (= (at {source} r c) 0)) "
        f"(= (at {source} r c) (at {source} (+ r 2) c)) "
        f"(= (at {source} (+ r 1) c) 0)) "
        f"(set-cell out (+ r 1) c (at {source} r c)) out))))"
    )


TWO_PASS_PROGRAM = (
    f"(rule! (let ((first {_pass_expression('g')})) {_pass_expression('first')}))"
)

DEMO_PROFILES: tuple[tuple[int, int], ...] = (
    (9, 9),
    (10, 13),
    (13, 10),
    (15, 17),
    (18, 20),
    (21, 24),
)
QUERY_PROFILES: tuple[tuple[int, int], ...] = (
    (14, 19),
    (19, 14),
    (24, 27),
    (30, 30),
)
PROFILES = DEMO_PROFILES + QUERY_PROFILES


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_grid(grid: list[list[int]]) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be a rectangular 1..30 exact-integer ARC grid")
    return grid


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def one_pass(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror of the exact canonical horizontal-then-vertical pass."""
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    out = _copy_grid(grid)
    for r in range(h):
        for c in range(w - 2):
            color = grid[r][c]
            if color != 0 and color == grid[r][c + 2] and grid[r][c + 1] == 0:
                out[r][c + 1] = color
    for r in range(h - 2):
        for c in range(w):
            color = grid[r][c]
            if color != 0 and color == grid[r + 2][c] and grid[r + 1][c] == 0:
                out[r + 1][c] = color
    return out


def apply_passes(grid: list[list[int]], passes: int) -> list[list[int]]:
    if type(passes) is not int or not 1 <= passes <= 32:
        raise ValueError("passes must be an exact integer in 1..32")
    out = _copy_grid(_validate_grid(grid))
    for _ in range(passes):
        out = one_pass(out)
    return out


def apply_until_stable(grid: list[list[int]], *, max_passes: int = 32) -> list[list[int]]:
    if type(max_passes) is not int or not 1 <= max_passes <= 32:
        raise ValueError("max_passes must be an exact integer in 1..32")
    out = _copy_grid(_validate_grid(grid))
    for _ in range(max_passes):
        nxt = one_pass(out)
        if nxt == out:
            return nxt
        out = nxt
    raise RuntimeError("midpoint closure did not stabilize within max_passes")


def _horizontal_only(grid: list[list[int]]) -> list[list[int]]:
    _validate_grid(grid)
    out = _copy_grid(grid)
    for r in range(len(grid)):
        for c in range(len(grid[0]) - 2):
            color = grid[r][c]
            if color != 0 and color == grid[r][c + 2] and grid[r][c + 1] == 0:
                out[r][c + 1] = color
    return out


def _vertical_only(grid: list[list[int]]) -> list[list[int]]:
    _validate_grid(grid)
    out = _copy_grid(grid)
    for r in range(len(grid) - 2):
        for c in range(len(grid[0])):
            color = grid[r][c]
            if color != 0 and color == grid[r + 2][c] and grid[r + 1][c] == 0:
                out[r + 1][c] = color
    return out


def program_for(passes: int) -> str:
    if type(passes) is not int or passes not in (1, 2):
        raise ValueError("passes must be exact integer 1 or 2")
    return CANONICAL_PROGRAM if passes == 1 else TWO_PASS_PROGRAM


def _derived_rng(seed: int, slot: int) -> random.Random:
    raw = f"{TASK_ID}:{seed}:{slot}:exact-pass-v1".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _cascade(kind: str, r: int, c: int):
    if kind == "hvh":
        initial = {(r, c), (r, c + 2), (r + 2, c + 1), (r + 1, c + 3)}
        stages = ((r, c + 1), (r + 1, c + 1), (r + 1, c + 2))
    elif kind == "vhv":
        initial = {(r, c), (r + 2, c), (r + 1, c + 2), (r + 3, c + 1)}
        stages = ((r + 1, c), (r + 1, c + 1), (r + 2, c + 1))
    else:
        raise ValueError(f"unknown cascade kind: {kind}")
    return initial, stages, initial | set(stages)


def _candidate_origins(kind: str, h: int, w: int):
    fh, fw = (3, 4) if kind == "hvh" else (4, 3)
    for r in range(1, h - fh):
        for c in range(1, w - fw):
            yield r, c


def _place_cascades(
    grid: list[list[int]],
    colors: list[int],
    count: int,
    rng: random.Random,
):
    h, w = len(grid), len(grid[0])
    anchors = [
        (0.02, 0.02),
        (0.98, 0.98),
        (0.02, 0.98),
        (0.98, 0.02),
        (0.50, 0.50),
    ]
    if rng.randrange(2):
        kinds = ["vhv" if i % 2 == 0 else "hvh" for i in range(count)]
    else:
        kinds = ["hvh" if i % 2 == 0 else "vhv" for i in range(count)]
    # The first two always cover both causal orientations.
    if count >= 2 and kinds[0] == kinds[1]:
        kinds[1] = "vhv" if kinds[0] == "hvh" else "hvh"

    reserved: set[tuple[int, int]] = set()
    stage_sets = [set(), set(), set()]
    for index, kind in enumerate(kinds):
        fh, fw = (3, 4) if kind == "hvh" else (4, 3)
        ar, ac = anchors[index]
        target_r = round(1 + ar * max(0, h - fh - 2))
        target_c = round(1 + ac * max(0, w - fw - 2))
        candidates = list(_candidate_origins(kind, h, w))
        rng.shuffle(candidates)
        candidates.sort(key=lambda rc: abs(rc[0] - target_r) + abs(rc[1] - target_c))
        selected = None
        for r, c in candidates:
            initial, stages, footprint = _cascade(kind, r, c)
            if footprint.isdisjoint(reserved):
                selected = (initial, stages, footprint)
                break
        if selected is None:
            raise RuntimeError(f"could not place {count} cascades in {h}x{w}")
        initial, stages, footprint = selected
        color = colors[index]
        for r, c in initial:
            grid[r][c] = color
        reserved.update(footprint)
        for stage_index, cell in enumerate(stages):
            stage_sets[stage_index].add(cell)
    return reserved, tuple(stage_sets)


def _free(cells, forbidden):
    return all(cell not in forbidden for cell in cells)


def _place_decoys(
    grid: list[list[int]],
    colors: list[int],
    forbidden: set[tuple[int, int]],
    rng: random.Random,
) -> None:
    h, w = len(grid), len(grid[0])
    color_index = 0

    longspan = []
    for r in range(h):
        for c in range(w - 4):
            longspan.append(((r, c), (r, c + 4)))
    for r in range(h - 4):
        for c in range(w):
            longspan.append(((r, c), (r + 4, c)))
    rng.shuffle(longspan)
    for cells in longspan:
        if _free(cells, forbidden):
            color = colors[color_index]
            color_index += 1
            for r, c in cells:
                grid[r][c] = color
            forbidden.update(cells)
            break
    else:
        raise RuntimeError("could not place long-span decoy")

    diagonals = [
        ((r, c), (r + 2, c + 2))
        for r in range(h - 2)
        for c in range(w - 2)
    ]
    rng.shuffle(diagonals)
    for cells in diagonals:
        if _free(cells, forbidden):
            color = colors[color_index]
            color_index += 1
            for r, c in cells:
                grid[r][c] = color
            forbidden.update(cells)
            break
    else:
        raise RuntimeError("could not place diagonal decoy")

    if color_index + 1 >= len(colors):
        return
    blocked = []
    for r in range(h):
        for c in range(w - 2):
            blocked.append(((r, c), (r, c + 1), (r, c + 2)))
    for r in range(h - 2):
        for c in range(w):
            blocked.append(((r, c), (r + 1, c), (r + 2, c)))
    rng.shuffle(blocked)
    for a, midpoint, b in blocked:
        if _free((a, midpoint, b), forbidden):
            endpoint_color = colors[color_index]
            blocker_color = colors[color_index + 1]
            grid[a[0]][a[1]] = endpoint_color
            grid[b[0]][b[1]] = endpoint_color
            grid[midpoint[0]][midpoint[1]] = blocker_color
            forbidden.update((a, midpoint, b))
            return
    raise RuntimeError("could not place blocked-midpoint decoy")


def _changed(left: list[list[int]], right: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(left)
        for c, value in enumerate(row)
        if right[r][c] != value
    }


def build_input(seed: int, slot: int) -> list[list[int]]:
    """Build one deterministic input independent of the hidden pass setting."""
    _validate_seed(seed)
    if type(slot) is not int or not 0 <= slot < len(PROFILES):
        raise ValueError(f"slot must be an exact integer in 0..{len(PROFILES) - 1}")
    h, w = PROFILES[slot]
    rng = _derived_rng(seed, slot)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    minimum = min(h, w)
    cascade_count = 5 if minimum >= 25 else 4 if minimum >= 20 else 3 if minimum >= 14 else 2
    grid = [[0 for _ in range(w)] for _ in range(h)]
    reserved, expected = _place_cascades(grid, palette[:cascade_count], cascade_count, rng)
    _place_decoys(grid, palette[cascade_count:], set(reserved), rng)

    stage1 = one_pass(grid)
    stage2 = one_pass(stage1)
    stage3 = one_pass(stage2)
    stage4 = one_pass(stage3)
    observed = (_changed(grid, stage1), _changed(stage1, stage2), _changed(stage2, stage3))
    if observed != expected or stage4 != stage3:
        raise RuntimeError(
            "generated scene violated exact depth contract: "
            + json.dumps(
                {
                    "shape": [h, w],
                    "expected": [sorted(x) for x in expected],
                    "observed": [sorted(x) for x in observed],
                    "stable_after_three": stage4 == stage3,
                },
                sort_keys=True,
            )
        )
    return grid


def _validate_episode_request(seed: int, passes: int, demos: int, queries: int) -> None:
    _validate_seed(seed)
    if type(passes) is not int or passes not in (1, 2):
        raise ValueError("passes must be exact integer 1 or 2")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def generate_episode(seed: int, *, passes: int, demos: int = 3, queries: int = 4) -> dict:
    _validate_episode_request(seed, passes, demos, queries)

    def pair(slot: int) -> dict:
        grid = build_input(seed, slot)
        return {"input": grid, "output": apply_passes(grid, passes)}

    train = [pair(slot) for slot in range(demos)]
    test = [pair(slot) for slot in range(len(DEMO_PROFILES), len(PROFILES))]
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"passes": passes},
        "counts": {"demos": demos, "queries": queries},
        "train": train,
        "test": test,
        "program_solution": program_for(passes),
    }


def public_challenge(episode: dict) -> dict:
    """Return only visible demonstrations and masked query inputs."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in test],
    }


def audit_episode(episode: dict) -> dict:
    """Bounded visible-demo audit against plausible midpoint shortcuts."""
    passes = episode.get("settings", {}).get("passes")
    if passes not in (1, 2):
        raise ValueError("episode lacks a supported passes setting")
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        "identity": _copy_grid,
        "passes_1": lambda grid: apply_passes(grid, 1),
        "passes_2": lambda grid: apply_passes(grid, 2),
        "closure": apply_until_stable,
        "horizontal_only": _horizontal_only,
        "vertical_only": _vertical_only,
    }
    rows = []
    for name, transform in rivals.items():
        demo_mismatches = [
            index
            for index, pair in enumerate(episode["train"])
            if transform(pair["input"]) != pair["output"]
        ]
        query_mismatches = [
            index
            for index, pair in enumerate(episode["test"])
            if transform(pair["input"]) != pair["output"]
        ]
        rows.append(
            {
                "name": name,
                "demo_mismatches": demo_mismatches,
                "query_mismatches": query_mismatches,
            }
        )
    survivors = [row["name"] for row in rows if not row["demo_mismatches"]]
    chosen = f"passes_{passes}"
    ambiguous = [
        row["name"]
        for row in rows
        if row["name"] != chosen
        and not row["demo_mismatches"]
        and row["query_mismatches"]
    ]
    return {
        "schema": "fe54bfae4cee-finite-shortcut-audit-v1",
        "chosen": chosen,
        "survivors": survivors,
        "ambiguous_query_changers": ambiguous,
        "rivals": rows,
        "limits": "Finite Python-mirror rivals on one deterministic episode; protected Racket qualification remains authoritative for declared setting programs.",
    }
