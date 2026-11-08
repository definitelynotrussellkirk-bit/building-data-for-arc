#!/usr/bin/env python3
"""Racket-executed prototype for a fixed-per-episode ``gallery_gap`` rule.

The selected production generator and its canonical rule remain unchanged.
This isolated prototype varies only the number of background rows/columns
between the nine 3x3 pairwise-union panels:

* 0 — panels touch (proposed alternative)
* 1 — canonical/default behavior
* 2 — two-cell separators (proposed alternative)

A setting is derived once from the episode seed and reused for all four
training demonstrations and the query.  Every retained demonstration exposes
the setting through output dimensions, so parameter rivals are distinguished
before the query.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "27b865c5f43a"
PARAMETER_NAME = "gallery_gap"
ALLOWED_GAPS = (0, 1, 2)
DEFAULT_GAP = 1
DEMO_INDICES = (0, 1, 2, 3)
QUERY_INDEX = 4
DIFFICULTY = "medium"


def _validate_gap(value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"gallery_gap must be an integer, not {type(value).__name__}")
    if value not in ALLOWED_GAPS:
        raise ValueError(f"gallery_gap={value} not in {ALLOWED_GAPS}")
    return value


def choose_gap(seed: int) -> int:
    """Choose exactly one bounded rule setting for an entire episode."""
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    return ALLOWED_GAPS[seed % len(ALLOWED_GAPS)]


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_source(*, root: Path | str | None = None) -> str:
    resolved = Path(root) if root is not None else find_root(__file__)
    with canonical_path(resolved).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(f"{TASK_ID}: canonical program_solution not found")


def racket_source(gallery_gap: int, *, root: Path | str | None = None) -> str:
    """Materialize the complete selected rule with only its final gap changed."""
    gap = _validate_gap(gallery_gap)
    canonical = _canonical_source(root=root)
    suffix = " 1))))"
    if not canonical.endswith(suffix):
        raise AssertionError("canonical rule tail no longer has the expected gap argument")
    if gap == DEFAULT_GAP:
        return canonical
    return canonical[: -len(suffix)] + f" {gap}))))"


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty row sequence")
    if any(not isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("every row must be a sequence")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def _components(grid: Any) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            found.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return found


def _binary_crop(component: dict[str, Any]) -> list[list[int]]:
    r0, c0, r1, c1 = component["bbox"]
    crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for row, col in component["cells"]:
        crop[row - r0][col - c0] = 1
    return crop


def gallery_output(grid: Any, gallery_gap: int) -> list[list[int]]:
    """Independent Python mirror used only to cross-check Racket evidence."""
    gap = _validate_gap(gallery_gap)
    objects = sorted(_components(grid), key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    if len(objects) != 3:
        raise ValueError(f"expected three components, got {len(objects)}")
    shapes = [_binary_crop(obj) for obj in objects]
    panel_h = max(len(shape) for shape in shapes)
    panel_w = max(len(shape[0]) for shape in shapes)
    padded: list[list[list[int]]] = []
    for shape in shapes:
        panel = [[0] * panel_w for _ in range(panel_h)]
        for row, values in enumerate(shape):
            for col, value in enumerate(values):
                panel[row][col] = value
        padded.append(panel)

    count = len(padded)
    out = [
        [0] * (count * panel_w + gap * (count - 1))
        for _ in range(count * panel_h + gap * (count - 1))
    ]
    for gallery_row, first in enumerate(padded):
        for gallery_col, second in enumerate(padded):
            top = gallery_row * (panel_h + gap)
            left = gallery_col * (panel_w + gap)
            for row in range(panel_h):
                for col in range(panel_w):
                    if first[row][col] or second[row][col]:
                        out[top + row][left + col] = 8
    return out


def _rule_body(program: str) -> str:
    text = program.strip()
    prefix = "(rule!"
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len(prefix) : -1].strip()


def execute_racket(bridge: Any, source: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute the exact materialized rule body with the bundled bridge."""
    bridge.define_grid("g", grid)
    bridge.define_value("h", len(grid))
    bridge.define_value("w", len(grid[0]))
    result = bridge.eval_text(_rule_body(source))
    if not (
        isinstance(result, list)
        and result
        and all(isinstance(row, list) and row for row in result)
    ):
        raise RuntimeError(f"Racket returned a non-grid: {result!r}")
    return [[int(value) for value in row] for row in result]


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_for_gap(gap: int) -> int:
    return next(seed for seed in range(100) if choose_gap(seed) == gap)


def _episode_inputs(generator: Any, seed: int) -> list[list[list[int]]]:
    return [
        generator.generate(seed * 10_000 + 137, index, difficulty=DIFFICULTY)
        for index in (*DEMO_INDICES, QUERY_INDEX)
    ]


