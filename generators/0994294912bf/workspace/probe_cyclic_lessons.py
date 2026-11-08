#!/usr/bin/env python3
"""Source-bound exhaustive cyclic-window probe for generator 0994294912bf.

This reviewer tool exercises the selected generator's real default sampler,
``EXAMPLES_NEEDED``, schedule declaration, Python rule mirror, and declared
``LESSON_COMPETITORS``.  It is deliberately independent of the shared lesson
census: the census rotates queries inside sampled lessons, while this probe
checks every requested consecutive schedule start.  The Racket authority is
still checked by the normal battery and census; this is a fast regression tool.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "outline_analogy_generator_for_probe", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid) -> str:
    encoded = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_inputs(
    seeds: Iterable[int], starts: int, bands: Iterable[str]
) -> tuple[tuple[int, ...], tuple[str, ...]]:
    seed_values = tuple(int(seed) for seed in seeds)
    band_values = tuple(str(band) for band in bands)
    if not seed_values:
        raise ValueError("seeds must be nonempty")
    if starts < 1:
        raise ValueError("starts must be positive")
    if not band_values or any(
        band not in ("easy", "medium", "hard") for band in band_values
    ):
        raise ValueError("bands must be a nonempty subset of easy, medium, hard")
    return seed_values, band_values


def run_probe(
    *,
    seeds: Iterable[int] = (17, 4242, 424242),
    starts: int = 16,
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict:
    """Check every consecutive default lesson window in the requested range."""
    seed_values, band_values = _validate_inputs(seeds, starts, bands)
    gen = _load_generator()
    n_demos = int(gen.EXAMPLES_NEEDED)
    rivals = dict(gen.LESSON_COMPETITORS)
    source_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()

    report = {
        "schema": "outline-analogy-cyclic-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": source_sha,
        "declared_rule_hash": gen.RULE_HASH,
        "seeds": list(seed_values),
        "starts_per_seed": starts,
        "bands_requested": list(band_values),
        "examples_needed": n_demos,
        "lesson_policy": (
            f"{n_demos} consecutive default samples as demonstrations; "
            "the next sample as query"
        ),
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "rivals": sorted(rivals),
        "bands": {},
        "errors": [],
        "rotation_errors": [],
    }

    for band in band_values:
        profile_counts: Counter[str] = Counter()
        observed_texture_counts: Counter[str] = Counter()
        rival_refuted_counts = Counter({name: 0 for name in rivals})
        identifiable = 0
        identifiable_rotations = 0
        total_rotations = 0
        total_windows = 0
        window_records = []

        for seed in seed_values:
            for start in range(starts):
                total_windows += 1
                pairs = []
                profiles = []
                textures = []
                input_hashes = []
                schedule_mismatches = []

                for sample_index in range(start, start + n_demos + 1):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    output = gen._mirror(grid)
                    if output is None:
                        raise RuntimeError(
                            f"Python mirror rejected generated grid at "
                            f"band={band} seed={seed} sample_index={sample_index}"
                        )
                    profile = str(
                        gen.schedule_profile(seed, sample_index, difficulty=band)
                    )
                    texture = str(gen.observe_overrides(grid)["texture"])
                    if profile != texture:
                        schedule_mismatches.append(
                            {
                                "sample_index": sample_index,
                                "declared_profile": profile,
                                "observed_texture": texture,
                            }
                        )
                    profile_counts[profile] += 1
                    observed_texture_counts[texture] += 1
                    profiles.append(profile)
                    textures.append(texture)
                    input_hashes.append(_grid_hash(grid))
                    pairs.append({"input": grid, "output": output})

                demos, query = pairs[:-1], pairs[-1]
                reasons = list(gen.lesson_identifiable(demos, query))
                survivors = sorted(
                    name
                    for name, rival in rivals.items()
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                )
                for name in rivals:
                    if name not in survivors:
                        rival_refuted_counts[name] += 1

                success = not reasons and not survivors and not schedule_mismatches
                if success:
                    identifiable += 1
                else:
                    report["errors"].append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "profiles": profiles,
                            "textures": textures,
                            "reasons": reasons,
                            "surviving_rivals": survivors,
                            "schedule_mismatches": schedule_mismatches,
                            "input_sha256": input_hashes,
                        }
                    )

                rotation_records = []
                for query_index, rotated_query in enumerate(pairs):
                    total_rotations += 1
                    rotated_demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    rotated_reasons = list(
                        gen.lesson_identifiable(rotated_demos, rotated_query)
                    )
                    rotated_survivors = sorted(
                        name
                        for name, rival in rivals.items()
                        if all(
                            rival(pair["input"]) == pair["output"]
                            for pair in rotated_demos
                        )
                    )
                    rotation_success = (
                        not rotated_reasons
                        and not rotated_survivors
                        and not schedule_mismatches
                    )
                    if rotation_success:
                        identifiable_rotations += 1
                    else:
                        report["rotation_errors"].append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "query_profile": profiles[query_index],
                                "train_profiles": [
                                    profile
                                    for index, profile in enumerate(profiles)
                                    if index != query_index
                                ],
                                "reasons": rotated_reasons,
                                "surviving_rivals": rotated_survivors,
                                "input_sha256": input_hashes,
                            }
                        )
                    rotation_records.append(
                        {
                            "query_index": query_index,
                            "query_profile": profiles[query_index],
                            "identifiable": rotation_success,
                            "surviving_rivals": rotated_survivors,
                        }
                    )

                window_records.append(
                    {
                        "seed": seed,
                        "start": start,
                        "sample_indices": list(range(start, start + n_demos + 1)),
                        "demo_profiles": profiles[:-1],
                        "query_profile": profiles[-1],
                        "demo_input_sha256": input_hashes[:-1],
                        "query_input_sha256": input_hashes[-1],
                        "identifiable": success,
                        "surviving_rivals": survivors,
                        "rotations": rotation_records,
                    }
                )

        report["bands"][band] = {
            "windows": total_windows,
            "identifiable_windows": identifiable,
            "rotations": total_rotations,
            "identifiable_rotations": identifiable_rotations,
            "profile_counts": dict(sorted(profile_counts.items())),
            "observed_texture_counts": dict(sorted(observed_texture_counts.items())),
            "rival_refuted_windows": dict(sorted(rival_refuted_counts.items())),
            "window_records": window_records,
        }

    report["all_windows_identifiable"] = (
        not report["errors"]
        and not report["rotation_errors"]
        and all(
        band_report["identifiable_windows"] == band_report["windows"]
        and band_report["identifiable_rotations"] == band_report["rotations"]
        and all(
            count == band_report["windows"]
            for count in band_report["rival_refuted_windows"].values()
        )
        for band_report in report["bands"].values()
        )
    )
    return report


def _parse_csv_ints(value: str) -> tuple[int, ...]:
    values = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one integer")
    return values


def _parse_csv_strings(value: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in value.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one value")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=_parse_csv_ints, default=(17, 4242, 424242))
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument(
        "--bands",
        type=_parse_csv_strings,
        default=("easy", "medium", "hard"),
        help="comma-separated subset of easy,medium,hard",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(seeds=args.seeds, starts=args.starts, bands=args.bands)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["all_windows_identifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
