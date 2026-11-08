#!/usr/bin/env python3
"""Source-bound lesson and query-rotation probe for ARC task 2243e48c880b.

The probe imports the selected generator by file path, reads its actual
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` declarations, checks every
canonical shortcut against all labeled canonical pairs, then exhaustively holds
out each member of consecutive four-pair curriculum windows.  It uses the
Python rule mirror for a fast authoring check; the packet's public
``lesson-census`` remains the Racket-labelled acceptance evidence.
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

TASK_ID = "2243e48c880b"
BANDS = ("easy", "medium", "hard")
LESSON_SIZE = 4
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
for entry in (REPO / "shared" / "runtime", REPO / "shared"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    source = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_{TASK_ID}", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator source {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_grid(grid):
    return [list(row) for row in grid]


def _pair(module: Any, seed: int, sample_index: int, difficulty: str):
    grid = module.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": module.rule_mirror(grid)}


def audit(*, starts: int, seed: int) -> dict[str, Any]:
    if starts < 1:
        raise ValueError("starts must be positive")
    module, source = _load_generator()
    root = find_root(HERE)
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}) or {})
    hook = getattr(module, "lesson_identifiable", None)
    if not competitors:
        raise RuntimeError("generator declares no LESSON_COMPETITORS")
    if hook is None:
        raise RuntimeError("generator declares no lesson_identifiable hook")

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    shortcut_results: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for name, rival in sorted(shortcuts.items()):
        fits = []
        for pair_index, pair in enumerate(canonical):
            try:
                same = rival(_copy_grid(pair["input"])) == pair["output"]
            except Exception as exc:  # pragma: no cover - reported, not hidden
                same = False
                failures.append(
                    {
                        "kind": "canonical_shortcut_error",
                        "shortcut": name,
                        "pair_index": pair_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            fits.append(bool(same))
        shortcut_results[name] = {
            "pairs": len(canonical),
            "fits": sum(fits),
            "fits_all": bool(fits) and all(fits),
        }
        if not shortcut_results[name]["fits_all"]:
            failures.append(
                {
                    "kind": "declared_canonical_shortcut_does_not_fit",
                    "shortcut": name,
                    "fit_vector": fits,
                }
            )

    counts: Counter[str] = Counter()
    by_band: dict[str, dict[str, Any]] = {}
    all_hashes: set[str] = set()
    for difficulty in BANDS:
        sequence = [
            _pair(module, seed, sample_index, difficulty)
            for sample_index in range(starts + LESSON_SIZE - 1)
        ]
        band_hashes: set[str] = set()
        band_ambiguities = 0
        band_hook_failures = 0
        for pair in sequence:
            digest = hashlib.sha256(
                json.dumps(pair["input"], separators=(",", ":")).encode()
            ).hexdigest()
            band_hashes.add(digest)
            all_hashes.add(digest)
            counts["source_pairs"] += 1
            issues = list(module.self_check(pair["input"]))
            if issues:
                failures.append(
                    {
                        "kind": "self_check_failure",
                        "difficulty": difficulty,
                        "issues": issues,
                        "input": pair["input"],
                    }
                )

        for start in range(starts):
            window = sequence[start : start + LESSON_SIZE]
            counts["lessons"] += 1
            for query_offset in range(LESSON_SIZE):
                counts["rotations"] += 1
                query = window[query_offset]
                demos = [pair for i, pair in enumerate(window) if i != query_offset]
                reasons = list(hook(demos, query) or [])
                if reasons:
                    counts["hook_failures"] += 1
                    band_hook_failures += 1
                    failures.append(
                        {
                            "kind": "lesson_hook_failure",
                            "difficulty": difficulty,
                            "start": start,
                            "query_offset": query_offset,
                            "reasons": reasons,
                        }
                    )
                for rival_name, rival in sorted(competitors.items()):
                    counts["rival_rotation_checks"] += 1
                    fits_demos = all(
                        rival(pair["input"]) == pair["output"] for pair in demos
                    )
                    if fits_demos:
                        counts["rival_demo_survivals"] += 1
                        query_differs = rival(query["input"]) != query["output"]
                        if query_differs:
                            counts["ambiguous_rotations"] += 1
                            band_ambiguities += 1
                            failures.append(
                                {
                                    "kind": "rival_ambiguity",
                                    "difficulty": difficulty,
                                    "start": start,
                                    "query_offset": query_offset,
                                    "rival": rival_name,
                                    "demos": demos,
                                    "query": query,
                                    "rival_query_output": rival(query["input"]),
                                }
                            )
                        else:
                            counts["rival_full_lesson_agreements"] += 1

        by_band[difficulty] = {
            "source_pairs": len(sequence),
            "unique_inputs": len(band_hashes),
            "lessons": starts,
            "rotations": starts * LESSON_SIZE,
            "ambiguous_rotations": band_ambiguities,
            "hook_failures": band_hook_failures,
        }

    for key in (
        "hook_failures",
        "ambiguous_rotations",
        "rival_demo_survivals",
        "rival_full_lesson_agreements",
    ):
        counts.setdefault(key, 0)
    counts["unique_inputs"] = len(all_hashes)
    return {
        "schema": "2243e48c880b-source-bound-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": _sha256(source),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "parameters": {
            "starts_per_band": starts,
            "seed": seed,
            "lesson_size": LESSON_SIZE,
            "query_policy": "every pair held out once",
            "difficulties": list(BANDS),
        },
        "declared_competitors": sorted(competitors),
        "canonical_shortcuts": shortcut_results,
        "counts": dict(counts),
        "by_band": by_band,
        "failures": failures,
        "passed": not failures,
        "limitations": [
            "finite check against declared rivals only",
            "uses rule_mirror labels; retain the public Racket-backed lesson census separately",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=24)
    parser.add_argument("--seed", type=int, default=2243001)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(starts=args.starts, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "lessons": report["counts"]["lessons"],
                "rotations": report["counts"]["rotations"],
                "ambiguous_rotations": report["counts"]["ambiguous_rotations"],
                "generator_sha256": report["generator_sha256"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