def build_episode(
    generator: Any,
    bridge: Any,
    *,
    episode_seed: int,
    root: Path,
) -> dict[str, Any]:
    gap = choose_gap(episode_seed)
    source = racket_source(gap, root=root)
    inputs = _episode_inputs(generator, episode_seed)
    outputs = [execute_racket(bridge, source, grid) for grid in inputs]
    mirrors = [gallery_output(grid, gap) for grid in inputs]
    if outputs != mirrors:
        raise AssertionError("Python mirror disagrees with executed Racket")
    if gap == DEFAULT_GAP and any(
        output != generator.rule_mirror(grid) for grid, output in zip(inputs, outputs)
    ):
        raise AssertionError("default prototype diverges from selected canonical rule")

    rival_predictions: dict[str, list[list[list[int]]]] = {}
    for rival_gap in ALLOWED_GAPS:
        if rival_gap == gap:
            continue
        rival_source = racket_source(rival_gap, root=root)
        rival_predictions[str(rival_gap)] = [
            execute_racket(bridge, rival_source, grid) for grid in inputs
        ]
    demos_distinguish = {
        rival: any(
            prediction[index] != outputs[index] for index in range(len(DEMO_INDICES))
        )
        for rival, prediction in rival_predictions.items()
    }
    query_differs = {
        rival: prediction[-1] != outputs[-1]
        for rival, prediction in rival_predictions.items()
    }
    if not all(demos_distinguish.values()) or not all(query_differs.values()):
        raise AssertionError("episode does not distinguish every gallery_gap rival")

    pairs = [
        {
            "sample_index": index,
            "input": grid,
            "output": output,
            "input_sha256": _digest(grid),
            "output_sha256": _digest(output),
        }
        for index, grid, output in zip((*DEMO_INDICES, QUERY_INDEX), inputs, outputs)
    ]
    return {
        "schema": "27b865c5f43a-gallery-gap-episode-v1",
        "task_id": TASK_ID,
        "status": "proposed_prototype_not_selected",
        "episode_seed": episode_seed,
        "parameter": {
            "name": PARAMETER_NAME,
            "value": gap,
            "allowed_values": list(ALLOWED_GAPS),
            "default": DEFAULT_GAP,
            "chosen_once_per_episode": True,
        },
        "difficulty": DIFFICULTY,
        "racket": {
            "source": source,
            "sha256": hashlib.sha256(source.encode()).hexdigest(),
            "normalized_hash": normalized_hash(source),
        },
        "demonstrations": pairs[:-1],
        "query": pairs[-1],
        "rival_predictions": rival_predictions,
        "checks": {
            "all_labels_from_executed_racket": True,
            "python_mirror_parity": True,
            "default_matches_selected_rule": gap != DEFAULT_GAP or normalized_hash(source) == generator.RULE_HASH,
            "demos_distinguish_every_rival": demos_distinguish,
            "query_differs_from_every_rival": query_differs,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Strip hidden setting, rule source, rival outputs, and query answer."""
    return {
        "schema": "27b865c5f43a-gallery-gap-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["demonstrations"]
        ],
        "test": [{"input": episode["query"]["input"]}],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument(
        "--examples",
        type=Path,
        default=Path(__file__).resolve().parent / "examples.json",
    )
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    if out_dir.exists():
        parser.error("--out-dir already exists; choose a fresh evidence path")
    out_dir.mkdir(parents=True)

    root = find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    canonical = racket_source(DEFAULT_GAP, root=root)
    if normalized_hash(canonical) != generator.RULE_HASH:
        raise AssertionError("default prototype no longer matches selected RULE_HASH")

    source_dir = Path(__file__).resolve().parent
    racket_dir = source_dir / "racket"
    racket_dir.mkdir(exist_ok=True)
    for gap in ALLOWED_GAPS:
        retained = racket_dir / f"gap_{gap}.rkt"
        source = racket_source(gap, root=root)
        if retained.exists() and retained.read_text(encoding="utf-8") != source:
            raise AssertionError(f"retained {retained.name} differs from materialized source")
        retained.write_text(source, encoding="utf-8")

    from arc_repl.racket_bridge import RacketBridge

    episodes: list[dict[str, Any]] = []
    command = {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]}
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        for gap in ALLOWED_GAPS:
            seed = _seed_for_gap(gap)
            episode = build_episode(generator, bridge, episode_seed=seed, root=root)
            evidence_path = out_dir / f"evidence-gap-{gap}.json"
            challenge_path = out_dir / f"challenge-gap-{gap}.json"
            _write_json(evidence_path, episode)
            _write_json(challenge_path, public_challenge(episode))
            episodes.append(
                {
                    "gap": gap,
                    "episode_seed": seed,
                    "evidence": evidence_path.name,
                    "evidence_sha256": _sha256_file(evidence_path),
                    "public_challenge": challenge_path.name,
                    "public_challenge_sha256": _sha256_file(challenge_path),
                    "racket_source": f"racket/gap_{gap}.rkt",
                    "racket_sha256": episode["racket"]["sha256"],
                    "normalized_hash": episode["racket"]["normalized_hash"],
                    "checks": episode["checks"],
                }
            )

    summary = {
        "schema": "27b865c5f43a-gallery-gap-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "proposed_prototype_not_selected",
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_GAPS),
            "default": DEFAULT_GAP,
            "chosen_once_per_episode": True,
            "input_constraints_depending_on_parameter": [],
            "observable_effect": "output height and width are 9 + 2*gallery_gap",
        },
        "selected_canonical_path_unchanged": True,
        "selected_generator": str(generator_path),
        "selected_generator_sha256": generator_sha256,
        "prototype_sources": {
            "gallery_gap.py": _sha256_file(Path(__file__).resolve()),
            "reference_probe.py": _sha256_file(source_dir.parent / "reference_probe.py"),
        },
        "episodes": episodes,
        "command": command,
        "limitations": [
            "This is an isolated task-local prototype, not an approved production parametric API.",
            "The gap is visually easy to infer because all demonstrations expose output dimensions.",
            "Only three bounded settings and one deterministic episode per setting were executed.",
            "No claim is made that changing gap improves the canonical training distribution.",
        ],
        "passed": all(
            all(item["checks"]["demos_distinguish_every_rival"].values())
            and all(item["checks"]["query_differs_from_every_rival"].values())
            for item in episodes
        ),
    }
    _write_json(out_dir / "summary.json", summary)
    _write_json(args.examples.resolve(), {"summary": summary, "episodes": episodes})
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
