#!/usr/bin/env python3
"""Replayable rival/profile probe for generator 7e19bce9c44c.

This stays task-local on purpose.  It reads the generator's *declared* rivals,
checks every declared canonical shortcut against every usable canonical pair,
then exhausts all ten schedule start residues and all four query rotations of a
three-demo/one-query block in every difficulty band.  It also repeats the
official 20-draw canonical-profile census so future schedule edits have one
small, fast regression command before the full battery.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

TASK_ID = "7e19bce9c44c"
BANDS = ("easy", "medium", "hard")
PERIOD = 10
N_DEMOS = 3


def _grid(value: Any) -> list[list[int]]:
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def _canonical_path(repo_root: Path) -> Path:
    path = repo_root / "shared/data/canonical/puzzles.jsonl"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _canonical_pairs(repo_root: Path) -> list[dict[str, list[list[int]]]]:
    pairs: list[dict[str, list[list[int]]]] = []
    with _canonical_path(repo_root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            train = row.get("train") or []
            test = row.get("test") or []
            if isinstance(train, dict):
                train = [train]
            if isinstance(test, dict):
                test = [test]
            for pair in train + test:
                if not isinstance(pair, dict):
                    continue
                pairs.append({
                    "input": _grid(pair["input"]),
                    "output": _grid(pair["output"]),
                })
    return pairs


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _declared_rules(gen: Any, name: str) -> dict[str, Callable]:
    value = getattr(gen, name, {})
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a dict")
    bad = [key for key, rule in value.items() if not callable(rule)]
    if bad:
        raise TypeError(f"{name} has non-callable entries: {bad}")
    return value


def _load_generator(repo_root: Path) -> Any:
    path = repo_root / f"generators/{TASK_ID}/generator.py"
    spec = importlib.util.spec_from_file_location(
        f"task_generator_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(gen: Any, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def run_probe(repo_root: Path) -> dict[str, Any]:
    gen = _load_generator(repo_root)
    generator_path = Path(gen.__file__)
    generator_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    canonical = _canonical_pairs(repo_root)
    canonical_profiles = {_profile(pair["input"]) for pair in canonical}
    shortcuts = _declared_rules(gen, "CANONICAL_SHORTCUTS")
    competitors = _declared_rules(gen, "LESSON_COMPETITORS")

    shortcut_fit: dict[str, Any] = {}
    for name, rival in sorted(shortcuts.items()):
        mismatches = []
        for index, pair in enumerate(canonical):
            prediction = rival(copy.deepcopy(pair["input"]))
            if prediction != pair["output"]:
                mismatches.append(index)
        shortcut_fit[name] = {
            "pairs": len(canonical),
            "fits": len(canonical) - len(mismatches),
            "mismatch_indices": mismatches,
        }

    windows = []
    ambiguity_count = 0
    competitor_survivors = {name: 0 for name in competitors}
    first_counterexample = None
    for band_index, band in enumerate(BANDS):
        seed = 7_190_000 + band_index
        for start in range(PERIOD):
            block = [
                _pair(gen, seed, start + offset, band)
                for offset in range(N_DEMOS + 1)
            ]
            for query_offset in range(N_DEMOS + 1):
                demos = [
                    pair for index, pair in enumerate(block)
                    if index != query_offset
                ]
                query = block[query_offset]
                reasons = gen.lesson_identifiable(demos, query)
                ambiguity_count += bool(reasons)
                survivors = []
                for name, rival in competitors.items():
                    if all(
                        rival(copy.deepcopy(pair["input"])) == pair["output"]
                        for pair in demos
                    ):
                        survivors.append(name)
                        competitor_survivors[name] += 1
                windows.append({
                    "band": band,
                    "seed": seed,
                    "start": start,
                    "query_offset": query_offset,
                    "reasons": reasons,
                    "surviving_competitors": survivors,
                })

            if first_counterexample is None:
                for pair in block:
                    for name, rival in shortcuts.items():
                        rival_output = rival(copy.deepcopy(pair["input"]))
                        if rival_output != pair["output"]:
                            first_counterexample = {
                                "shortcut": name,
                                "band": band,
                                "seed": seed,
                                "sample_index": start + block.index(pair),
                                "input": pair["input"],
                                "intended_output": pair["output"],
                                "rival_output": rival_output,
                            }
                            break
                    if first_counterexample is not None:
                        break

    profile_floor: dict[str, Any] = {}
    for band in BANDS:
        exact = 0
        profiles: dict[str, int] = {}
        for index in range(20):
            seed = _pinned_seed(band, index)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            profile = _profile(grid)
            exact += profile in canonical_profiles
            key = "x".join(map(str, profile))
            profiles[key] = profiles.get(key, 0) + 1
        profile_floor[band] = {
            "draws": 20,
            "exact_canonical_profile_hits": exact,
            "profiles": dict(sorted(profiles.items())),
        }

    errors = []
    for name, row in shortcut_fit.items():
        if row["fits"] != row["pairs"]:
            errors.append(f"canonical shortcut {name!r} does not fit all pairs")
    if ambiguity_count:
        errors.append(f"{ambiguity_count}/{len(windows)} rotated windows ambiguous")
    for band, row in profile_floor.items():
        if row["exact_canonical_profile_hits"] == 0:
            errors.append(f"{band} has zero exact canonical-profile hits")
    if first_counterexample is None:
        errors.append("no generated counterexample found for declared shortcuts")

    return {
        "schema": "7e19bce9c44c-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "generator_version": getattr(gen, "VERSION", None),
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit": shortcut_fit,
        "lesson_policy": {
            "bands": list(BANDS),
            "starts": list(range(PERIOD)),
            "pairs_per_block": N_DEMOS + 1,
            "query_rotations_per_block": N_DEMOS + 1,
            "rotated_windows": len(windows),
        },
        "ambiguous_rotated_windows": ambiguity_count,
        "competitor_survivor_counts": competitor_survivors,
        "first_generated_shortcut_counterexample": first_counterexample,
        "profile_floor": profile_floor,
        "errors": errors,
        "status": "pass" if not errors else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    repo_root = Path.cwd()
    report = run_probe(repo_root)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
