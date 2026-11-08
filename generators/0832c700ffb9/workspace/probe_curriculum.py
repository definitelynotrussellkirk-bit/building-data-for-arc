#!/usr/bin/env python3
"""Replayable curriculum audit for generator 0832c700ffb9.

The probe deliberately reads the generator's production declarations instead of
copying rival or witness names.  It checks canonical mirror/shortcut behaviour,
all legal joint overrides, witness-to-rival disagreements, and every single-query
rotation of overlapping six-pair schedule windows.  Labels in this probe come
from the Python ``rule_mirror``; the public Racket battery/census remains the
authority for final evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
RUNTIME = HERE.parents[3] / "shared" / "runtime"
if RUNTIME.is_dir() and str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "0832c700ffb9"
BANDS = (None, "easy", "medium", "hard")


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = Path(path or os.environ.get("GENERATOR_UNDER_TEST", TASK_DIR / "generator.py"))
    spec = importlib.util.spec_from_file_location("probe_generator_0832c700ffb9", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _pair(gen, grid):
    return {"input": deepcopy(grid), "output": gen.rule_mirror(grid)}


def audit(*, per_band: int = 12, generator_path: str | None = None) -> dict[str, Any]:
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    gen = load_generator(generator_path)
    source_path = Path(gen.__file__).resolve()
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()

    pairs = canonical_pairs(TASK_ID, root=find_root(HERE))
    mirror_mismatches = []
    shortcut_failures = []
    for pair in pairs:
        identity = f"v{pair['variant']}:{pair['split']}:{pair['pair_index']}"
        if gen.rule_mirror(pair["input"]) != pair["output"]:
            mirror_mismatches.append(identity)
        for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
            if shortcut(pair["input"]) != pair["output"]:
                shortcut_failures.append({"pair": identity, "shortcut": name})

    override_failures = []
    override_cases = 0
    for band in BANDS:
        for height in range(14, 19):
            for width in range(14, 19):
                for texture in gen.TEXTURES:
                    override_cases += 1
                    requested = {
                        "grid_h": height,
                        "grid_w": width,
                        "texture": texture,
                    }
                    try:
                        grid = gen.generate(
                            8100 + height * 100 + width,
                            override_cases,
                            difficulty=band,
                            **requested,
                        )
                        observed = gen.observe_overrides(grid)
                        errors = gen.self_check(grid)
                    except Exception as exc:  # retained as exact finite failure
                        override_failures.append({
                            "band": band,
                            "requested": requested,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                        continue
                    if observed != requested or errors:
                        override_failures.append({
                            "band": band,
                            "requested": requested,
                            "observed": observed,
                            "self_check": errors,
                        })

    witness_hits = Counter({name: 0 for name in gen.SEMANTIC_WITNESSES})
    witness_rival_failures = []
    profile_counts: dict[str, Counter] = {}
    unique_inputs: set[str] = set()
    ambiguous = []
    rotations_checked = 0
    windows_checked = 0

    for band_index, band in enumerate(BANDS):
        generated = []
        counts = Counter()
        # Five demos plus one query, and enough tail for every requested start.
        for index in range(per_band + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(
                9200 + band_index * 1000 + index,
                index,
                difficulty=band,
            )
            errors = gen.self_check(grid)
            if errors:
                raise AssertionError(f"production draw outside manifold: {band=} {index=} {errors}")
            profile = gen.schedule_profile(9200 + band_index * 1000 + index, index, band)
            counts[str(profile)] += 1
            unique_inputs.add(_grid_hash(grid))
            truth = gen.rule_mirror(grid)
            for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    continue
                witness_hits[witness_name] += 1
                for rival_name in gen.WITNESS_RIVALS[witness_name]:
                    if gen.SEMANTIC_RIVALS[rival_name](grid) == truth:
                        witness_rival_failures.append({
                            "band": band,
                            "index": index,
                            "witness": witness_name,
                            "rival": rival_name,
                            "input_sha256": _grid_hash(grid),
                        })
            generated.append(_pair(gen, grid))
        profile_counts[str(band)] = counts

        window_size = gen.EXAMPLES_NEEDED + 1
        for start in range(per_band):
            window = generated[start:start + window_size]
            windows_checked += 1
            for query_index in range(window_size):
                rotations_checked += 1
                query = window[query_index]
                demos = [pair for index, pair in enumerate(window) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                survivors = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(rival(demo["input"]) == demo["output"] for demo in demos)
                    and rival(query["input"]) != query["output"]
                ]
                if reasons or survivors:
                    ambiguous.append({
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "reasons": reasons,
                        "survivors": survivors,
                        "input_sha256": _grid_hash(query["input"]),
                    })

    return {
        "schema": "0832c700ffb9-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "rule_hash": gen.RULE_HASH,
        "label_basis": "Python rule_mirror; corroborate final claims with public Racket checks",
        "parameters": {"per_band": per_band, "bands": list(BANDS)},
        "canonical": {
            "pairs": len(pairs),
            "mirror_mismatches": mirror_mismatches,
            "shortcut_failures": shortcut_failures,
            "declared_shortcuts": sorted(gen.CANONICAL_SHORTCUTS),
        },
        "joint_overrides": {
            "cases": override_cases,
            "failures": override_failures,
        },
        "profile_counts": {band: dict(counts) for band, counts in profile_counts.items()},
        "witness_hits": dict(witness_hits),
        "witness_rival_failures": witness_rival_failures,
        "lessons": {
            "demonstrations": gen.EXAMPLES_NEEDED,
            "windows_checked": windows_checked,
            "rotations_checked": rotations_checked,
            "ambiguous": ambiguous,
            "unique_inputs": len(unique_inputs),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=12)
    parser.add_argument("--generator", default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = audit(per_band=args.per_band, generator_path=args.generator)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(args.out)
    failed = bool(
        report["canonical"]["mirror_mismatches"]
        or report["canonical"]["shortcut_failures"]
        or report["joint_overrides"]["failures"]
        or report["witness_rival_failures"]
        or report["lessons"]["ambiguous"]
        or not all(report["witness_hits"].values())
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
