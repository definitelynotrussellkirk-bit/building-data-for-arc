#!/usr/bin/env python3
"""Exhaust the finite generator contract and retain a shortcut witness.

This is a source-bound reviewer/maintainer tool, not a replacement for the
Racket authority.  It checks the task-local Python mirror against every labeled
canonical pair, verifies that the declared canonical shortcut also fits those
pairs, enumerates every exact ``scene_profile`` override, and saves one concrete
input where the shortcut and intended transformation disagree.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_GENERATOR = HERE.parent / "generator.py"
REPO_ROOT = HERE.parents[2]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("contract_probe_generator", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    spec.loader.exec_module(module)
    return module


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def analyze(generator_path: Path | str = DEFAULT_GENERATOR) -> dict[str, Any]:
    """Return a deterministic, JSON-serializable contract report."""
    generator_path = Path(generator_path).resolve()
    gen = _load_generator(generator_path)
    root = find_root(__file__)
    pairs = canonical_pairs(gen.TASK_ID, root=root, labeled_only=True)
    shortcut = gen.CANONICAL_SHORTCUTS["canonical_size_to_count"]

    mirror_matches = sum(gen.rule_mirror(pair["input"]) == pair["output"] for pair in pairs)
    shortcut_fits = sum(shortcut(pair["input"]) == pair["output"] for pair in pairs)

    lawful = 0
    observed_exactly = 0
    distinguishing = 0
    output_keys: set[tuple[tuple[int, ...], ...]] = set()
    witness: dict[str, Any] | None = None

    for index, profile in enumerate(gen.SCENE_PROFILES):
        seed = 20261011 + index
        grid = gen.generate(seed, index, scene_profile=profile)
        errors = gen.self_check(grid)
        observed = gen.observe_overrides(grid)
        intended = gen.rule_mirror(grid)
        rival = shortcut(grid)

        lawful += not errors
        observed_exactly += observed == {"scene_profile": profile}
        distinguishing += intended != rival
        output_keys.add(_grid_key(intended))

        if profile == "n11_vertical_c7":
            witness = {
                "profile": profile,
                "seed": seed,
                "sample_index": index,
                "self_check": errors,
                "observed": observed,
                "input": grid,
                "intended_output": intended,
                "rival_output": rival,
            }

    profile_count = len(gen.SCENE_PROFILES)
    report = {
        "schema": "5c0bcc9d1b8b-contract-probe/1",
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "canonical_pairs": len(pairs),
        "canonical_mirror_matches": mirror_matches,
        "canonical_shortcut_fits": shortcut_fits,
        "profile_count": profile_count,
        "profiles_lawful": lawful,
        "profiles_observed_exactly": observed_exactly,
        "profiles_distinguishing": distinguishing,
        "declared_output_codomain": gen.EXPECTED_OUTPUT_CODOMAIN,
        "distinct_outputs": len(output_keys),
        "counterexample": witness,
    }
    report["ok"] = all(
        (
            len(pairs) > 0,
            mirror_matches == len(pairs),
            shortcut_fits == len(pairs),
            lawful == profile_count,
            observed_exactly == profile_count,
            distinguishing == profile_count,
            len(output_keys) == gen.EXPECTED_OUTPUT_CODOMAIN,
            witness is not None,
        )
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    report = analyze(args.generator)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "generator_sha256": report["generator_sha256"],
                "profiles": report["profile_count"],
                "distinguishing": report["profiles_distinguishing"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
