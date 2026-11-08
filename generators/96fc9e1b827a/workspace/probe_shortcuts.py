#!/usr/bin/env python3
"""Replay canonical shortcuts and find production-sampler counterexamples.

The report is intentionally source-bound: it loads the selected generator,
iterates its declared ``CANONICAL_SHORTCUTS``/``LESSON_COMPETITORS``, and embeds
the exact generated grids and outputs needed for later Racket verification.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "96fc9e1b827a"


def _bootstrap_root() -> Path:
    path = Path(__file__).resolve()
    for candidate in (path.parent, *path.parents):
        runtime = candidate / "shared" / "runtime"
        if runtime.is_dir():
            sys.path.insert(0, str(runtime))
            return candidate
        if (candidate / "data" / "canonical" / "puzzles.jsonl").is_file():
            return candidate
    raise FileNotFoundError(f"could not find repository/runtime root from {path}")


_BOOTSTRAP_ROOT = _bootstrap_root()

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    module_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if not (
            exc.name == module_name
            or (exc.name and module_name.startswith(exc.name + "."))
        ):
            raise
    path = find_root(__file__) / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"shortcut_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pairs_for_lesson(gen, *, seed: int, start: int, difficulty: str) -> list[dict[str, Any]]:
    return [
        {
            "input": grid,
            "output": gen.solve_intended(grid),
            "seed": seed,
            "sample_index": start + offset,
            "difficulty": difficulty,
        }
        for offset in range(4)
        for grid in [gen.generate(seed, start + offset, difficulty=difficulty)]
    ]


def build_report(
    *,
    seed: int = 91_337,
    starts: Iterable[int] = range(4),
    difficulties: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    """Return canonical-fit evidence and first emitted witness for every rival."""
    gen = _load_generator()
    root = find_root(__file__)
    generator_path = root / "generators" / TASK_ID / "generator.py"
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    starts = tuple(int(start) for start in starts)
    difficulties = tuple(str(difficulty) for difficulty in difficulties)

    canonical_shortcuts: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = [rival(pair["input"]) == pair["output"] for pair in canonical]
        canonical_shortcuts[name] = {
            "canonical_pair_count": len(canonical),
            "fits_count": sum(matches),
            "fits_each": matches,
        }

    witnesses: dict[str, Any] = {}
    lesson_rotations: list[dict[str, Any]] = []
    for difficulty in difficulties:
        for start in starts:
            pairs = _pairs_for_lesson(gen, seed=seed, start=start, difficulty=difficulty)
            rotation_errors = []
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                rotation_errors.append(
                    {
                        "query_index": query_index,
                        "errors": list(gen.lesson_identifiable(demos, query)),
                    }
                )
            lesson_rotations.append(
                {
                    "seed": seed,
                    "start": start,
                    "difficulty": difficulty,
                    "pair_count": len(pairs),
                    "rotations": rotation_errors,
                }
            )

            for pair in pairs:
                grid = pair["input"]
                intended = pair["output"]
                for name, rival in gen.CANONICAL_SHORTCUTS.items():
                    if name in witnesses:
                        continue
                    rival_output = rival(grid)
                    if rival_output == intended:
                        continue
                    witnesses[name] = {
                        "seed": pair["seed"],
                        "sample_index": pair["sample_index"],
                        "difficulty": pair["difficulty"],
                        "schedule_profile": gen.schedule_profile(
                            pair["seed"], pair["sample_index"], pair["difficulty"]
                        ),
                        "observed_axes": gen.observe_overrides(grid),
                        "input": grid,
                        "intended_output": intended,
                        "rival_output": rival_output,
                        "self_check_errors": list(gen.self_check(grid)),
                    }

    missing = sorted(set(gen.CANONICAL_SHORTCUTS) - set(witnesses))
    if missing:
        raise RuntimeError(
            "production sampler did not emit a disagreement for declared rival(s): "
            + ", ".join(missing)
        )

    return {
        "schema": "arcpuzzles-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _sha256(generator_path),
        "rule_hash": gen.RULE_HASH,
        "seed": seed,
        "starts": list(starts),
        "difficulties": list(difficulties),
        "canonical_shortcuts": canonical_shortcuts,
        "generated_witnesses": witnesses,
        "lesson_rotation_audit": lesson_rotations,
        "all_tested_rotations_identifiable": all(
            not rotation["errors"]
            for lesson in lesson_rotations
            for rotation in lesson["rotations"]
        ),
        "scope_note": (
            "Finite audit of declared rivals over canonical labels and the listed "
            "production schedule windows; not a proof against undeclared rules."
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=91_337)
    parser.add_argument(
        "--starts",
        type=int,
        default=4,
        help="audit lesson starts 0..N-1 (default: 4, covering every schedule residue)",
    )
    parser.add_argument("--out", type=Path, help="write JSON here; stdout when omitted")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.starts <= 0:
        raise SystemExit("--starts must be positive")
    report = build_report(seed=args.seed, starts=range(args.starts))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(rendered)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
