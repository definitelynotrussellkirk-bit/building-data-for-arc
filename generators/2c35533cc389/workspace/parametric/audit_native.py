#!/usr/bin/env python3
"""Source-bound finite audit for a native parametric ARC family.

The audit exercises every supported demonstration/query prefix, verifies that
inputs are matched across settings, checks prefix stability and public-turn
redaction, and rejects any declared rival that fits the demonstrations while
changing an independently scored query.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve()
TASK_ID = HERE.parents[2].name


def _load_family():
    path = HERE.with_name("native_family.py")
    name = f"native_family_audit_{TASK_ID}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load native family from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if getattr(module, "TASK_ID", None) != TASK_ID:
        raise RuntimeError("audit path and native family task id disagree")
    return module


def _stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _input_vector(episode: dict[str, Any]) -> list[Any]:
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def build_report(seeds: Iterable[int] = range(32)) -> dict[str, Any]:
    seed_list = list(seeds)
    if not seed_list or len(seed_list) > 256:
        raise ValueError("audit requires 1..256 seeds")
    if any(type(seed) is not int or seed < 0 for seed in seed_list):
        raise ValueError("audit seeds must be nonnegative exact integers")
    if len(set(seed_list)) != len(seed_list):
        raise ValueError("audit seeds must be unique")

    family = _load_family()
    demo_counts = list(range(2, 7))
    query_counts = list(range(1, 5))
    findings: list[dict[str, Any]] = []
    episodes_checked = 0
    pair_labels_checked = 0
    public_views_checked = 0
    distinct_inputs: set[str] = set()

    for seed in seed_list:
        full = {
            mode: family.generate(seed, {family.PARAMETER: mode}, demos=6, queries=4)
            for mode in family.MODES
        }
        vectors = {mode: _stable(_input_vector(episode)) for mode, episode in full.items()}
        reference = vectors[family.MODES[0]]
        for mode, vector in vectors.items():
            if vector != reference:
                findings.append({"kind": "unmatched_inputs", "seed": seed, "mode": mode})
        distinct_inputs.update(_stable(grid) for grid in _input_vector(full[family.MODES[0]]))

        for mode in family.MODES:
            expected_full = full[mode]
            for demos in demo_counts:
                for queries in query_counts:
                    episode = family.generate(
                        seed,
                        {family.PARAMETER: mode},
                        demos=demos,
                        queries=queries,
                    )
                    episodes_checked += 1
                    pair_labels_checked += demos + queries
                    if episode["train"] != expected_full["train"][:demos]:
                        findings.append({
                            "kind": "demo_prefix_instability",
                            "seed": seed,
                            "mode": mode,
                            "demos": demos,
                            "queries": queries,
                        })
                    if episode["test"] != expected_full["test"][:queries]:
                        findings.append({
                            "kind": "query_prefix_instability",
                            "seed": seed,
                            "mode": mode,
                            "demos": demos,
                            "queries": queries,
                        })
                    for finding in family.teaching_check(episode):
                        findings.append({
                            "kind": "dangerous_rival",
                            "seed": seed,
                            "mode": mode,
                            "demos": demos,
                            "queries": queries,
                            **finding,
                        })
                    for index in range(queries):
                        public = json.loads(family.public_turn_bytes(episode, index))
                        public_views_checked += 1
                        expected_public = {
                            "train": episode["train"],
                            "test": [{"input": episode["test"][index]["input"]}],
                        }
                        if public != expected_public:
                            findings.append({
                                "kind": "public_projection_mismatch",
                                "seed": seed,
                                "mode": mode,
                                "demos": demos,
                                "queries": queries,
                                "query_index": index,
                            })

    source = HERE.with_name("native_family.py")
    report = {
        "schema": "arcpuzzles-native-family-audit-v1",
        "task_id": TASK_ID,
        "source": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "seeds": seed_list,
        "settings": [{family.PARAMETER: mode} for mode in family.MODES],
        "declared_rivals": list(family.RIVALS),
        "demo_counts": demo_counts,
        "query_counts": query_counts,
        "episodes_checked": episodes_checked,
        "pair_labels_checked": pair_labels_checked,
        "public_views_checked": public_views_checked,
        "distinct_inputs_seen": len(distinct_inputs),
        "findings": findings,
        "ok": not findings,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if not 1 <= args.seed_count <= 256:
        parser.error("--seed-count must be in 1..256")
    report = build_report(range(args.seed_count))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
