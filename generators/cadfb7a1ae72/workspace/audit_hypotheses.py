#!/usr/bin/env python3
"""Enumerate and audit composed rule shortcuts for ``cadfb7a1ae72``.

The ordinary semantic-rival registry changes one assumption at a time.  This
companion auditor crosses the assumptions that the official examples leave
ambiguous: symmetry representation, hole representation, object order, and
relation precedence.  It first keeps only hypotheses that fit every official
pair, then asks whether any non-authority hypothesis survives a sliding
four-example generated lesson window.

From the repository root::

    PYTHONPATH=shared/runtime python3 \
      generators/cadfb7a1ae72/workspace/audit_hypotheses.py \
      --starts 200 --out /tmp/cadfb-hypotheses.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

TASK_ID = "cadfb7a1ae72"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"hypothesis_{TASK_ID}_generator", TASK_DIR / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load task generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
AUTHORITY = {
    "symmetry": "exact",
    "holes": "regions",
    "order": "top_left",
    "precedence": "symmetry_first",
}


def _canonical_pairs() -> list[dict[str, Any]]:
    ledger = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    pairs: list[dict[str, Any]] = []
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for split in ("train", "test"):
            values = row.get(split) or []
            if isinstance(values, dict):
                values = [values]
            for pair in values:
                if not isinstance(pair, dict) or not pair.get("input") or not pair.get("output"):
                    continue
                source = pair["input"]
                target = pair["output"]
                if source and isinstance(source[0], str):
                    source = [[int(char) for char in text] for text in source]
                if target and isinstance(target[0], str):
                    target = [[int(char) for char in text] for text in target]
                pairs.append({"input": source, "output": target})
    return pairs


def _axis_count(obj: dict[str, Any]) -> int:
    value = obj["symmetry_class"]
    return int(bool(value & 1)) + int(bool(value & 2))


def _projection_symmetry(obj: dict[str, Any]) -> int:
    return GEN._projection_symmetry_class(obj["normalized_cells"])


def _binary_holes(obj: dict[str, Any]) -> bool:
    return bool(obj["holes"])


def _enclosed_cells(obj: dict[str, Any]) -> int:
    return GEN._enclosed_zero_cell_count(obj["normalized_cells"])


SYMMETRY_FEATURES: dict[str, Callable[[dict[str, Any]], Any]] = {
    "exact": lambda obj: obj["symmetry_class"],
    "axis_count": _axis_count,
    "projection": _projection_symmetry,
}
HOLE_FEATURES: dict[str, Callable[[dict[str, Any]], Any]] = {
    "regions": lambda obj: obj["holes"],
    "binary": _binary_holes,
    "enclosed_cells": _enclosed_cells,
}
ORDERS = ("top_left", "ascending_color")
PRECEDENCES = ("symmetry_first", "holes_first")


def enumerate_hypotheses() -> list[dict[str, str]]:
    return [
        {
            "symmetry": symmetry,
            "holes": holes,
            "order": order,
            "precedence": precedence,
        }
        for symmetry, holes, order, precedence in itertools.product(
            SYMMETRY_FEATURES,
            HOLE_FEATURES,
            ORDERS,
            PRECEDENCES,
        )
    ]


def _ordered_objects(
    objects: list[dict[str, Any]],
    order: str,
) -> list[dict[str, Any]]:
    if order == "top_left":
        return list(objects)
    if order == "ascending_color":
        return sorted(objects, key=lambda obj: obj["color"])
    raise ValueError(f"unknown order {order!r}")


def _apply_to_objects(
    source_objects: list[dict[str, Any]],
    hypothesis: dict[str, str],
) -> list[list[int]]:
    objects = _ordered_objects(source_objects, hypothesis["order"])
    symmetry = SYMMETRY_FEATURES[hypothesis["symmetry"]]
    holes = HOLE_FEATURES[hypothesis["holes"]]
    symmetry_first = hypothesis["precedence"] == "symmetry_first"

    result: list[list[int]] = []
    for row_index, left in enumerate(objects):
        row: list[int] = []
        for col_index, right in enumerate(objects):
            if row_index == col_index:
                value = 1
            else:
                same_symmetry = symmetry(left) == symmetry(right)
                same_holes = holes(left) == holes(right)
                if symmetry_first:
                    value = 8 if same_symmetry else 4 if same_holes else 0
                else:
                    value = 4 if same_holes else 8 if same_symmetry else 0
            row.append(value)
        result.append(row)
    return result


def apply_hypothesis(
    grid: list[list[int]],
    hypothesis: dict[str, str],
) -> list[list[int]]:
    analysis = GEN._analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task input: " + "; ".join(analysis["errors"]))
    return _apply_to_objects(analysis["objects"], hypothesis)


def _generator_sha256() -> str:
    return hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest()


def _is_authority(hypothesis: dict[str, str]) -> bool:
    return hypothesis == AUTHORITY


def run_audit(
    *,
    starts: Iterable[int],
    bands: Iterable[str] = ("easy", "medium", "hard"),
    seed_base: int = 91_000,
) -> dict[str, Any]:
    starts = tuple(int(value) for value in starts)
    bands = tuple(str(value) for value in bands)
    invalid_bands = sorted(set(bands) - {"easy", "medium", "hard"})
    if invalid_bands:
        raise ValueError(f"invalid bands: {invalid_bands}")
    if not starts:
        raise ValueError("starts must contain at least one sample index")

    hypotheses = enumerate_hypotheses()
    canonical = _canonical_pairs()
    canonical_fit = [
        hypothesis
        for hypothesis in hypotheses
        if all(
            apply_hypothesis(pair["input"], hypothesis) == pair["output"]
            for pair in canonical
        )
    ]
    alternatives = [hypothesis for hypothesis in canonical_fit if not _is_authority(hypothesis)]
    stats = [
        {
            "hypothesis": hypothesis,
            "surviving_windows": 0,
            "first_survivor": None,
            "first_disagreement": None,
        }
        for hypothesis in alternatives
    ]

    windows_tested = 0
    for band_index, band in enumerate(bands):
        for start in starts:
            windows_tested += 1
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                sample_index = start + offset
                seed = seed_base + band_index * 1_000_003 + start * 101 + offset
                grid = GEN.generate(seed, sample_index, difficulty=band)
                demos.append(
                    {
                        "seed": seed,
                        "sample_index": sample_index,
                        "profile": GEN.observe_overrides(grid)["profile"],
                        "objects": GEN._analyze(grid)["objects"],
                        "output": GEN.rule_mirror(grid),
                    }
                )

            for item in stats:
                hypothesis = item["hypothesis"]
                disagreements = [
                    demo
                    for demo in demos
                    if _apply_to_objects(demo["objects"], hypothesis) != demo["output"]
                ]
                if disagreements:
                    if item["first_disagreement"] is None:
                        first = disagreements[0]
                        item["first_disagreement"] = {
                            "band": band,
                            "seed": first["seed"],
                            "sample_index": first["sample_index"],
                            "profile": first["profile"],
                        }
                else:
                    item["surviving_windows"] += 1
                    if item["first_survivor"] is None:
                        item["first_survivor"] = {
                            "band": band,
                            "start": start,
                            "demonstrations": [
                                {
                                    "seed": demo["seed"],
                                    "sample_index": demo["sample_index"],
                                    "profile": demo["profile"],
                                }
                                for demo in demos
                            ],
                        }

    surviving = [
        item["hypothesis"]
        for item in stats
        if item["surviving_windows"] > 0
    ]
    return {
        "task_id": TASK_ID,
        "generator_sha256": _generator_sha256(),
        "authority": dict(AUTHORITY),
        "feature_families": {
            "symmetry": list(SYMMETRY_FEATURES),
            "holes": list(HOLE_FEATURES),
            "order": list(ORDERS),
            "precedence": list(PRECEDENCES),
        },
        "hypotheses_enumerated": len(hypotheses),
        "canonical_pairs": len(canonical),
        "canonical_fit_hypotheses": len(canonical_fit),
        "non_authority_canonical_fit_hypotheses": len(alternatives),
        "canonical_fit": canonical_fit,
        "bands": list(bands),
        "starts": list(starts),
        "seed_base": seed_base,
        "windows_tested": windows_tested,
        "draws_tested": windows_tested * GEN.EXAMPLES_NEEDED,
        "hypothesis_stats": stats,
        "surviving_hypotheses": surviving,
        "all_non_authority_hypotheses_killed": not surviving,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--starts",
        type=int,
        default=200,
        metavar="N",
        help="audit sliding windows starting at indices 0..N-1 (default: 200)",
    )
    parser.add_argument("--seed-base", type=int, default=91_000)
    parser.add_argument(
        "--bands",
        nargs="+",
        choices=("easy", "medium", "hard"),
        default=("easy", "medium", "hard"),
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.starts < 1:
        parser.error("--starts must be at least 1")

    report = run_audit(
        starts=range(args.starts),
        bands=args.bands,
        seed_base=args.seed_base,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["all_non_authority_hypotheses_killed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
