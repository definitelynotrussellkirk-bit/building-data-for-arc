#!/usr/bin/env python3
"""Episode-fixed rotation-handedness family for 8c73e339d80e.

The canonical rule interprets codes 4/9 as one/three clockwise quarter-turns.
The alternate keeps the same code-reading/stamping pipeline but reverses those
quarter turns.  Inputs are sampled independently of the private setting.
"""
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

TASK_ID = "8c73e339d80e"
SETTINGS = (
    {"direction": "clockwise"},
    {"direction": "counterclockwise"},
)
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
_CODE_MAP = "(cond [(= v 2) 0] [(= v 4) 1] [(= v 6) 2] [(= v 9) 3] [else #f])"
_REVERSED_CODE_MAP = "(cond [(= v 2) 0] [(= v 4) 3] [(= v 6) 2] [(= v 9) 1] [else #f])"
if CANONICAL_PROGRAM.count(_CODE_MAP) != 1:
    raise RuntimeError("canonical handedness patch point changed")
COUNTERCLOCKWISE_PROGRAM = CANONICAL_PROGRAM.replace(_CODE_MAP, _REVERSED_CODE_MAP)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(value: dict[str, Any] | None, *, seed: int | None = None) -> dict[str, str]:
    if value is None:
        if seed is None:
            value = dict(DEFAULT_SETTINGS)
        else:
            value = dict(SETTINGS[_rng(seed, "setting").randrange(len(SETTINGS))])
    if type(value) is not dict or set(value) != {"direction"}:
        raise ValueError("settings must name exactly direction")
    direction = value["direction"]
    if direction not in {"clockwise", "counterclockwise"}:
        raise ValueError("direction must be clockwise or counterclockwise")
    return {"direction": direction}


def program(settings: dict[str, Any] | None = None) -> str:
    chosen = _settings(settings)
    return CANONICAL_PROGRAM if chosen["direction"] == "clockwise" else COUNTERCLOCKWISE_PROGRAM


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    payload = f"{TASK_ID}|{seed}|{stream}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _normalize(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return sorted((r - r0, c - c0) for r, c in points)


def _rotate_once(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    max_r = max(r for r, _ in points)
    return _normalize([(c, max_r - r) for r, c in points])


def _rotate(points: list[tuple[int, int]], steps: int) -> list[tuple[int, int]]:
    out = list(points)
    for _ in range(steps % 4):
        out = _rotate_once(out)
    return out


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    chosen = _settings(settings)
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    base = _normalize([(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3])
    if not base:
        raise ValueError("input requires a color-3 base motif")
    code_to_steps = {2: 0, 4: 1, 6: 2, 9: 3}
    if chosen["direction"] == "counterclockwise":
        code_to_steps = {2: 0, 4: 3, 6: 2, 9: 1}
    out = [[0] * w for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1 or c == 0 or grid[r][c - 1] not in code_to_steps:
                continue
            for dr, dc in _rotate(base, code_to_steps[grid[r][c - 1]]):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = 8
    return out


_MOTIFS = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
)
_DEMO_PROFILES = ((9, 11), (10, 13), (12, 14), (14, 16), (16, 18), (18, 20))
_QUERY_PROFILES = ((12, 15), (18, 21), (24, 27), (30, 30), (15, 23), (21, 29), (27, 30), (29, 28))


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    h, w = profiles[index]
    rng = _rng(seed, f"{split}-input", index)
    grid = [[0] * w for _ in range(h)]
    motif = _MOTIFS[(index + rng.randrange(len(_MOTIFS))) % len(_MOTIFS)]
    # Keep the source motif at the opposite corner from the far stress marker.
    top = 1 + (rng.randrange(2) if h >= 12 and index % 2 else 0)
    left = 1 + (rng.randrange(2) if w >= 12 and index % 3 else 0)
    for dr, dc in motif:
        grid[top + dr][left + dc] = 3

    # Every lesson contains both handedness-sensitive codes.  The far marker on
    # the 30x30 profile makes the stress field substantive rather than padded.
    markers = [
        (h - 3, 2, 4),
        (2, w - 3, 9),
        (h - 3, w - 3, 6),
    ]
    if index % 2:
        markers[0], markers[1] = markers[1], markers[0]
    for r, c, code in markers:
        if grid[r][c] or grid[r][c - 1]:
            raise AssertionError("internal marker collision")
        grid[r][c - 1] = code
        grid[r][c] = 1

    # Irrelevant colors force the solver to isolate the source motif, rotation
    # codes, and markers instead of treating every nonzero cell as geometry.
    distractor_candidates = (
        (5, ((h // 2, w // 2), (h // 2 - 1, w // 2), (h // 2, w // 2 + 1))),
        (7, ((h // 2 + 1, w // 2 - 2), (h // 2, w // 2 - 2), (h // 2 + 1, w // 2))),
    )
    for value, candidates in distractor_candidates:
        for rr, cc in candidates:
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0:
                grid[rr][cc] = value
                break
        else:
            raise AssertionError("could not place distractor")

    if transform(grid, SETTINGS[0]) == transform(grid, SETTINGS[1]):
        raise AssertionError("lesson input failed to expose handedness")
    return grid


def _datum(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_rule(source: str, grid: list[list[int]], *, bridge: Any | None = None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge

    own = bridge is None
    bridge = RacketBridge() if own else bridge
    try:
        result = bridge.eval_text(f"({wrap_rule(source)} {_datum(normalize_grid(grid))})")
        return normalize_grid(result)
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
        if execute is None:
            return transform(grid, candidate)
        return execute(program(candidate), grid)

    # First authenticate every retained label under the selected setting so a
    # corrupt label cannot masquerade as a different surviving rule.
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            try:
                observed = predict(selected, pair["input"])
            except (KeyError, TypeError) as exc:
                raise ValueError(f"malformed {split} pair {index}") from exc
            if observed != pair.get("output"):
                raise ValueError(f"label mismatch in {split} pair {index}")

    survivors = []
    for candidate in SETTINGS:
        if all(predict(candidate, pair["input"]) == pair["output"] for pair in train):
            survivors.append(dict(candidate))
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not uniquely identify setting: {survivors}")
    queries = []
    for index, pair in enumerate(test):
        predictions = [predict(candidate, pair["input"]) for candidate in survivors]
        queries.append(
            {
                "index": index,
                "unanimous": bool(predictions) and all(value == predictions[0] for value in predictions),
                "output_sha256": digest(pair["output"]),
            }
        )
    return {"survivors": survivors, "queries": queries, "demo_only": True}


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
        "schema": f"{TASK_ID}-parametric-handedness-v1",
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
    parser.add_argument("--direction", choices=("clockwise", "counterclockwise"))
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    settings_rows = list(SETTINGS) if args.all_settings else [
        {"direction": args.direction or "clockwise"}
    ]
    seeds = args.seed or [0]
    args.out.mkdir(parents=True)
    public_dir = args.out / "public"
    public_dir.mkdir()
    private_rows = []
    seen: set[str] = set()
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as bridge:
        for selected in settings_rows:
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
    private = {
        "schema": f"{TASK_ID}-parametric-evidence-v1",
        "task_id": TASK_ID,
        "episodes": private_rows,
        "runtime": runtime,
    }
    (args.out / "private.json").write_text(json.dumps(private, indent=2, sort_keys=True) + "\n")
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
