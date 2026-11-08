#!/usr/bin/env python3
"""Source-bound distribution probe for task 0f7d80015d9d.

The production lesson sampler always requests a small fixed index window.  This
probe measures that window directly, as well as the longer schedule claimed by
the generator, so periodic sample-index logic cannot hide behind a long-run
average.  It also records marker placement, rectangle support, edge contact,
strict-profile hits, and input/output uniqueness.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

TASK_ID = "0f7d80015d9d"
DIFFICULTIES = ("easy", "medium", "hard")


def _bootstrap_runtime(source_path: Path) -> None:
    """Locate the packet or staged ``puzzle_generators`` runtime."""
    starts = (Path(__file__).resolve(), source_path.resolve())
    checked: set[Path] = set()
    for start in starts:
        for ancestor in (start.parent, *start.parents):
            for candidate in (ancestor, ancestor / "shared" / "runtime"):
                candidate = candidate.resolve()
                if candidate in checked:
                    continue
                checked.add(candidate)
                if (candidate / "puzzle_generators" / "base.py").is_file():
                    sys.path.insert(0, str(candidate))
                    return
    raise RuntimeError(
        "cannot locate puzzle_generators runtime beside the probe or generator source"
    )


def _load_generator(path: Path) -> ModuleType:
    _bootstrap_runtime(path)
    raw = path.read_bytes()
    name = f"distribution_probe_{hashlib.sha256(raw).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _anchor_fn(module: ModuleType):
    fn = module._canonical_anchor
    arity = len(inspect.signature(fn).parameters)
    if arity == 1:
        return lambda seed, sample_index: bool(fn(sample_index))
    if arity == 2:
        return lambda seed, sample_index: bool(fn(seed, sample_index))
    raise RuntimeError(f"unsupported _canonical_anchor arity: {arity}")


def _counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _bounds(values: list[int]) -> dict[str, int] | None:
    if not values:
        return None
    return {"min": min(values), "max": max(values)}


def measure(
    module: ModuleType,
    *,
    source_path: Path,
    seeds: int,
    episode_pairs: int,
    schedule_indices: int,
) -> dict[str, Any]:
    anchor = _anchor_fn(module)
    source_raw = source_path.read_bytes()

    episode_anchor_hist = Counter(
        sum(anchor(seed, index) for index in range(episode_pairs))
        for seed in range(seeds)
    )
    schedule_anchor_count = sum(
        anchor(seed, index)
        for seed in range(seeds)
        for index in range(schedule_indices)
    )

    bands: dict[str, Any] = {}
    for difficulty in DIFFICULTIES:
        input_hashes: set[str] = set()
        output_hashes: set[str] = set()
        profiles: Counter[str] = Counter()
        aspects: Counter[str] = Counter()
        rect_heights: list[int] = []
        rect_widths: list[int] = []
        strict_hits = 0
        anchor_hits = 0
        anchor_cap_hits = 0
        left_edge = 0
        right_edge = 0
        total = seeds * episode_pairs

        for seed in range(seeds):
            for sample_index in range(episode_pairs):
                grid = module.generate(seed, sample_index, difficulty=difficulty)
                facts = module._analyze(grid)
                if facts["errors"]:
                    raise AssertionError(facts["errors"])
                output = module.rule_mirror(grid)
                input_hashes.add(_grid_hash(grid))
                output_hashes.add(_grid_hash(output))
                profiles[facts["scene_profile"]] += 1
                aspects[facts["rect_aspect"]] += 1
                rect_heights.append(facts["rect_h"])
                rect_widths.append(facts["rect_w"])
                strict_hits += int(not module.strict_canonical_like(grid))
                left_edge += int(facts["rect"][2] == 0)
                right_edge += int(facts["rect"][3] == facts["width"] - 1)

                if anchor(seed, sample_index):
                    anchor_hits += 1
                    cap_row = facts["rect"][0] - 1
                    anchor_cap_hits += int(
                        facts["red"][0] == cap_row and facts["cyan"][0] == cap_row
                    )

        bands[difficulty] = {
            "pairs": total,
            "anchor_hits": anchor_hits,
            "anchor_cap_row_hits": anchor_cap_hits,
            "strict_canonical_hits": strict_hits,
            "unique_inputs": len(input_hashes),
            "unique_outputs": len(output_hashes),
            "profiles": _counter(profiles),
            "aspects": _counter(aspects),
            "rect_height": _bounds(rect_heights),
            "rect_width": _bounds(rect_widths),
            "left_edge_contacts": left_edge,
            "right_edge_contacts": right_edge,
        }

    forced_sizes: dict[str, dict[str, Any]] = {}
    for aspect, profile in (
        ("wide", "left_opposite"),
        ("tall", "right_opposite"),
        ("square", "right_same_side"),
    ):
        heights: list[int] = []
        widths: list[int] = []
        pairs: set[tuple[int, int]] = set()
        for seed in range(seeds):
            grid = module.generate(
                seed,
                7,
                difficulty="hard",
                grid_h=19,
                grid_w=19,
                rect_aspect=aspect,
                scene_profile=profile,
            )
            facts = module._analyze(grid)
            heights.append(facts["rect_h"])
            widths.append(facts["rect_w"])
            pairs.add((facts["rect_h"], facts["rect_w"]))
        forced_sizes[aspect] = {
            "rect_height": _bounds(heights),
            "rect_width": _bounds(widths),
            "distinct_size_pairs": len(pairs),
        }

    forced_edges: dict[str, Any] = {}
    for profile in ("left_opposite", "right_opposite"):
        left_count = 0
        right_count = 0
        for seed in range(seeds):
            grid = module.generate(
                seed,
                9,
                grid_h=9,
                grid_w=9,
                rect_aspect="wide",
                scene_profile=profile,
            )
            facts = module._analyze(grid)
            left_count += int(facts["rect"][2] == 0)
            right_count += int(facts["rect"][3] == facts["width"] - 1)
        forced_edges[profile] = {
            "draws": seeds,
            "left_edge_contacts": left_count,
            "right_edge_contacts": right_count,
        }

    total_schedule_draws = seeds * schedule_indices
    return {
        "schema": "0f7d80015d9d-distribution-probe-v1",
        "task_id": TASK_ID,
        "version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "generator_path": str(source_path),
        "generator_sha256": hashlib.sha256(source_raw).hexdigest(),
        "parameters": {
            "seeds": seeds,
            "episode_pairs": episode_pairs,
            "schedule_indices": schedule_indices,
            "difficulties": list(DIFFICULTIES),
        },
        "schedule": {
            "episode_anchor_count_histogram": _counter(episode_anchor_hist),
            "long_run_anchor_hits": schedule_anchor_count,
            "long_run_draws": total_schedule_draws,
            "long_run_anchor_fraction": schedule_anchor_count / total_schedule_draws,
        },
        "production_episode_bands": bands,
        "forced_19x19_size_support": forced_sizes,
        "forced_9x9_edge_support": forced_edges,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    default_generator = Path(__file__).resolve().parents[1] / "generator.py"
    parser.add_argument("--generator", type=Path, default=default_generator)
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--episode-pairs", type=int, default=6)
    parser.add_argument("--schedule-indices", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    source = args.generator.resolve()
    report = measure(
        _load_generator(source),
        source_path=source,
        seeds=args.seeds,
        episode_pairs=args.episode_pairs,
        schedule_indices=args.schedule_indices,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
