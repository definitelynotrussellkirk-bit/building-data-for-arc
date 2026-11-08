#!/usr/bin/env python3
"""Bounded self-audit for the 64a8d13b4024 parametric lesson family.

This tool is intentionally reusable by later agents.  It checks the complete
supported demo/query count surface for supplied seeds, compares matched inputs
across settings, verifies prefix stability and the demonstration-only teaching
certificate, and can write public one-query projections whose names hash only
visible bytes.  It is a finite audit, not a uniqueness or learning guarantee.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = _load(HERE / "adapter.py", "_parametric_64a8d13b4024_audit")
reviewer_support = _load(
    HERE.parents[3] / "shared" / "runtime" / "reviewer_support.py",
    "_reviewer_support_64a8d13b4024_audit",
)


def _inputs(episode: dict[str, Any]) -> list[Any]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _exact_seed(value: Any) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError("audit seeds must be exact integers in 0..2**63-1")
    return value


def run_audit(seeds: Iterable[int]) -> dict[str, Any]:
    seed_values = [_exact_seed(seed) for seed in seeds]
    failures: list[dict[str, Any]] = []
    harmful: list[dict[str, Any]] = []
    episodes = 0
    matched = 0
    exact_30 = 0
    output_differences = 0
    settings = tuple(dict(item) for item in adapter.SETTINGS)

    for seed in seed_values:
        full = {
            tuple(setting.items()): adapter.generate(seed, setting, 6, 4)
            for setting in settings
        }
        for demos in (2, 3, 6):
            for queries in range(1, 5):
                generated = {}
                for setting in settings:
                    key = tuple(setting.items())
                    episode = adapter.generate(seed, setting, demos, queries)
                    generated[key] = episode
                    episodes += 1
                    check = adapter.teaching_check(episode, setting)
                    if check["survivors"] != [setting] or check["surviving_rivals"]:
                        row = {
                            "seed": seed,
                            "settings": setting,
                            "demos": demos,
                            "queries": queries,
                            "check": check,
                        }
                        harmful.append(row)
                        failures.append({"kind": "teaching", **row})
                    if episode["train"] != full[key]["train"][:demos] or episode["test"] != full[key]["test"][:queries]:
                        failures.append({
                            "kind": "prefix",
                            "seed": seed,
                            "settings": setting,
                            "demos": demos,
                            "queries": queries,
                        })
                    exact_30 += sum(
                        len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                        for pair in episode["test"]
                    )

                fixed = generated[(('column_order', 'color_order'),)]
                ranked = generated[(('column_order', 'count_descending'),)]
                matched += 1
                if _inputs(fixed) != _inputs(ranked):
                    failures.append({
                        "kind": "setting_input_confound",
                        "seed": seed,
                        "demos": demos,
                        "queries": queries,
                    })
                output_differences += sum(
                    left["output"] != right["output"]
                    for left, right in zip(
                        fixed["train"] + fixed["test"],
                        ranked["train"] + ranked["test"],
                        strict=True,
                    )
                )

    return {
        "schema": "64a8d13b4024-parametric-audit-v1",
        "status": "passed" if not failures else "failed",
        "seeds": len(seed_values),
        "episodes": episodes,
        "matched_input_checks": matched,
        "exact_30x30_pairs": exact_30,
        "setting_output_differences": output_differences,
        "harmful_survivors": harmful,
        "failures": failures,
        "limits": (
            "Finite sweep of two declared settings, demo counts 2/3/6, query counts 1..4, "
            "prefix/matched-input checks, and nine Python rivals; Racket parity is established "
            "separately by native qualification."
        ),
    }


def write_public_samples(output: Path | str, *, seed: int = 0) -> dict[str, Any]:
    seed = _exact_seed(seed)
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise FileExistsError(f"public sample directory must be empty: {destination}")
    identifiers: list[str] = []
    for setting in adapter.SETTINGS:
        episode = adapter.generate(seed, dict(setting), 3, 4)
        for query_index in range(4):
            challenge = adapter.public_turn(episode, query_index)
            payload = reviewer_support.public_challenge_bytes(challenge)
            identifier = reviewer_support.public_challenge_id(challenge)
            if hashlib.sha256(payload).hexdigest() != identifier:
                raise ValueError("public identifier differs from exact visible bytes")
            (destination / f"{identifier}.json").write_bytes(payload)
            identifiers.append(identifier)
    duplicates = sorted({value for value in identifiers if identifiers.count(value) > 1})
    return {
        "schema": "64a8d13b4024-public-samples-v1",
        "seed": seed,
        "files": len(identifiers),
        "duplicate_public_ids": duplicates,
        "public_ids": sorted(identifiers),
        "private_fields_written": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--public-dir", type=Path)
    args = parser.parse_args(argv)
    if args.seed_count < 1:
        parser.error("--seed-count must be positive")
    summary = run_audit(range(args.seed_start, args.seed_start + args.seed_count))
    if args.public_dir:
        summary["public_samples"] = write_public_samples(args.public_dir, seed=args.seed_start)
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
