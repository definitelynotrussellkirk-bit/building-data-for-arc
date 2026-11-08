#!/usr/bin/env python3
"""Audit lesson windows against every declared semantic rival.

The generator's ordinary schedule is only useful if each lesson window kills
all known canonical-fitting or otherwise plausible shortcuts.  This tool makes
that claim reproducible and JSON-serializable instead of relying on a few
hand-picked examples.

From the repository root::

    PYTHONPATH=shared/runtime python3 \
      generators/cadfb7a1ae72/workspace/audit_curriculum.py \
      --starts 200 --seed-base 71000 --out /tmp/cadfb-shortcuts.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "cadfb7a1ae72"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"audit_{TASK_ID}_generator", TASK_DIR / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load task generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


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
                pairs.append({"split": split, "input": source, "output": target})
    return pairs


def _generator_sha256() -> str:
    return hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest()


def run_audit(
    *,
    starts: Iterable[int],
    bands: Iterable[str] = ("easy", "medium", "hard"),
    seed_base: int = 71_000,
) -> dict[str, Any]:
    """Return canonical-fit and sliding-window survival evidence.

    A rival *survives* a window only when it exactly reproduces the intended
    matrix for every demonstration in that window.
    """
    starts = tuple(int(value) for value in starts)
    bands = tuple(str(value) for value in bands)
    invalid_bands = sorted(set(bands) - {"easy", "medium", "hard"})
    if invalid_bands:
        raise ValueError(f"invalid bands: {invalid_bands}")
    if not starts:
        raise ValueError("starts must contain at least one sample index")

    canonical = _canonical_pairs()
    canonical_shortcuts = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical)
        for name, rival in GEN.CANONICAL_SHORTCUTS.items()
    }

    rival_stats = {
        name: {
            "surviving_windows": 0,
            "first_survivor": None,
            "first_disagreement": None,
        }
        for name in GEN.SEMANTIC_RIVALS
    }
    profile_counts: dict[str, int] = {name: 0 for name in GEN.PROFILES}
    windows_tested = 0

    for band_index, band in enumerate(bands):
        for start in starts:
            windows_tested += 1
            demonstrations = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                sample_index = start + offset
                seed = seed_base + band_index * 1_000_003 + start * 101 + offset
                grid = GEN.generate(seed, sample_index, difficulty=band)
                intended = GEN.rule_mirror(grid)
                profile = GEN.observe_overrides(grid)["profile"]
                profile_counts[profile] += 1
                demonstrations.append(
                    {
                        "seed": seed,
                        "sample_index": sample_index,
                        "profile": profile,
                        "grid": grid,
                        "intended": intended,
                    }
                )

            for name, rival in GEN.SEMANTIC_RIVALS.items():
                disagreements = []
                for demo in demonstrations:
                    rival_output = rival(demo["grid"])
                    if rival_output != demo["intended"]:
                        disagreements.append(
                            {
                                "seed": demo["seed"],
                                "sample_index": demo["sample_index"],
                                "profile": demo["profile"],
                            }
                        )
                if disagreements:
                    if rival_stats[name]["first_disagreement"] is None:
                        rival_stats[name]["first_disagreement"] = {
                            "band": band,
                            **disagreements[0],
                        }
                else:
                    rival_stats[name]["surviving_windows"] += 1
                    if rival_stats[name]["first_survivor"] is None:
                        rival_stats[name]["first_survivor"] = {
                            "band": band,
                            "start": start,
                            "demonstrations": [
                                {
                                    "seed": demo["seed"],
                                    "sample_index": demo["sample_index"],
                                    "profile": demo["profile"],
                                }
                                for demo in demonstrations
                            ],
                        }

    all_killed = all(
        item["surviving_windows"] == 0
        for item in rival_stats.values()
    )
    all_canonical_fit = all(canonical_shortcuts.values())
    audit_passed = all_killed and all_canonical_fit
    return {
        "task_id": TASK_ID,
        "generator_sha256": _generator_sha256(),
        "examples_needed": GEN.EXAMPLES_NEEDED,
        "bands": list(bands),
        "starts": list(starts),
        "seed_base": seed_base,
        "windows_tested": windows_tested,
        "draws_tested": windows_tested * GEN.EXAMPLES_NEEDED,
        "profile_counts": profile_counts,
        "canonical_pairs": len(canonical),
        "canonical_shortcuts": canonical_shortcuts,
        "all_canonical_shortcuts_fit": all_canonical_fit,
        "rivals": rival_stats,
        "all_declared_rivals_killed": all_killed,
        "audit_passed": audit_passed,
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
    parser.add_argument("--seed-base", type=int, default=71_000)
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
    return 0 if report["audit_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
