#!/usr/bin/env python3
"""Source-bound diagnostics for the 95f849a2fe0f teaching schedule.

This probe is intentionally independent of the shared lesson census. It checks
all cyclic starts and every query rotation for the small deterministic schedule,
then samples the production distribution for basic diversity and witness counts.
It never supplies labels; labels come from the task-local mirror only for this
post-repair diagnostic, while the Racket authority remains the production oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "95f849a2fe0f"


def _bootstrap() -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
        if (ancestor / "reviewer_support.py").is_file():
            sys.path.insert(0, str(ancestor))
            break
    from reviewer_support import find_root  # type: ignore

    return find_root(__file__)


def _load_generator(root: Path):
    candidates = (
        Path(__file__).resolve().parents[1] / "generator.py",
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise FileNotFoundError("could not locate selected generator")
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def _pair(gen, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def build_report(per_band: int) -> dict:
    if per_band < 1:
        raise ValueError("--per-band must be positive")

    root = _bootstrap()
    from reviewer_support import canonical_pairs  # type: ignore

    gen, generator_path = _load_generator(root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    shortcut_fits = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }

    ambiguous = []
    rotations_checked = 0
    period = len(gen.DEFAULT_SCHEDULE)
    for band in ("easy", "medium", "hard"):
        for start in range(period):
            lesson = [
                _pair(gen, gen.generate(730_000 + start, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index in range(4):
                query = lesson[query_index]
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                rotations_checked += 1
                if reasons:
                    ambiguous.append({
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "reasons": reasons,
                    })

    sampling = {}
    sampling_errors = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        inputs = set()
        outputs = set()
        profiles = {}
        witnesses = 0
        for sample_index in range(per_band):
            grid = gen.generate(
                910_000 + band_index * 10_000 + sample_index,
                sample_index,
                difficulty=band,
            )
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                sampling_errors.append({
                    "band": band,
                    "sample_index": sample_index,
                    "errors": errors,
                })
            profile = gen.observe_overrides(grid)["scene_profile"]
            profiles[profile] = profiles.get(profile, 0) + 1
            output = gen.rule_mirror(grid)
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, output)))
            witnesses += int(output != gen.recrop_xor_rival(grid))
        sampling[band] = {
            "draws": per_band,
            "unique_inputs": len(inputs),
            "unique_outputs": len(outputs),
            "witnesses": witnesses,
            "profiles": dict(sorted(profiles.items())),
        }

    problems = []
    if len(canonical) != 3:
        problems.append(f"expected 3 canonical pairs, found {len(canonical)}")
    if not shortcut_fits or not all(shortcut_fits.values()):
        problems.append("a declared canonical shortcut does not fit every canonical pair")
    if ambiguous:
        problems.append(f"{len(ambiguous)} cyclic query rotations remain ambiguous")
    if sampling_errors:
        problems.append(f"{len(sampling_errors)} sampled inputs failed self_check")

    return {
        "schema": "95f849a2fe0f-lesson-probe/1",
        "status": "ok" if not problems else "failed",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "canonical": {
            "pairs": len(canonical),
            "shortcut_fits": shortcut_fits,
        },
        "pair_pool_sizes": {
            profile: len(pairs) for profile, pairs in sorted(gen._PAIR_POOLS.items())
        },
        "schedule": {
            "profiles": list(gen.DEFAULT_SCHEDULE),
            "demonstrations": gen.EXAMPLES_NEEDED,
            "lesson_pairs": gen.EXAMPLES_NEEDED + 1,
            "cyclic_starts": period,
            "rotations_checked": rotations_checked,
            "ambiguous_rotations": len(ambiguous),
            "ambiguities": ambiguous,
        },
        "sampling": sampling,
        "sampling_errors": sampling_errors,
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(args.per_band)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
