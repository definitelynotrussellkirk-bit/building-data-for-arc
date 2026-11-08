#!/usr/bin/env python3
"""Isolated episode-level tile-count prototype for adcdcbe48f64.

This file is authoring evidence only.  It does not change the selected
production generator, canonical rule, or public generation API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "adcdcbe48f64"
DEFAULT_TILE_COUNT = 5
TILE_COUNTS = (3, 5)
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
CANONICAL_RECORD = (
    ROOT
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "bc4146bd__adcdcbe48f64.json"
)
PROTOTYPE_SCHEMA = "arcpuzzles-alternating-tile-count-prototype-v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_rule() -> str:
    record = json.loads(CANONICAL_RECORD.read_text())
    if record.get("task_id") != TASK_ID:
        raise ValueError("canonical authority task ID mismatch")
    return record["racket_target"]["target_code"]


def rule_hash(source: str) -> str:
    """Use the catalog's whitespace-normalized SHA-256 convention."""
    return digest(" ".join(source.split()).encode())


def _validate_tile_count(tile_count: Any) -> int:
    if type(tile_count) is not int:
        raise TypeError("tile_count must be a literal integer")
    if tile_count not in TILE_COUNTS:
        raise ValueError(f"tile_count must be one of {TILE_COUNTS!r}")
    return tile_count


def materialize_rule(tile_count: int = DEFAULT_TILE_COUNT) -> str:
    """Return exact executable Racket for one fixed episode setting."""
    count = _validate_tile_count(tile_count)
    source = canonical_rule()
    if count == DEFAULT_TILE_COUNT:
        return source
    needle = f"(* w {DEFAULT_TILE_COUNT})"
    if source.count(needle) != 1:
        raise RuntimeError("canonical source no longer has one tile-count literal")
    return source.replace(needle, f"(* w {count})", 1)


def choose_tile_count(seed: int) -> int:
    """Choose exactly once per episode using a stable task-bound digest."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    index = hashlib.sha256(f"{TASK_ID}:tile_count:{seed}".encode()).digest()[0] % len(TILE_COUNTS)
    return TILE_COUNTS[index]


def python_apply(grid: list[list[int]], tile_count: int) -> list[list[int]]:
    count = _validate_tile_count(tile_count)
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
        or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)
    ):
        raise ValueError("grid must be a rectangular ARC integer grid")
    output = []
    for row in grid:
        original = list(row)
        mirror = list(reversed(row))
        tiles = [original if index % 2 == 0 else mirror for index in range(count)]
        output.append([cell for tile in tiles for cell in tile])
    return output


def execute_rule(source: str, inputs: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the exact materialized rule with the included Racket bridge."""
    outputs = []
    with RacketBridge(timeout=15.0, startup_timeout=60.0) as bridge:
        for index, grid in enumerate(inputs):
            # The Python oracle also performs strict input validation.
            python_apply(grid, DEFAULT_TILE_COUNT)
            name = f"parametric-input-{index}"
            bridge.define_grid(name, grid)
            out = bridge.eval_text(
                f"(let ([rule! (lambda (f) f)]) ({source} {name}))"
            )
            if (
                not isinstance(out, list)
                or len(out) != len(grid)
                or not out
                or any(not isinstance(row, list) or not row for row in out)
                or any(type(cell) is not int or not 0 <= cell <= 9 for row in out for cell in row)
            ):
                raise RuntimeError("Racket output is not a rectangular ARC grid")
            width = len(out[0])
            if any(len(row) != width for row in out):
                raise RuntimeError("Racket output is not rectangular")
            outputs.append(out)
    return outputs


