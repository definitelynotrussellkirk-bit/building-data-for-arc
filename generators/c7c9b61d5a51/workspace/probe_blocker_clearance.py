#!/usr/bin/env python3
"""Probe whether lessons distinguish full-path clearance from elbow-only checks.

Run from the repository root with ``shared/runtime`` on ``PYTHONPATH``.  The
script loads the selected generator by path, measures canonical and generated
blocker placement, and constructs a lawful off-elbow counterexample when one
exists in the generator's declared strict grammar.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("clearance_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _elbow_only(gen, grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: inspect candidate elbows, not the complete paths."""
    analysis = gen._analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    out = [row[:] for row in grid]
    for pair in analysis["pairs"]:
        a, b = pair["cells"]
        elbows = ((a[0], b[1]), (b[0], a[1]))
        selected = next(
            (
                index
                for index, (row, col) in enumerate(elbows)
                if grid[row][col] in (0, pair["color"])
            ),
            None,
        )
        if selected is not None:
            for row, col in pair["routes"][selected]:
                out[row][col] = pair["color"]
    return out


def _pair_blocker_kind(gen, grid: list[list[int]], pair: dict[str, Any]) -> str:
    selected = pair["selected"]
    if selected is None:
        return "unresolved"
    blocked = 1 - selected
    a, b = pair["cells"]
    elbow = (a[0], b[1]) if blocked == 0 else (b[0], a[1])
    hits = [cell for cell in pair["routes"][blocked] if grid[cell[0]][cell[1]] == 5]
    if elbow in hits:
        return "elbow"
    if hits:
        return "leg"
    return "none"


def _scene_kinds(gen, grid: list[list[int]]) -> list[str]:
    return [_pair_blocker_kind(gen, grid, pair) for pair in gen._analyze(grid)["pairs"]]


def _canonical_row(repo: Path, task_id: str) -> dict[str, Any]:
    path = repo / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def _pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for split in ("train", "test"):
        value = row[split]
        result.extend([value] if isinstance(value, dict) else value)
    return result


def _counterexample(gen):
    """Move one elbow blocker along the same blocked route, preserving strictness."""
    for seed in range(100):
        for sample_index in range(24):
            source = gen.generate(seed, sample_index, difficulty="medium")
            analysis = gen._analyze(source)
            selected_paths = [
                set(pair["routes"][pair["selected"]])
                for pair in analysis["pairs"]
                if pair["selected"] is not None
            ]
            for pair_index, pair in enumerate(analysis["pairs"]):
                if pair["selected"] != 1:
                    continue
                a, b = pair["cells"]
                elbow = (a[0], b[1])  # route 0 is blocked when route 1 is selected
                if source[elbow[0]][elbow[1]] != gen.BLOCKER_COLOR:
                    continue
                blocked_route = pair["routes"][0]
                candidates = [
                    cell
                    for cell in blocked_route
                    if cell not in pair["cells"]
                    and cell != elbow
                    and source[cell[0]][cell[1]] == 0
                    and all(cell not in path for path in selected_paths)
                ]
                for candidate in candidates:
                    moved = copy.deepcopy(source)
                    moved[elbow[0]][elbow[1]] = 0
                    moved[candidate[0]][candidate[1]] = gen.BLOCKER_COLOR
                    if gen.strict_canonical_like(moved):
                        continue
                    truth = gen.rule_mirror(moved)
                    rival = _elbow_only(gen, moved)
                    if truth == rival:
                        continue
                    return {
                        "seed": seed,
                        "sample_index": sample_index,
                        "pair_index": pair_index,
                        "moved_from": list(elbow),
                        "moved_to": list(candidate),
                        "input": moved,
                        "truth": truth,
                        "elbow_only": rival,
                    }
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--task", default="c7c9b61d5a51")
    parser.add_argument("--samples-per-band", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    generator_path = repo / "generators" / args.task / "generator.py"
    gen = _load(generator_path)
    canonical = _pairs(_canonical_row(repo, args.task))

    canonical_kinds = [_scene_kinds(gen, pair["input"]) for pair in canonical]
    generated_kinds: dict[str, list[list[str]]] = {}
    generated_agreement: dict[str, dict[str, int]] = {}
    for band in ("easy", "medium", "hard"):
        kinds = []
        agreements = 0
        for index in range(args.samples_per_band):
            grid = gen.generate(700_000 + index, index, difficulty=band)
            kinds.append(_scene_kinds(gen, grid))
            agreements += _elbow_only(gen, grid) == gen.rule_mirror(grid)
        generated_kinds[band] = kinds
        generated_agreement[band] = {
            "matches": agreements,
            "total": args.samples_per_band,
        }

    result = {
        "schema": "c7c9b61d5a51-blocker-clearance-probe-v1",
        "task_id": args.task,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "canonical_scene_kinds": canonical_kinds,
        "generated_kind_counts": {
            band: {
                kind: sum(scene.count(kind) for scene in scenes)
                for kind in ("elbow", "leg", "none", "unresolved")
            }
            for band, scenes in generated_kinds.items()
        },
        "elbow_only_generated_agreement": generated_agreement,
        "lawful_counterexample": _counterexample(gen),
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if result["lawful_counterexample"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
