#!/usr/bin/env python3
"""Replay the task's declared rivals against canonical demos and generated draws.

This is an authoring probe, not an authority implementation. It uses the
selected generator's Python mirror to locate compact counterexamples. Confirm a
retained counterexample with ``arcpuzzles apply`` before treating it as rule
evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "6c40e60caa4a"
TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"
ROOT = find_root(__file__)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _declared_rivals(gen) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for declaration in (
        "CANONICAL_SHORTCUTS",
        "LESSON_COMPETITORS",
        "SEMANTIC_RIVALS",
    ):
        mapping = getattr(gen, declaration, {}) or {}
        if not isinstance(mapping, dict):
            continue
        for name, fn in mapping.items():
            if not callable(fn):
                continue
            row = found.setdefault(str(name), {"callable": fn, "declared_in": []})
            row["declared_in"].append(declaration)
    return found


def _digest(value) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def run_probe(*, seed_count: int, index_count: int) -> dict:
    gen = _load_generator()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    demos = [pair for pair in pairs if pair["split"] == "train"]
    rivals = _declared_rivals(gen)
    bands = ["easy", "medium", "hard"]

    report = {
        "schema": "arcpuzzles-declared-rival-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_training_pairs": len(demos),
        "scan": {
            "bands": bands,
            "seeds": list(range(seed_count)),
            "sample_indices": list(range(index_count)),
        },
        "rivals": {},
    }

    for name, declared in sorted(rivals.items()):
        rival: Callable = declared["callable"]
        canonical_results = []
        for pair in demos:
            try:
                prediction = rival(pair["input"])
                canonical_results.append(prediction == pair["output"])
            except Exception as exc:  # evidence should keep the exact failure
                canonical_results.append(f"{type(exc).__name__}: {exc}")

        witness = None
        checked = 0
        for band in bands:
            if witness is not None:
                break
            for seed in range(seed_count):
                if witness is not None:
                    break
                for sample_index in range(index_count):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    checked += 1
                    intended = gen.expected_output(grid)
                    try:
                        alternate = rival(grid)
                    except Exception as exc:
                        witness = {
                            "kind": "rival_error",
                            "error": f"{type(exc).__name__}: {exc}",
                            "seed": seed,
                            "sample_index": sample_index,
                            "difficulty": band,
                            "input": grid,
                        }
                        break
                    if alternate != intended:
                        witness = {
                            "kind": "prediction_disagreement",
                            "seed": seed,
                            "sample_index": sample_index,
                            "difficulty": band,
                            "profile": gen.observe_overrides(grid),
                            "validator_findings": gen.self_check(grid),
                            "input_sha256": _digest(grid),
                            "intended_output_sha256": _digest(intended),
                            "rival_output_sha256": _digest(alternate),
                            "input": grid,
                            "python_mirror_output": intended,
                            "rival_output": alternate,
                        }
                        break

        report["rivals"][name] = {
            "declared_in": declared["declared_in"],
            "fits_every_canonical_training_pair": all(
                result is True for result in canonical_results
            ),
            "canonical_training_results": canonical_results,
            "generated_draws_checked_until_witness": checked,
            "first_generated_witness": witness,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--indices", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds <= 0 or args.indices <= 0:
        parser.error("--seeds and --indices must be positive")
    report = run_probe(seed_count=args.seeds, index_count=args.indices)
    payload = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