def build_episode(
    seed: int,
    *,
    tile_count: int | None = None,
    difficulty: str | None = "medium",
    start: int = 0,
) -> dict[str, Any]:
    """Build three demonstrations and one query under one fixed hidden count."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")
    if type(start) is not int or start < 0:
        raise ValueError("start must be a nonnegative literal integer")
    chosen = choose_tile_count(seed) if tile_count is None else _validate_tile_count(tile_count)
    rival = TILE_COUNTS[1 - TILE_COUNTS.index(chosen)]

    generator, _, generator_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    inputs = [
        generator.generate(seed, start + offset, difficulty=difficulty)
        for offset in range(4)
    ]
    for grid in inputs:
        errors = generator.self_check(grid, difficulty=difficulty)
        if errors:
            raise RuntimeError(f"production generator returned an unlawful input: {errors}")

    source = materialize_rule(chosen)
    rival_source = materialize_rule(rival)
    outputs = execute_rule(source, inputs)
    rival_outputs = execute_rule(rival_source, inputs)
    expected = [python_apply(grid, chosen) for grid in inputs]
    rival_expected = [python_apply(grid, rival) for grid in inputs]
    if outputs != expected or rival_outputs != rival_expected:
        raise AssertionError("Racket and independent Python labels disagree")

    rejected = [index for index in range(3) if outputs[index] != rival_outputs[index]]
    if rejected != [0, 1, 2]:
        raise RuntimeError("all demonstrations must distinguish the tile-count rival")
    if outputs[3] == rival_outputs[3]:
        raise RuntimeError("query must distinguish the tile-count rival")

    challenge = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(inputs[:3], outputs[:3])
        ],
        "test": [{"input": inputs[3]}],
    }
    private = {
        "schema": PROTOTYPE_SCHEMA,
        "status": "proposed prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": difficulty,
        "start": start,
        "parameters": {"tile_count": chosen},
        "parameter_domain": {"tile_count": list(TILE_COUNTS)},
        "canonical_setting": {"tile_count": DEFAULT_TILE_COUNT},
        "chosen_once_per_episode": True,
        "selection": "seeded once" if tile_count is None else "explicit once",
        "query_outputs": outputs[3:],
        "generator_sha256": generator_sha256,
        "racket_text": source,
        "racket_text_sha256": digest(source.encode()),
        "rule_hash": rule_hash(source)[:12],
        "input_sha256": [
            digest(json.dumps(grid, separators=(",", ":")).encode()) for grid in inputs
        ],
        "rival_setting_check": {
            "tile_count": rival,
            "racket_text_sha256": digest(rival_source.encode()),
            "rejected_by_demo_indices": rejected,
            "query_disagrees": rival_outputs[3] != outputs[3],
            "rival_outputs": rival_outputs,
        },
        "all_pairs_separate_settings": all(
            output != rival_output for output, rival_output in zip(outputs, rival_outputs)
        ),
        "sampling": {
            "sample_indices": list(range(start, start + 4)),
            "rule_selection": "before all input draws",
        },
        "variant_approved": False,
        "production_parametric_api": False,
    }
    return {"challenge": challenge, "private": private}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _find_seed_per_count(seed_start: int, limit: int = 128) -> dict[int, int]:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative literal integer")
    found: dict[int, int] = {}
    for seed in range(seed_start, seed_start + limit):
        found.setdefault(choose_tile_count(seed), seed)
        if set(found) == set(TILE_COUNTS):
            return found
    raise RuntimeError(f"did not observe both tile counts in {limit} seeds")


def source_hashes() -> dict[str, str]:
    paths = [
        Path(__file__),
        Path(__file__).with_name("README.md"),
        TASK_HOME / "generator.py",
        TASK_HOME / "tests" / "test_parametric_tile_count.py",
        CANONICAL_RECORD,
        ROOT / "shared" / "runtime" / "reviewer_support.py",
        ROOT / "shared" / "runtime" / "arc_repl" / "racket_bridge.py",
        ROOT / "shared" / "runtime" / "arc_repl" / "racket_prelude" / "arc-prelude.rkt",
    ]
    return {
        str(path.relative_to(ROOT)): digest(path.read_bytes())
        for path in paths
        if path.is_file()
    }


def build_evidence(out: Path, *, seed_start: int = 71, difficulty: str = "medium") -> dict[str, Any]:
    """Materialize replayable public/private evidence for both settings."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {out}")
    out.mkdir(parents=True)

    seed_by_count = _find_seed_per_count(seed_start)
    episodes = [
        build_episode(seed_by_count[count], tile_count=None, difficulty=difficulty)
        for count in TILE_COUNTS
    ]

    for index, episode in enumerate(episodes):
        _write_json(out / "public" / f"episode-{index:03d}" / "challenge.json", episode["challenge"])
        _write_json(out / "private" / f"episode-{index:03d}.json", episode["private"])
        (out / "private" / f"episode-{index:03d}.rkt").write_text(
            episode["private"]["racket_text"] + "\n"
        )

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_outputs = execute_rule(materialize_rule(DEFAULT_TILE_COUNT), [p["input"] for p in pairs])
    parity = [
        {
            "variant": pair.get("variant"),
            "split": pair.get("split"),
            "pair_index": pair.get("pair_index"),
            "equal": actual == pair["output"],
        }
        for pair, actual in zip(pairs, canonical_outputs)
    ]
    if not all(item["equal"] for item in parity):
        raise RuntimeError("default tile_count disagrees with canonical labels")
    _write_json(out / "private" / "canonical-parity.json", parity)

    witness_grid = pairs[0]["input"]
    witness_outputs = {
        str(count): execute_rule(materialize_rule(count), [witness_grid])[0]
        for count in TILE_COUNTS
    }
    witness = {
        "input": witness_grid,
        "outputs": witness_outputs,
        "settings_disagree": witness_outputs["3"] != witness_outputs["5"],
    }
    if not witness["settings_disagree"]:
        raise RuntimeError("same-input count witness does not discriminate")
    _write_json(out / "private" / "same-input-witness.json", witness)

    report = {
        "schema": "arcpuzzles-alternating-tile-count-verification-v1",
        "status": "proposed prototype",
        "task_id": TASK_ID,
        "parameters": {
            "tile_count": {
                "allowed": list(TILE_COUNTS),
                "canonical_default": DEFAULT_TILE_COUNT,
                "chosen_once_per_episode": True,
                "input_constraints_depend_on_parameter": False,
            }
        },
        "seed_search": {
            "start": seed_start,
            "limit": 128,
            "selected_private_seeds": {str(k): v for k, v in seed_by_count.items()},
        },
        "prototype_source_hashes": source_hashes(),
        "rules": {
            str(count): {
                "text": materialize_rule(count),
                "text_sha256": digest(materialize_rule(count).encode()),
                "rule_hash": rule_hash(materialize_rule(count))[:12],
            }
            for count in TILE_COUNTS
        },
        "canonical_parity": {
            "checked": len(parity),
            "passed": sum(item["equal"] for item in parity),
        },
        "episodes": [
            {
                "public": f"public/episode-{index:03d}/challenge.json",
                "private": f"private/episode-{index:03d}.json",
                "tile_count": episode["private"]["parameters"]["tile_count"],
                "seed": episode["private"]["seed"],
                "all_pairs_separate_settings": episode["private"]["all_pairs_separate_settings"],
            }
            for index, episode in enumerate(episodes)
        ],
        "runtime": racket_runtime_status(),
        "command": list(sys.argv),
        "variant_approved": False,
        "production_parametric_api": False,
        "limits": (
            "Two bounded count settings and two deterministic episodes; finite evidence only. "
            "This does not establish universal identifiability, solver benefit, or training admission."
        ),
    }
    _write_json(out / "report.json", report)

    files = [
        {
            "path": str(path.relative_to(out)),
            "sha256": digest(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    manifest = {
        "schema": "arcpuzzles-parametric-evidence-manifest-v1",
        "task_id": TASK_ID,
        "files": files,
    }
    _write_json(out / "manifest.json", manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=71)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build_evidence(args.out, seed_start=args.seed_start, difficulty=args.difficulty)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
