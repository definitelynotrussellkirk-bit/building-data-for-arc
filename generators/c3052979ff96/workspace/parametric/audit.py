#!/usr/bin/env python3
"""Bounded deterministic audit for the c3052979ff96 relay family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SETTINGS = ("rotation_only", "relay_hit_color")
DEMO_COUNTS = (2, 3, 6)


def _load_adapter():
    source = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location(
        "_c3052979ff96_parametric_adapter_audit", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adapter from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _visible_inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def build_report(seeds: int = 16) -> dict[str, Any]:
    if type(seeds) is not int or not 1 <= seeds <= 256:
        raise ValueError("seeds must be an exact integer in 1..256")
    adapter = _load_adapter()
    failures: list[dict[str, Any]] = []
    episodes = 0
    neutral_checks = 0
    survivor_checks = 0
    stress_checks = 0
    query_codes: set[int] = set()
    query_colors: set[int] = set()
    demo_color_pairs: set[tuple[int, int]] = set()

    for seed in range(seeds):
        for demos in DEMO_COUNTS:
            generated = {
                mode: adapter.generate(seed, {"rule_mode": mode}, demos, 4)
                for mode in SETTINGS
            }
            neutral_checks += 1
            canonical_inputs = _visible_inputs(generated["rotation_only"])
            relay_inputs = _visible_inputs(generated["relay_hit_color"])
            if canonical_inputs != relay_inputs:
                failures.append(
                    {"seed": seed, "demos": demos, "check": "setting_neutral_inputs"}
                )
            serialized = [json.dumps(value, separators=(",", ":")) for value in canonical_inputs]
            if len(serialized) != len(set(serialized)):
                failures.append(
                    {"seed": seed, "demos": demos, "check": "distinct_inputs"}
                )

            first_two = [adapter.observe(pair["input"]) for pair in generated["relay_hit_color"]["train"][:2]]
            demo_color_pairs.add(
                (first_two[0]["relay_color"], first_two[1]["relay_color"])
            )
            if [item["code"] for item in first_two] != [1, 1]:
                failures.append(
                    {"seed": seed, "demos": demos, "check": "paired_demo_codes"}
                )
            if first_two[0]["relay_color"] == first_two[1]["relay_color"]:
                failures.append(
                    {"seed": seed, "demos": demos, "check": "paired_demo_colors"}
                )

            for mode in SETTINGS:
                episode = generated[mode]
                episodes += 1
                proof = adapter.certificate(
                    episode["train"], [pair["input"] for pair in episode["test"]]
                )
                survivor_checks += 1
                if proof["survivors"] != [mode]:
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "check": "unique_survivor",
                            "survivors": proof["survivors"],
                        }
                    )
                observed_queries = [adapter.observe(pair["input"]) for pair in episode["test"]]
                query_codes.update(item["code"] for item in observed_queries)
                query_colors.update(item["relay_color"] for item in observed_queries)
                stress_checks += 1
                stress = episode["test"][-1]
                grid = stress["input"]
                occupied = [
                    (row, col)
                    for row, values in enumerate(grid)
                    for col, cell in enumerate(values)
                    if cell != 0
                ]
                if (
                    (len(grid), len(grid[0])) != (30, 30)
                    or min(row for row, _ in occupied) != 0
                    or max(row for row, _ in occupied) != 29
                    or min(col for _, col in occupied) != 0
                    or max(col for _, col in occupied) != 29
                    or len(occupied) < 35
                ):
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "check": "30x30_stress",
                        }
                    )

    return {
        "schema": "c3052979ff96-parametric-audit-v1",
        "status": "passed" if not failures else "failed",
        "settings": list(SETTINGS),
        "demo_counts": list(DEMO_COUNTS),
        "seed_count": seeds,
        "episodes": episodes,
        "setting_neutral_input_checks": neutral_checks,
        "unique_survivor_checks": survivor_checks,
        "query_30x30_checks": stress_checks,
        "query_codes": sorted(query_codes),
        "query_relay_colors": sorted(query_colors),
        "first_two_demo_color_pairs": [list(pair) for pair in sorted(demo_color_pairs)],
        "declared_hypotheses": list(adapter.HYPOTHESES),
        "source_sha256": {
            "adapter.py": _sha256(HERE / "adapter.py"),
            "relay_hit_color.rkt": _sha256(HERE / "relay_hit_color.rkt"),
            "promotion.json": _sha256(HERE / "promotion.json"),
        },
        "failures": failures,
        "scope": (
            "Finite audit over seeds 0..seed_count-1, demo counts 2/3/6, both "
            "settings and the adapter's declared executable rivals. Protected "
            "Racket parity is covered separately by focused tests and native qualification."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = build_report(args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out is None:
        print(text, end="")
    else:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
        print(args.json_out)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
