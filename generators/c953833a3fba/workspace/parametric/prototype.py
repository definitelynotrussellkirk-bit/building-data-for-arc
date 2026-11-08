#!/usr/bin/env python3
"""Episode-fixed Manhattan-shell-radius family for c953833a3fba."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "c953833a3fba"
SETTINGS = ({"radius": 2}, {"radius": 3})
DEFAULT_SETTINGS = SETTINGS[0]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 8)


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
if CANONICAL_PROGRAM.count("centers 2 1") != 1:
    raise RuntimeError("canonical shell-radius patch point changed")
RADIUS_THREE_PROGRAM = CANONICAL_PROGRAM.replace("centers 2 1", "centers 3 2")


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


def _settings(value: dict[str, Any] | None, *, seed: int | None = None) -> dict[str, int]:
    if value is None:
        value = dict(DEFAULT_SETTINGS if seed is None else SETTINGS[_rng(seed, "setting").randrange(2)])
    if type(value) is not dict or set(value) != {"radius"}:
        raise ValueError("settings must name exactly radius")
    radius = value["radius"]
    if type(radius) is not int or radius not in (2, 3):
        raise ValueError("radius must be exact integer 2 or 3")
    return {"radius": radius}


def program(settings: dict[str, Any] | None = None) -> str:
    selected = _settings(settings)
    return CANONICAL_PROGRAM if selected["radius"] == 2 else RADIUS_THREE_PROGRAM


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    selected = _settings(settings)
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    centers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not centers:
        raise ValueError("input requires at least one nonzero center")
    radius = selected["radius"]
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if min(abs(r - rr) + abs(c - cc) for rr, cc in centers) == radius:
                out[r][c] = 8
    return out


_DEMO_PROFILES = ((9, 9), (10, 11), (12, 13), (14, 15), (16, 18), (18, 20))
_QUERY_PROFILES = ((12, 14), (18, 20), (24, 26), (30, 30), (15, 22), (21, 29), (27, 30), (29, 28))
_COLORS = (8, 2, 5, 7)


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    h, w = profiles[index]
    grid = [[0] * w for _ in range(h)]
    # Four full-radius anchors.  The fourth query uses all four, spanning 23x23
    # on a 30x30 field.  Smaller lessons use a deterministic 2..4-center prefix.
    anchors = [(3, 3), (3, w - 4), (h - 4, 3), (h - 4, w - 4)]
    n_centers = 4 if split == "query" and index == 3 else 2 + (index % 3)
    rng = _rng(seed, f"{split}-input", index)
    colors = list(_COLORS)
    tail = colors[1:]
    rng.shuffle(tail)
    colors = [8, *tail]
    # Rotate the non-cyan color assignment without moving the stress anchors.
    if index % 2:
        colors[1], colors[2] = colors[2], colors[1]
    for (r, c), color in zip(anchors[:n_centers], colors[:n_centers], strict=True):
        grid[r][c] = color
    if transform(grid, SETTINGS[0]) == transform(grid, SETTINGS[1]):
        raise AssertionError("lesson input failed to expose radius")
    return grid


def _datum(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_rule(source: str, grid: list[list[int]], *, bridge: Any | None = None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge

    own = bridge is None
    bridge = RacketBridge() if own else bridge
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
            {
                "index": index,
                "unanimous": True,
                "output_sha256": digest(pair["output"]),
            }
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
        "schema": f"{TASK_ID}-parametric-radius-v1",
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
    parser.add_argument("--radius", type=int, choices=(2, 3))
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    selected_rows = list(SETTINGS) if args.all_settings else [{"radius": args.radius or 2}]
    seeds = args.seed or [0]
    args.out.mkdir(parents=True)
    public_dir = args.out / "public"
    public_dir.mkdir()
    private_rows = []
    seen: set[str] = set()
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as bridge:
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
