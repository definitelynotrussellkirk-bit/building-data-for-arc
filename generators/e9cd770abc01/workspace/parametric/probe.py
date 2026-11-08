#!/usr/bin/env python3
"""Bounded deterministic self-review for the e9cd770abc01 parametric family.

This probe deliberately does not execute Racket; the native authoring preflight
independently replays every retained label.  Its job is to pressure-test the
sampler, teaching certificate, count independence, matched setting inputs and
large-canvas content before the source inventory is built.
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
PROTOTYPE = HERE / "prototype.py"
SETTINGS = ("nearest_only", "nearest_size_class")
DEMO_COUNTS = (2, 3, 4, 5, 6)
DEFAULT_SEEDS = (0, 1, 2, 9, 17, 23, 100)


def load_prototype():
    spec = importlib.util.spec_from_file_location("_e9cd770abc01_probe_prototype", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adjacent prototype")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(episode: dict[str, Any], split: str) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode[split]]


def _content_quadrants(grid: list[list[int]]) -> list[int]:
    h, w = len(grid), len(grid[0])
    cuts_r = (0, h // 2, h)
    cuts_c = (0, w // 2, w)
    return [
        sum(
            grid[r][c] != 0
            for r in range(cuts_r[ri], cuts_r[ri + 1])
            for c in range(cuts_c[ci], cuts_c[ci + 1])
        )
        for ri in range(2)
        for ci in range(2)
    ]


def build_study(prototype=None, *, seeds: list[int] | tuple[int, ...] = DEFAULT_SEEDS) -> dict[str, Any]:
    p = prototype or load_prototype()
    failures: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    matched_inputs = True
    prefix_stable = True
    all_rivals_rejected = True
    max_shape = [0, 0]
    by_key: dict[tuple[int, int], dict[str, Any]] = {}
    shadow_selector_disagreements: list[dict[str, Any]] = []

    for seed in seeds:
        for demos in DEMO_COUNTS:
            episodes: dict[str, dict[str, Any]] = {}
            for scope in SETTINGS:
                try:
                    settings = {"paint_scope": scope}
                    episode = p.generate(seed, settings, demos, 4)
                    prefix = p.generate(seed, settings, demos, 1)
                    report = p.teaching_report(episode["train"], settings)
                    stable = prefix["train"] == episode["train"] and prefix["test"] == episode["test"][:1]
                    rejected = (
                        report["setting_survivors"] == [scope]
                        and report["plausible_rival_survivors"] == []
                    )
                    prefix_stable = prefix_stable and stable
                    all_rivals_rejected = all_rivals_rejected and rejected
                    episodes[scope] = episode
                    query_shapes = [[len(x["input"]), len(x["input"][0])] for x in episode["test"]]
                    for shape in query_shapes:
                        if shape[0] * shape[1] > max_shape[0] * max_shape[1]:
                            max_shape = shape
                    demo_equivalent_shadows: list[str] = []
                    shadow_query_disagreements: dict[str, list[int]] = {}
                    for selector in p.SHADOW_SELECTORS:
                        if all(
                            p.apply_rival(pair["input"], selector, scope) == pair["output"]
                            for pair in episode["train"]
                        ):
                            demo_equivalent_shadows.append(selector)
                            changed = [
                                index
                                for index, pair in enumerate(episode["test"])
                                if p.apply_rival(pair["input"], selector, scope) != pair["output"]
                            ]
                            if changed:
                                shadow_query_disagreements[selector] = changed
                                shadow_selector_disagreements.append(
                                    {
                                        "seed": seed,
                                        "paint_scope": scope,
                                        "demos": demos,
                                        "selector": selector,
                                        "changed_query_indices": changed,
                                    }
                                )
                    rows.append(
                        {
                            "seed": seed,
                            "paint_scope": scope,
                            "demos": demos,
                            "queries": 4,
                            "query_shapes": query_shapes,
                            "large_query_quadrant_nonzero": _content_quadrants(episode["test"][-1]["input"]),
                            "setting_survivors": report["setting_survivors"],
                            "plausible_rival_survivors": report["plausible_rival_survivors"],
                            "query_prefix_stable": stable,
                            "demo_equivalent_shadow_selectors": demo_equivalent_shadows,
                            "shadow_query_disagreements": shadow_query_disagreements,
                            "status": "passed" if stable and rejected and not shadow_query_disagreements else "failed",
                        }
                    )
                except Exception as exc:  # report bounded failures instead of hiding them
                    failures.append(
                        {
                            "seed": seed,
                            "paint_scope": scope,
                            "demos": demos,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )
            if set(episodes) == set(SETTINGS):
                same = all(
                    _inputs(episodes[SETTINGS[0]], split) == _inputs(episodes[SETTINGS[1]], split)
                    for split in ("train", "test")
                )
                by_key[(seed, demos)] = {"matched_inputs": same}
                matched_inputs = matched_inputs and same

    successes = sum(row["status"] == "passed" for row in rows)
    return {
        "schema": "e9cd770abc01-parametric-self-review-v1",
        "scope": "Bounded Python sampler/teaching review; native preflight supplies protected-Racket execution.",
        "settings": list(SETTINGS),
        "seeds": list(seeds),
        "demo_counts": list(DEMO_COUNTS),
        "queries_per_job": 4,
        "jobs": len(seeds) * len(SETTINGS) * len(DEMO_COUNTS),
        "successes": successes,
        "failures": failures,
        "matched_inputs_across_settings": matched_inputs,
        "query_prefix_stable": prefix_stable,
        "all_declared_rivals_rejected": all_rivals_rejected,
        "declared_rival_count": len(p.RIVALS),
        "shadow_selector_count": len(p.SHADOW_SELECTORS),
        "shadow_selector_query_safe": not shadow_selector_disagreements,
        "shadow_selector_disagreements": shadow_selector_disagreements,
        "max_query_shape": max_shape,
        "source_sha256": {
            name: _sha256(HERE / name)
            for name in ("prototype.py", "adapter.py", "promotion.json", "canonical.rkt", "size_class.rkt")
        },
        "rows": rows,
        "limits": [
            "Finite rival bank and seven deterministic audit seeds by default; not a universal uniqueness proof.",
            "Shadow selectors are retained only when demo-equivalent and are required to agree on every generated query.",
            "Python labels are claims here; protected Racket execution is delegated to review_base_preflight.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = build_study(seeds=args.seeds or DEFAULT_SEEDS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("jobs", "successes", "failures", "max_query_shape")}, sort_keys=True))
    return 0 if not failures_from(report) else 1


def failures_from(report: dict[str, Any]) -> list[Any]:
    if report["failures"]:
        return list(report["failures"])
    if report["successes"] != report["jobs"]:
        return ["not every bounded job passed"]
    if not report["matched_inputs_across_settings"]:
        return ["settings changed sampled inputs"]
    if not report["query_prefix_stable"]:
        return ["query prefix changed with requested count"]
    if not report["all_declared_rivals_rejected"]:
        return ["a declared rival survived"]
    if not report["shadow_selector_query_safe"]:
        return ["a demo-equivalent shadow selector changes a query"]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
