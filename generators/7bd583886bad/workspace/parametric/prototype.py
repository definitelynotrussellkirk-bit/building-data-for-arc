#!/usr/bin/env python3
"""Episode-fixed exact-cover label-policy family for 7bd583886bad.

Both settings infer the same unique cover by the canonical square/L pieces.
`shape_type` paints the canonical type 1..4; `area` paints each piece by its
cell count (4 for the square, 3 for every L).  The hidden setting therefore
changes the executed label policy without changing segmentation or search.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable, Iterable

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "7bd583886bad"
SETTINGS = ({"label_mode": "shape_type"}, {"label_mode": "area"})
DEFAULT_SETTINGS = SETTINGS[0]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 8)
PIECES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
)


def _canonical_program() -> str:
    root = find_root(__file__)
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    matches.append(row["program_solution"])
    if not matches or len(set(matches)) != 1:
        raise RuntimeError(f"expected one stable canonical program for {TASK_ID}")
    return matches[0]


CANONICAL_PROGRAM = _canonical_program()
_CANONICAL_LABEL = "(paint-cells acc (snd piece) (fst piece))"
_AREA_LABEL = "(paint-cells acc (snd piece) (length (snd piece)))"
if CANONICAL_PROGRAM.count(_CANONICAL_LABEL) != 1:
    raise RuntimeError("canonical exact-cover label patch point changed")
AREA_PROGRAM = CANONICAL_PROGRAM.replace(_CANONICAL_LABEL, _AREA_LABEL)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    payload = f"{TASK_ID}|{seed}|{stream}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _settings(value: dict[str, Any] | None, *, seed: int | None = None) -> dict[str, str]:
    if value is None:
        value = dict(DEFAULT_SETTINGS if seed is None else SETTINGS[_rng(seed, "setting").randrange(2)])
    if type(value) is not dict or set(value) != {"label_mode"}:
        raise ValueError("settings must name exactly label_mode")
    mode = value["label_mode"]
    if mode not in {"shape_type", "area"}:
        raise ValueError("label_mode must be shape_type or area")
    return {"label_mode": mode}


def program(settings: dict[str, Any] | None = None) -> str:
    selected = _settings(settings)
    return CANONICAL_PROGRAM if selected["label_mode"] == "shape_type" else AREA_PROGRAM


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _neighbors(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _components(mask: frozenset[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for first in sorted(mask):
        if first in seen:
            continue
        stack = [first]
        seen.add(first)
        component: list[tuple[int, int]] = []
        while stack:
            cell = stack.pop()
            component.append(cell)
            for neighbor in _neighbors(cell):
                if neighbor in mask and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _piece_cells(piece: Iterable[tuple[int, int]], top: int, left: int) -> frozenset[tuple[int, int]]:
    return frozenset((top + r, left + c) for r, c in piece)


def _placement_candidates(
    h: int,
    w: int,
    occupied: frozenset[tuple[int, int]],
    *,
    require_touch: bool,
) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    candidates: list[tuple[int, frozenset[tuple[int, int]]]] = []
    for typ, piece in enumerate(PIECES, start=1):
        ph = max(r for r, _ in piece) + 1
        pw = max(c for _, c in piece) + 1
        for top in range(h - ph + 1):
            for left in range(w - pw + 1):
                cells = _piece_cells(piece, top, left)
                if cells & occupied:
                    continue
                if require_touch and not any(
                    neighbor in occupied for cell in cells for neighbor in _neighbors(cell)
                ):
                    continue
                candidates.append((typ, cells))
    return candidates


def _cover_candidates(
    mask: frozenset[tuple[int, int]], h: int, w: int
) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    candidates: list[tuple[int, frozenset[tuple[int, int]]]] = []
    for typ, piece in enumerate(PIECES, start=1):
        ph = max(r for r, _ in piece) + 1
        pw = max(c for _, c in piece) + 1
        for top in range(h - ph + 1):
            for left in range(w - pw + 1):
                cells = _piece_cells(piece, top, left)
                if cells <= mask:
                    candidates.append((typ, cells))
    return candidates


def _cover_solutions(
    mask: frozenset[tuple[int, int]], h: int, w: int, *, limit: int = 2
) -> list[list[tuple[int, frozenset[tuple[int, int]]]]]:
    if not mask:
        return []
    by_cell: dict[tuple[int, int], list[tuple[int, frozenset[tuple[int, int]]]]] = {
        cell: [] for cell in mask
    }
    for candidate in _cover_candidates(mask, h, w):
        for cell in candidate[1]:
            by_cell[cell].append(candidate)
    solutions: list[list[tuple[int, frozenset[tuple[int, int]]]]] = []

    def search(
        uncovered: frozenset[tuple[int, int]],
        partial: list[tuple[int, frozenset[tuple[int, int]]]],
    ) -> None:
        if len(solutions) >= limit:
            return
        if not uncovered:
            solutions.append(list(partial))
            return
        cell = min(
            uncovered,
            key=lambda value: sum(1 for _, cells in by_cell.get(value, ()) if cells <= uncovered),
        )
        options = [(typ, cells) for typ, cells in by_cell.get(cell, ()) if cells <= uncovered]
        for typ, cells in options:
            partial.append((typ, cells))
            search(uncovered - cells, partial)
            partial.pop()
            if len(solutions) >= limit:
                return

    search(mask, [])
    return solutions


def _bbox(mask: frozenset[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in mask]
    cols = [c for _, c in mask]
    return min(rows), min(cols), max(rows), max(cols)


def _build_mask(
    seed: int,
    stream: str,
    index: int,
    h: int,
    w: int,
    piece_count: int,
) -> tuple[frozenset[tuple[int, int]], list[tuple[int, frozenset[tuple[int, int]]]]]:
    for attempt in range(256):
        rng = _rng(seed, f"{stream}-mask-{index}", attempt)
        occupied: frozenset[tuple[int, int]] = frozenset()
        for piece_index in range(piece_count):
            candidates = _placement_candidates(
                h, w, occupied, require_touch=piece_index > 0
            )
            if not candidates:
                break
            if piece_index == 0:
                candidates.sort(
                    key=lambda item: (
                        min(r for r, _ in item[1]) + min(c for _, c in item[1]),
                        item[0],
                    )
                )
                pool = candidates[: min(8, len(candidates))]
            else:
                scored: list[tuple[float, tuple[int, frozenset[tuple[int, int]]]]] = []
                for candidate in candidates:
                    _, cells = candidate
                    combined = occupied | cells
                    r0, c0, r1, c1 = _bbox(combined)
                    bh, bw = r1 - r0 + 1, c1 - c0 + 1
                    contacts = sum(
                        neighbor in occupied
                        for cell in cells
                        for neighbor in _neighbors(cell)
                    )
                    score = (
                        min(bh, bw) * 1000
                        + (bh + bw) * 100
                        + bh * bw * 2
                        - contacts * 8
                        + rng.random()
                    )
                    scored.append((score, candidate))
                scored.sort(key=lambda row: row[0], reverse=True)
                pool = [candidate for _, candidate in scored[: min(10, len(scored))]]
            _typ, cells = rng.choice(pool)
            occupied = occupied | cells
        else:
            if len(_components(occupied)) != 1:
                continue
            solutions = _cover_solutions(occupied, h, w, limit=2)
            if len(solutions) != 1:
                continue
            # All-type-3 covers are the one degenerate case where shape labels
            # happen to equal area labels cell-for-cell.
            if all(typ == 3 for typ, _ in solutions[0]):
                continue
            r0, c0, r1, c1 = _bbox(occupied)
            if h == 30 and w == 30 and (r1 - r0 + 1 < 25 or c1 - c0 + 1 < 25):
                continue
            return occupied, solutions[0]
    raise ValueError(
        f"could not construct connected unique cover for {h}x{w} with {piece_count} pieces"
    )


_DEMO_PROFILES = ((7, 7, 3), (8, 8, 4), (9, 9, 5), (10, 10, 6), (11, 12, 7), (12, 12, 8))
_QUERY_PROFILES = (
    (9, 11, 6),
    (14, 16, 10),
    (22, 24, 18),
    (30, 30, 30),
    (13, 18, 11),
    (18, 23, 15),
    (25, 29, 22),
    (29, 30, 27),
)


@lru_cache(maxsize=512)
def _build_input_tuple(seed: int, split: str, index: int) -> tuple[tuple[int, ...], ...]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    h, w, piece_count = profiles[index]
    mask, _solution = _build_mask(seed, split, index, h, w, piece_count)
    return tuple(tuple(8 if (r, c) in mask else 0 for c in range(w)) for r in range(h))


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    return [list(row) for row in _build_input_tuple(seed, split, index)]


def _mask_from_grid(grid: list[list[int]]) -> frozenset[tuple[int, int]]:
    grid = normalize_grid(grid)
    bad = {value for row in grid for value in row if value not in (0, 8)}
    if bad:
        raise ValueError(f"input contains colors outside 0/8: {sorted(bad)}")
    mask = frozenset((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8)
    if not mask:
        raise ValueError("input requires a nonempty color-8 mask")
    return mask


def analyze_mask(grid: list[list[int]]) -> dict[str, Any]:
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    mask = _mask_from_grid(grid)
    solutions = _cover_solutions(mask, h, w, limit=2)
    r0, c0, r1, c1 = _bbox(mask)
    return {
        "connected": len(_components(mask)) == 1,
        "cover_count": len(solutions),
        "bbox_height": r1 - r0 + 1,
        "bbox_width": c1 - c0 + 1,
        "cell_count": len(mask),
    }


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    selected = _settings(settings)
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    mask = _mask_from_grid(grid)
    solutions = _cover_solutions(mask, h, w, limit=2)
    if len(solutions) != 1:
        raise ValueError(f"input must have exactly one legal cover, found {len(solutions)}")
    out = [[0] * w for _ in range(h)]
    for typ, cells in solutions[0]:
        label = typ if selected["label_mode"] == "shape_type" else len(cells)
        for r, c in cells:
            out[r][c] = label
    return out


def _datum(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_rule(source: str, grid: list[list[int]], *, bridge: Any | None = None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge

    own = bridge is None
    bridge = RacketBridge(timeout=60) if own else bridge
    try:
        return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {_datum(normalize_grid(grid))})"))
    finally:
        if own:
            bridge.close()


def certify(
    episode: dict[str, Any],
    *,
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    selected = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(selected):
        raise ValueError("private program does not match selected setting")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode requires nonempty train and test lists")

    def predict(candidate: dict[str, Any], grid: list[list[int]]) -> list[list[int]]:
        return transform(grid, candidate) if execute is None else execute(program(candidate), grid)

    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            try:
                observed = predict(selected, pair["input"])
            except (KeyError, TypeError) as exc:
                raise ValueError(f"malformed {split} pair {index}") from exc
            if observed != pair.get("output"):
                raise ValueError(f"label mismatch in {split} pair {index}")
    survivors = [
        dict(candidate)
        for candidate in SETTINGS
        if all(predict(candidate, pair["input"]) == pair["output"] for pair in train)
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not uniquely identify setting: {survivors}")
    return {
        "survivors": survivors,
        "demo_only": True,
        "queries": [
            {"index": index, "unanimous": True, "output_sha256": digest(pair["output"])}
            for index, pair in enumerate(test)
        ],
    }


def generate(
    seed: int,
    settings: dict[str, Any] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    queries = _integer(queries, "queries", *QUERY_LIMITS)
    selected = _settings(settings, seed=seed)
    train_inputs = [_build_input(seed, "demo", index) for index in range(demos)]
    test_inputs = [_build_input(seed, "query", index) for index in range(queries)]
    keys = [digest(grid) for grid in train_inputs + test_inputs]
    if len(set(keys)) != len(keys):
        raise ValueError("episode inputs must be distinct")
    episode = {
        "schema": f"{TASK_ID}-parametric-label-policy-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": [{"input": grid, "output": transform(grid, selected)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, selected)} for grid in test_inputs],
        "program_solution": program(selected),
        "racket_checked": False,
    }
    episode["certificate"] = certify(episode)
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(public_challenge_bytes(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(episode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="append", type=int, default=[])
    parser.add_argument("--label-mode", choices=("shape_type", "area"))
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    selected_rows = list(SETTINGS) if args.all_settings else [
        {"label_mode": args.label_mode or "shape_type"}
    ]
    seeds = args.seed or [0]
    args.out.mkdir(parents=True)
    public_dir = args.out / "public"
    public_dir.mkdir()
    private_rows = []
    seen: set[str] = set()
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=60) as bridge:
        for selected in selected_rows:
            for seed in seeds:
                episode = generate(seed, selected, args.demos, args.queries)
                cert = certify(
                    episode,
                    execute=lambda source, grid: execute_rule(source, grid, bridge=bridge),
                )
                challenge_id = public_id(episode)
                if challenge_id in seen:
                    raise ValueError(f"duplicate visible challenge {challenge_id}")
                seen.add(challenge_id)
                (public_dir / f"{challenge_id}.json").write_bytes(public_challenge_bytes(episode))
                private_rows.append(
                    {
                        "public_id": challenge_id,
                        "seed": seed,
                        "settings": selected,
                        "program_solution": episode["program_solution"],
                        "program_sha256": digest(episode["program_solution"]),
                        "query_outputs": [pair["output"] for pair in episode["test"]],
                        "certificate": cert,
                    }
                )
        runtime = bridge.runtime_identity
    (args.out / "private.json").write_text(
        json.dumps(
            {
                "schema": f"{TASK_ID}-parametric-evidence-v1",
                "task_id": TASK_ID,
                "episodes": private_rows,
                "runtime": runtime,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    manifest = {
        "schema": "arcpuzzles-parametric-prototype-export-v1",
        "task_id": TASK_ID,
        "episode_count": len(private_rows),
        "public_ids": sorted(seen),
        "files": {
            str(path.relative_to(args.out)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(args.out.rglob("*"))
            if path.is_file()
        },
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "episodes": len(private_rows), "public_ids": sorted(seen)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
