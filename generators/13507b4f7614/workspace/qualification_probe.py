#!/usr/bin/env python3
"""Source-bound qualification probe for ARC generator 13507b4f7614.

This task-local helper complements the shared battery. It verifies every
canonical-fitting shortcut declared by the generator, exact realization of all
public grid-profile overrides, every cyclic lesson start and query rotation,
and per-band structural/witness coverage. It is finite evidence against the
declared rivals, not a proof that no other rule can fit the lessons.

Run from the repository root::

    python3 generators/13507b4f7614/workspace/qualification_probe.py \
        --per-band 100 --out ../checks/qualification-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "13507b4f7614"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs  # noqa: E402

BANDS = ("easy", "medium", "hard")


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"qualification_{TASK_ID}_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed(label: str) -> int:
    digest = hashlib.sha256(f"qualification:v1:{TASK_ID}:{label}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _pair(generator, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def qualify(
    *,
    per_band: int = 100,
    generator_path: Path | str | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable source-bound qualification report."""
    if type(per_band) is not int or per_band < 4:
        raise ValueError("per_band must be an integer >= 4")
    source = Path(generator_path) if generator_path is not None else TASK_HOME / "generator.py"
    source = source.resolve()
    generator = _load_generator(source)
    canonical = canonical_pairs(TASK_ID, root=REPO_ROOT)
    errors: list[dict[str, Any]] = []

    shortcut_rows: dict[str, dict[str, Any]] = {}
    for name, shortcut in sorted(dict(generator.CANONICAL_SHORTCUTS).items()):
        matches = sum(
            shortcut(deepcopy(pair["input"])) == pair["output"]
            for pair in canonical
        )
        row = {
            "matches": matches,
            "pairs": len(canonical),
            "fits_all": bool(canonical) and matches == len(canonical),
        }
        shortcut_rows[name] = row
        if not row["fits_all"]:
            errors.append({"kind": "canonical_shortcut", "name": name, **row})

    exact_failures: list[dict[str, Any]] = []
    exact_cases = 0
    for band_index, band in enumerate(BANDS):
        for profile_index, profile in enumerate(generator.GRID_PROFILES):
            exact_cases += 1
            seed = _seed(f"override:{band}:{profile}")
            sample_index = band_index * 100 + profile_index
            try:
                grid = generator.generate(
                    seed,
                    sample_index,
                    difficulty=band,
                    grid_profile=profile,
                )
                observed = generator.observe_overrides(grid)
                findings = generator.self_check(
                    grid,
                    difficulty=band,
                    meta={"overrides": {"grid_profile": profile}},
                )
            except Exception as exc:  # pragma: no cover - diagnostic path
                exact_failures.append(
                    {"band": band, "profile": profile, "error": repr(exc)}
                )
            else:
                if observed != {"grid_profile": profile} or findings:
                    exact_failures.append(
                        {
                            "band": band,
                            "profile": profile,
                            "observed": observed,
                            "self_check": findings,
                        }
                    )
    errors.extend({"kind": "exact_override", **row} for row in exact_failures)

    period = len(generator.SCHEDULE_PROFILES)
    window_size = int(generator.EXAMPLES_NEEDED) + 1
    rotation_failures: list[dict[str, Any]] = []
    rotations_checked = 0
    competitors = dict(generator.LESSON_COMPETITORS)
    for band in BANDS:
        for start in range(period):
            seed = _seed(f"rotation:{band}:{start}")
            lesson = [
                _pair(
                    generator,
                    generator.generate(
                        seed,
                        start + offset,
                        difficulty=band,
                    ),
                )
                for offset in range(window_size)
            ]
            for query_index, query in enumerate(lesson):
                rotations_checked += 1
                demos = [
                    pair for index, pair in enumerate(lesson) if index != query_index
                ]
                reasons = list(generator.lesson_identifiable(demos, query))
                surviving = [
                    name
                    for name, rival in sorted(competitors.items())
                    if all(
                        rival(deepcopy(pair["input"])) == pair["output"]
                        for pair in demos
                    )
                ]
                if reasons or surviving:
                    rotation_failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "hook_reasons": reasons,
                            "surviving_competitors": surviving,
                        }
                    )
    errors.extend({"kind": "rotation", **row} for row in rotation_failures)

    band_rows: dict[str, dict[str, Any]] = {}
    for band in BANDS:
        scene_counts: Counter[str] = Counter()
        profile_counts: Counter[str] = Counter()
        witness_hits: Counter[str] = Counter()
        self_check_failures: list[dict[str, Any]] = []
        replay_failures: list[dict[str, Any]] = []
        grid_keys: set[str] = set()
        for index in range(per_band):
            seed = _seed(f"sample:{band}:{index}")
            grid = generator.generate(seed, index, difficulty=band)
            replay = generator.generate(seed, index, difficulty=band)
            if grid != replay or grid is replay:
                replay_failures.append(
                    {"index": index, "equal": grid == replay, "same_object": grid is replay}
                )
            findings = generator.self_check(grid, difficulty=band)
            if findings:
                self_check_failures.append({"index": index, "findings": findings})
            scene_counts[generator.schedule_profile(seed, index, difficulty=band)] += 1
            profile_counts[generator.observe_overrides(grid)["grid_profile"]] += 1
            for name, predicate in sorted(generator.SEMANTIC_WITNESSES.items()):
                if predicate(grid):
                    witness_hits[name] += 1
            grid_keys.add(_grid_key(grid))

        row = {
            "samples": per_band,
            "unique_inputs": len(grid_keys),
            "scene_counts": dict(sorted(scene_counts.items())),
            "grid_profile_counts": dict(sorted(profile_counts.items())),
            "witness_hits": dict(sorted(witness_hits.items())),
            "self_check_failures": self_check_failures,
            "replay_failures": replay_failures,
        }
        band_rows[band] = row
        if self_check_failures:
            errors.append(
                {"kind": "band_self_check", "band": band, "failures": self_check_failures}
            )
        if replay_failures:
            errors.append(
                {"kind": "determinism", "band": band, "failures": replay_failures}
            )
        missing_scenes = sorted(set(generator.SCHEDULE_PROFILES) - set(scene_counts))
        if missing_scenes:
            errors.append(
                {"kind": "scene_coverage", "band": band, "missing": missing_scenes}
            )
        for name in generator.SEMANTIC_WITNESSES:
            if witness_hits[name] == 0:
                errors.append(
                    {"kind": "witness_coverage", "band": band, "witness": name}
                )

    return {
        "schema": "arc-generator-task-local-qualification-v1",
        "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "per_band": per_band,
        "limitations": (
            "Finite Python-mirror evidence against the generator's declared rivals; "
            "use the shared Racket battery and lesson census for authority-labelled evidence."
        ),
        "canonical_shortcuts": shortcut_rows,
        "exact_overrides": {"checked": exact_cases, "failures": exact_failures},
        "rotations": {
            "period": period,
            "window_size": window_size,
            "checked": rotations_checked,
            "failures": rotation_failures,
        },
        "bands": band_rows,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--generator", type=Path, default=TASK_HOME / "generator.py")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")
    report = qualify(per_band=args.per_band, generator_path=args.generator)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "generator_sha256": report["generator_sha256"],
                "errors": len(report["errors"]),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
