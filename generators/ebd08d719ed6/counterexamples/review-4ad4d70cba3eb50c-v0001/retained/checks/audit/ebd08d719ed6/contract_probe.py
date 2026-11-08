#!/usr/bin/env python3
"""Reproduce public override/self-check contract defects for ebd08d719ed6."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "ebd08d719ed6"
HERE = Path(__file__).resolve()


def packet_root() -> Path:
    for parent in HERE.parents:
        if (parent / "repo" / "generators" / TASK_ID / "generator.py").is_file():
            return parent
    raise RuntimeError("could not locate packet root")


def load_generator(path: Path):
    repo = packet_root() / "repo"
    sys.path.insert(0, str(repo / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_hash(grid: Any) -> str:
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()


def tile_counts(grid: list[list[int]]) -> list[int]:
    h, w = len(grid), len(grid[0])
    sep_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]

    def spans(n: int, separators: list[int]):
        previous = -1
        for current in separators + [n]:
            if current - previous - 1 > 0:
                yield previous + 1, current
            previous = current

    return [
        sum(grid[r][c] != 0 for r in range(r1, r2) for c in range(c1, c2))
        for r1, r2 in spans(h, sep_rows)
        for c1, c2 in spans(w, sep_cols)
    ]


def describe(gen, call) -> dict[str, Any]:
    try:
        grid = call()
    except Exception as exc:  # exact public failure is evidence
        return {"status": "raised", "error": f"{type(exc).__name__}: {exc}"}
    return {
        "status": "returned",
        "shape": [len(grid), len(grid[0])],
        "sha256": grid_hash(grid),
        "tile_counts": tile_counts(grid),
        "self_check": gen.self_check(grid),
    }


def build(generator_path: Path) -> dict[str, Any]:
    gen = load_generator(generator_path)
    baseline = gen.generate(0, 0)
    unknown = describe(
        gen,
        lambda: gen.generate(0, 0, __override_contract_unknown_axis__=1),
    )
    warm_texture = gen.generate(0, 0, texture="warm")
    cool_texture = gen.generate(0, 0, texture="cool")
    warm_palette = gen.generate(0, 0, palette_kind="warm")
    cool_palette = gen.generate(0, 0, palette_kind="cool")
    single = gen.generate(0, 0, texture="single_tile")

    return {
        "schema": "audit-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "axes": getattr(gen, "AXES", None),
        "unknown_override": {
            "call": unknown,
            "equal_to_baseline": unknown.get("status") == "returned"
            and unknown.get("sha256") == grid_hash(baseline),
        },
        "helpful_texture_dead": {
            "warm_sha256": grid_hash(warm_texture),
            "cool_sha256": grid_hash(cool_texture),
            "warm_equals_cool": warm_texture == cool_texture,
        },
        "palette_kind_dead": {"warm_equals_cool": warm_palette == cool_palette},
        "max_density_outside_declared_domain": {
            "override_4": describe(gen, lambda: gen.generate(0, 0, max_density=4)),
            "override_100": describe(gen, lambda: gen.generate(0, 0, max_density=100)),
        },
        "advertised_axis_boundary_rejections": {
            "easy_tile_rows_1": describe(
                gen, lambda: gen.generate(0, 0, difficulty="easy", tile_rows=1)
            ),
            "easy_tile_cols_1": describe(
                gen, lambda: gen.generate(0, 0, difficulty="easy", tile_cols=1)
            ),
            "default_tile_rows_5": describe(
                gen, lambda: gen.generate(0, 0, tile_rows=5)
            ),
            "default_tile_cols_6": describe(
                gen, lambda: gen.generate(0, 0, tile_cols=6)
            ),
        },
        "degenerate_single_tile": {
            "shape": [len(single), len(single[0])],
            "tile_counts": tile_counts(single),
            "self_check": gen.self_check(single),
        },
    }


def main() -> int:
    root = packet_root()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=root / "repo" / "generators" / TASK_ID / "generator.py",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build(args.generator.resolve())
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
