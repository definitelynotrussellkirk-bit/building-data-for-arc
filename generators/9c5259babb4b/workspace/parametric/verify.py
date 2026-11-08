"""Bounded teaching and public-projection audit for the precedence family."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"
_NAME = "_symmetry_precedence_verify_target_" + hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, PROTOTYPE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling precedence prototype")
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = PROTOTYPE
_SPEC.loader.exec_module(PROTOTYPE)


Grid = list[list[int]]
Rival = Callable[[Grid, str], Grid]


def _background(grid: Grid) -> int:
    counts = Counter(value for row in grid for value in row)
    return max(counts, key=lambda value: (counts[value], -value))


def _objects(grid: Grid, *, connectivity: int) -> list[list[tuple[int, int]]]:
    background = _background(grid)
    if connectivity == 4:
        deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    elif connectivity == 8:
        deltas = tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if dr or dc
        )
    else:
        raise ValueError(connectivity)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] == background:
                continue
            color = grid[row][col]
            queue = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for dr, dc in deltas:
                    other = current_row + dr, current_col + dc
                    if other in seen:
                        continue
                    if 0 <= other[0] < height and 0 <= other[1] < width and grid[other[0]][other[1]] == color:
                        seen.add(other)
                        queue.append(other)
            result.append(cells)
    return result


def _flags(cells: list[tuple[int, int]]) -> tuple[bool, bool]:
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    norm = {(row - row0, col - col0) for row, col in cells}
    height = max(row for row, _ in norm) + 1
    width = max(col for _, col in norm) + 1
    top_bottom = {(height - 1 - row, col) for row, col in norm} == norm
    left_right = {(row, width - 1 - col) for row, col in norm} == norm
    return top_bottom, left_right


def _selected_color(top_bottom: bool, left_right: bool, setting: str) -> int:
    if setting == "top_bottom_first":
        return 1 if top_bottom else 3 if left_right else 6
    if setting == "left_right_first":
        return 3 if left_right else 1 if top_bottom else 6
    raise ValueError(setting)


def _recolor(grid: Grid, setting: str, *, connectivity: int = 8,
             chooser: Callable[[list[tuple[int, int]], bool, bool, str], int | None] | None = None,
             keep_singletons: bool = False) -> Grid:
    background = _background(grid)
    output = [[background] * len(grid[0]) for _ in grid]
    for cells in _objects(grid, connectivity=connectivity):
        if len(cells) == 1:
            if keep_singletons:
                row, col = cells[0]
                output[row][col] = grid[row][col]
            continue
        top_bottom, left_right = _flags(cells)
        color = _selected_color(top_bottom, left_right, setting) if chooser is None else chooser(
            cells, top_bottom, left_right, setting
        )
        if color is None:
            continue
        for row, col in cells:
            output[row][col] = color
    return output


def _other_declared(grid: Grid, setting: str) -> Grid:
    other = "left_right_first" if setting == "top_bottom_first" else "top_bottom_first"
    return PROTOTYPE.output_for(grid, other)


def _four_connected(grid: Grid, setting: str) -> Grid:
    return _recolor(grid, setting, connectivity=4)


def _keep_singletons(grid: Grid, setting: str) -> Grid:
    return _recolor(grid, setting, keep_singletons=True)


def _ignore_asymmetric(grid: Grid, setting: str) -> Grid:
    return _recolor(
        grid,
        setting,
        chooser=lambda _cells, top, left, selected: _selected_color(top, left, selected) if top or left else None,
    )


def _both_as_asymmetric(grid: Grid, setting: str) -> Grid:
    return _recolor(
        grid,
        setting,
        chooser=lambda _cells, top, left, selected: 6 if top and left else _selected_color(top, left, selected),
    )


def _top_bottom_only(grid: Grid, setting: str) -> Grid:
    del setting
    return _recolor(
        grid,
        "top_bottom_first",
        chooser=lambda _cells, top, _left, _selected: 1 if top else 6,
    )


def _left_right_only(grid: Grid, setting: str) -> Grid:
    del setting
    return _recolor(
        grid,
        "left_right_first",
        chooser=lambda _cells, _top, left, _selected: 3 if left else 6,
    )


def _size_parity(grid: Grid, setting: str) -> Grid:
    del setting
    return _recolor(
        grid,
        "top_bottom_first",
        chooser=lambda cells, _top, _left, _selected: 1 if len(cells) % 2 == 0 else 3,
    )


RIVALS: dict[str, Rival] = {
    "other_declared_setting": _other_declared,
    "four_connected_objects": _four_connected,
    "keep_singletons": _keep_singletons,
    "ignore_asymmetric": _ignore_asymmetric,
    "both_as_asymmetric": _both_as_asymmetric,
    "top_bottom_only": _top_bottom_only,
    "left_right_only": _left_right_only,
    "size_parity": _size_parity,
}


def audit_episode(seed: int, setting: str, demos: int = 2) -> dict[str, Any]:
    episode = PROTOTYPE.build_episode(seed, setting, demos=demos, queries=4)
    defeated: list[str] = []
    ambiguous: list[str] = []
    equivalent_on_episode: list[str] = []
    details: dict[str, Any] = {}
    for name, rival in RIVALS.items():
        demo_outputs = [rival(pair["input"], setting) for pair in episode["train"]]
        demo_match = all(output == pair["output"] for output, pair in zip(demo_outputs, episode["train"]))
        query_outputs = [rival(pair["input"], setting) for pair in episode["test"]]
        query_disagreements = [
            index
            for index, (output, pair) in enumerate(zip(query_outputs, episode["test"]))
            if output != pair["output"]
        ]
        if not demo_match:
            defeated.append(name)
        elif query_disagreements:
            ambiguous.append(name)
        else:
            equivalent_on_episode.append(name)
        details[name] = {
            "fits_demonstrations": demo_match,
            "query_disagreements": query_disagreements,
        }
    return {
        "seed": seed,
        "selected_setting": setting,
        "demonstration_count": demos,
        "tested_rivals": list(RIVALS),
        "defeated_rivals": defeated,
        "ambiguous_rivals": ambiguous,
        "equivalent_on_episode": equivalent_on_episode,
        "details": details,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n")


def build_evidence(output: Path, seeds: list[int], demos: int) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.mkdir(parents=True)

    audit_rows = [
        audit_episode(seed, setting, count)
        for seed in range(12)
        for count in (2, 3, 6)
        for setting in PROTOTYPE.PRECEDENCES
    ]
    ambiguous = [
        {"seed": row["seed"], "setting": row["selected_setting"], "demos": row["demonstration_count"], "rivals": row["ambiguous_rivals"]}
        for row in audit_rows
        if row["ambiguous_rivals"]
    ]
    if ambiguous:
        raise AssertionError(f"finite teaching ambiguity remains: {ambiguous[:4]}")

    public_dir = output / "public"
    private_episodes: list[dict[str, Any]] = []
    projection_rows: list[dict[str, Any]] = []
    public_payloads: dict[str, bytes] = {}
    for seed in seeds:
        for setting in PROTOTYPE.PRECEDENCES:
            episode = PROTOTYPE.build_episode(seed, setting, demos=demos, queries=4)
            private_episodes.append(episode)
            for query_index in range(4):
                public = PROTOTYPE.public_projection(episode, query_index)
                payload = public_challenge_bytes(public)
                identifier = public_challenge_id(public)
                if hashlib.sha256(payload).hexdigest() != identifier:
                    raise AssertionError("public identifier does not hash exact visible bytes")
                previous = public_payloads.setdefault(identifier, payload)
                if previous != payload:
                    raise AssertionError("public identifier collision")
                path = public_dir / f"{identifier}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.exists() and path.read_bytes() != payload:
                    raise AssertionError("duplicate public path has different bytes")
                path.write_bytes(payload)

                changed = copy.deepcopy(episode)
                changed["settings"] = {"precedence": "private-mutated"}
                changed["program_solution"] = "private-mutated"
                changed["test"][query_index]["output"][0][0] = (
                    changed["test"][query_index]["output"][0][0] + 1
                ) % 10
                if public_challenge_bytes(PROTOTYPE.public_projection(changed, query_index)) != payload:
                    raise AssertionError("private metadata or query answer changed visible bytes")
                projection_rows.append({
                    "seed": seed,
                    "setting": setting,
                    "query_index": query_index,
                    "public_id": identifier,
                    "path": f"public/{identifier}.json",
                    "bytes": len(payload),
                    "input_sha256": hashlib.sha256(
                        json.dumps(episode["test"][query_index]["input"], separators=(",", ":")).encode()
                    ).hexdigest(),
                })

    summaries = [
        {
            "seed": episode["seed"],
            "settings": episode["settings"],
            "demos": [PROTOTYPE.scene_summary(pair["input"]) for pair in episode["train"]],
            "queries": [PROTOTYPE.scene_summary(pair["input"]) for pair in episode["test"]],
            "episode_sha256": PROTOTYPE.episode_digest(episode),
            "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
        }
        for episode in private_episodes
    ]
    summary = {
        "schema": "9c5259babb4b-symmetry-precedence-audit-v1",
        "status": "passed",
        "settings": list(PROTOTYPE.PRECEDENCES),
        "audit_episode_count": len(audit_rows),
        "audit_seeds": list(range(12)),
        "audit_demo_counts": [2, 3, 6],
        "tested_rivals": list(RIVALS),
        "ambiguous_cases": ambiguous,
        "public_projection_count": len(projection_rows),
        "public_file_count": len(public_payloads),
        "projection_seeds": seeds,
        "projection_demos": demos,
        "limits": "Finite Python teaching/public-projection audit. Label authority comes from subsequent protected-Racket native qualification.",
    }
    _write_json(output / "teaching-audit.json", {"schema": "9c5259babb4b-finite-rivals-v1", "rows": audit_rows})
    _write_json(output / "projection-index.json", {"schema": "9c5259babb4b-public-projection-v1", "rows": projection_rows})
    _write_json(output / "private" / "episodes.json", {"schema": "9c5259babb4b-private-episodes-v1", "episodes": private_episodes})
    _write_json(output / "scene-summaries.json", {"schema": "9c5259babb4b-scene-summaries-v1", "rows": summaries})
    _write_json(output / "summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args(argv)
    seeds = [0, 17] if args.seeds is None else args.seeds
    if not 1 <= len(seeds) <= 8 or len(set(seeds)) != len(seeds):
        raise ValueError("provide 1..8 distinct projection seeds")
    for seed in seeds:
        PROTOTYPE._literal_int("seed", seed, 0, 2**63 - 1)
    PROTOTYPE._literal_int("demos", args.demos, 2, 6)
    summary = build_evidence(args.out, seeds, args.demos)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
