#!/usr/bin/env python3
"""Replay the enclosure curriculum against its declared shortcut family.

The probe is source-bound and portable: it loads the sibling generator, reads
canonical pairs through ``reviewer_support``, discovers rival functions from the
generator's public semantic contract, and checks every contiguous lesson window.
It is diagnostic only; labels are produced by the generator's explicitly marked
Python mirror, never by this script as an authority substitute.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "5a70e1b62a50"
BANDS = ("easy", "medium", "hard")
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
GENERATOR_PATH = TASK_HOME / "generator.py"

for _path in (REPO_ROOT / "shared/runtime", REPO_ROOT / "src", REPO_ROOT):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"curriculum_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid_key(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _pair(gen: Any, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def collect(*, seed_count: int = 8, samples_per_seed: int = 16) -> dict[str, Any]:
    """Return a JSON-serializable census of canonical and generated lessons."""
    if type(seed_count) is not int or seed_count <= 0:
        raise ValueError("seed_count must be a positive integer")
    if type(samples_per_seed) is not int or samples_per_seed <= 0:
        raise ValueError("samples_per_seed must be a positive integer")

    gen = _load_generator()
    examples_needed = int(getattr(gen, "EXAMPLES_NEEDED", 0))
    if examples_needed <= 0:
        raise ValueError("generator must declare positive EXAMPLES_NEEDED")
    if samples_per_seed <= examples_needed:
        raise ValueError("samples_per_seed must exceed EXAMPLES_NEEDED")

    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    if not shortcuts:
        raise ValueError("generator declares no CANONICAL_SHORTCUTS")
    if not competitors:
        raise ValueError("generator declares no LESSON_COMPETITORS")
    if not callable(getattr(gen, "lesson_identifiable", None)):
        raise ValueError("generator declares no callable lesson_identifiable")

    root = find_root(HERE)
    canonical = canonical_pairs(
        TASK_ID, root=root, variant=0, labeled_only=True
    )
    canonical_shortcut_matches = {
        name: sum(fn(pair["input"]) == pair["output"] for pair in canonical)
        for name, fn in shortcuts.items()
    }

    profiles_per_band: dict[str, set[str]] = {band: set() for band in BANDS}
    counterexamples_per_band: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    lesson_failures: list[dict[str, Any]] = []
    rival_survivor_windows: list[dict[str, Any]] = []
    draws = 0
    lesson_windows = 0

    for band in BANDS:
        for seed in range(seed_count):
            pairs: list[dict[str, list[list[int]]]] = []
            for sample_index in range(samples_per_seed):
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    lesson_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "stage": "self_check",
                            "errors": list(errors),
                        }
                    )
                profile = gen.profile_signature(grid)
                profiles_per_band[band].add(profile)
                pair = _pair(gen, grid)
                pairs.append(pair)
                draws += 1
                unique_inputs.add(_grid_key(grid))

                bbox = competitors.get("global_color_bbox")
                if bbox is not None and bbox(grid) != pair["output"]:
                    counterexamples_per_band[band] += 1

            # Every contiguous window has EXAMPLES_NEEDED demonstrations and
            # the immediately following item as its held-out query.
            for start in range(samples_per_seed - examples_needed):
                demos = pairs[start:start + examples_needed]
                query = pairs[start + examples_needed]
                lesson_windows += 1
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    lesson_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "stage": "lesson_identifiable",
                            "errors": list(reasons),
                        }
                    )
                for name, rival in competitors.items():
                    if all(
                        rival(pair["input"]) == pair["output"]
                        for pair in demos
                    ):
                        rival_survivor_windows.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "rival": name,
                                "changes_query": (
                                    rival(query["input"]) != query["output"]
                                ),
                            }
                        )

    return {
        "schema_version": 1,
        "task_id": TASK_ID,
        "generator_sha256": _sha256(GENERATOR_PATH),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "parameters": {
            "seed_count": seed_count,
            "samples_per_seed": samples_per_seed,
            "bands": list(BANDS),
            "examples_needed": examples_needed,
        },
        "canonical_pairs": len(canonical),
        "canonical_shortcut_matches": canonical_shortcut_matches,
        "declared_competitors": sorted(competitors),
        "draws": draws,
        "unique_inputs": len(unique_inputs),
        "profiles_per_band": {
            band: sorted(profile for profile in profiles if profile is not None)
            for band, profiles in profiles_per_band.items()
        },
        "bbox_counterexamples_per_band": {
            band: counterexamples_per_band[band] for band in BANDS
        },
        "lesson_windows": lesson_windows,
        "lesson_failures": lesson_failures,
        "rival_survivor_windows": rival_survivor_windows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-count", type=int, default=8)
    parser.add_argument("--samples-per-seed", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = collect(
        seed_count=args.seed_count,
        samples_per_seed=args.samples_per_seed,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 1 if report["lesson_failures"] or report["rival_survivor_windows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
