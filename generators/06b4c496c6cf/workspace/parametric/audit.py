#!/usr/bin/env python3
"""Bounded deterministic self-audit for the template-width parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
ADAPTER_PATH = HERE / "adapter.py"


def _load_adapter():
    body = ADAPTER_PATH.read_bytes()
    name = "_06b4c496c6cf_audit_adapter_" + hashlib.sha256(body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {ADAPTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _input_bytes(episode: dict) -> list[str]:
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in episode["train"] + episode["test"]
    ]


def audit(*, seeds: Iterable[int] = range(16), demo_counts: Iterable[int] = range(2, 7)) -> dict:
    adapter = _load_adapter()
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    findings: list[dict] = []
    episodes = 0
    pairs = 0
    widths: set[int] = set()
    target_colors: set[int] = set()
    sizes: set[tuple[int, int]] = set()

    for seed in seeds:
        for demos in demo_counts:
            by_setting = []
            for settings in adapter.SETTINGS:
                label = settings["marker_selection"]
                try:
                    episode = adapter.generate(seed, settings, demos, 4)
                    episodes += 1
                    pairs += demos + 4
                    inputs = _input_bytes(episode)
                    by_setting.append(inputs)
                    if len(inputs) != len(set(inputs)):
                        findings.append({
                            "seed": seed, "demos": demos, "setting": label,
                            "code": "duplicate_input",
                        })
                    report = adapter.lesson_report(episode, settings)
                    if report["surviving_rivals"] or report["query_disagreements"]:
                        findings.append({
                            "seed": seed, "demos": demos, "setting": label,
                            "code": "teaching_hole", "report": report,
                        })
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            if pair["output"] != adapter.solve(pair["input"], settings):
                                findings.append({
                                    "seed": seed, "demos": demos, "setting": label,
                                    "code": "claim_mismatch", "split": split, "index": index,
                                })
                            facts = adapter.analyze(pair["input"])
                            widths.add(facts["template_width"])
                            target_colors.add(facts["target_color"])
                            sizes.add((facts["height"], facts["width"]))
                    largest = episode["test"][3]["input"]
                    if (len(largest), len(largest[0])) != (30, 30):
                        findings.append({
                            "seed": seed, "demos": demos, "setting": label,
                            "code": "missing_30x30_query",
                        })
                except Exception as error:  # audit retains failures instead of hiding them
                    findings.append({
                        "seed": seed,
                        "demos": demos,
                        "setting": label,
                        "code": "exception",
                        "error": f"{type(error).__name__}: {error}",
                    })
            if len(by_setting) == 2 and by_setting[0] != by_setting[1]:
                findings.append({
                    "seed": seed,
                    "demos": demos,
                    "code": "setting_dependent_inputs",
                })

    if widths != {1, 2, 3, 4}:
        findings.append({"code": "width_coverage", "observed": sorted(widths)})
    if target_colors != {6, 7, 8, 9}:
        findings.append({"code": "target_color_coverage", "observed": sorted(target_colors)})
    if (30, 30) not in sizes:
        findings.append({"code": "size_coverage", "observed": sorted(sizes)})

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "06b4c496c6cf",
        "status": "failed" if findings else "passed",
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": 4,
        "settings": [dict(setting) for setting in adapter.SETTINGS],
        "episodes": episodes,
        "pairs": pairs,
        "coverage": {
            "template_widths": sorted(widths),
            "target_colors": sorted(target_colors),
            "grid_sizes": [list(size) for size in sorted(sizes)],
        },
        "rivals": sorted(adapter.lesson_report(adapter.generate(0, adapter.SETTINGS[0], 2, 4), adapter.SETTINGS[0])["rivals_tested"]),
        "findings": findings,
        "limits": "Finite seeds, declared settings, authored rivals and requested demo counts only.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seeds", type=int, default=16, help="audit seeds 0..N-1")
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    report = audit(seeds=range(args.seeds), demo_counts=range(2, 7))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        if args.out.exists():
            raise FileExistsError(args.out)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
