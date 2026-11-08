#!/usr/bin/env python3
"""Source-bound probe for canonical-fitting shortcuts in b8259d813f79.

The retained witness is an ordinary production draw.  The probe discovers the
selected generator's declared shortcuts at runtime, verifies that each claimed
canonical shortcut fits every usable canonical pair, checks the retained Racket
receipt, and measures finite default-domain refutation counts.  It does not
claim uniqueness against undeclared hypotheses.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "b8259d813f79"
TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    source = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_probe_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _differing_cells(expected, actual) -> list[list[int]]:
    return [
        [row, column]
        for row in range(len(expected))
        for column in range(len(expected[row]))
        if expected[row][column] != actual[row][column]
    ]


def _named_callables(namespace: str) -> dict[str, Any]:
    value = getattr(GEN, namespace, None)
    if not isinstance(value, dict) or not value:
        raise AssertionError(f"{namespace} must be a nonempty dictionary")
    if not all(isinstance(name, str) and callable(fn) for name, fn in value.items()):
        raise AssertionError(f"{namespace} must contain only named callables")
    return value


def build_report(per_band: int, seed: int) -> dict[str, Any]:
    if per_band <= 0:
        raise ValueError("per_band must be positive")
    source = TASK_DIR / "generator.py"
    source_hash = _sha256(source)
    retained = json.loads((TASK_DIR / "counterexamples" / "shortcut-input.json").read_text())
    receipt = json.loads((TASK_DIR / "counterexamples" / "shortcut-racket.json").read_text())
    grid = retained["input"]
    intended = receipt["results"][0]["output"]

    assert retained["task_id"] == TASK_ID
    assert retained["generator_version"] == GEN.VERSION
    assert retained["rule_hash"] == GEN.RULE_HASH
    assert receipt["task_id"] == TASK_ID
    assert receipt["generator_sha256"] == source_hash
    assert receipt["executed_rule_hash"] == GEN.RULE_HASH
    assert receipt["rule_hash_matches_catalog"] is True
    assert receipt["results"][0]["input"] == grid
    assert receipt["results"][0]["valid_output"] is True
    assert GEN.self_check(deepcopy(grid)) == []
    assert GEN.rule_mirror(deepcopy(grid)) == intended

    canonical = canonical_pairs(TASK_ID, root=ROOT)
    shortcuts = _named_callables("CANONICAL_SHORTCUTS")
    competitors = _named_callables("LESSON_COMPETITORS")
    canonical_fit: dict[str, dict[str, int | bool]] = {}
    witness_results: dict[str, dict[str, Any]] = {}
    for name, rival in shortcuts.items():
        fits = [rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical]
        rival_output = rival(deepcopy(grid))
        differences = _differing_cells(intended, rival_output)
        assert all(fits), f"declared canonical shortcut {name!r} does not fit all pairs"
        assert differences, f"retained witness does not refute {name!r}"
        canonical_fit[name] = {
            "fit": sum(fits),
            "total": len(fits),
            "all_fit": all(fits),
        }
        witness_results[name] = {
            "rival_output": rival_output,
            "differing_cells_zero_based": differences,
        }

    if set(competitors) != set(shortcuts):
        raise AssertionError("lesson competitors and canonical shortcuts diverged")

    per_band_summary: dict[str, Any] = {}
    first_generated_witness: dict[str, Any] = {}
    for band in ("easy", "medium", "hard"):
        counts = {name: 0 for name in competitors}
        witness_counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        unique: set[str] = set()
        for sample_index in range(per_band):
            sample = GEN.generate(seed, sample_index, difficulty=band)
            errors = GEN.self_check(deepcopy(sample))
            if errors:
                raise AssertionError((band, sample_index, errors))
            expected = GEN.rule_mirror(deepcopy(sample))
            unique.add(
                hashlib.sha256(
                    json.dumps(sample, separators=(",", ":")).encode()
                ).hexdigest()
            )
            for name, rival in competitors.items():
                if rival(deepcopy(sample)) != expected:
                    counts[name] += 1
                    first_generated_witness.setdefault(
                        name,
                        {
                            "difficulty": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "profile": GEN.schedule_profile(seed, sample_index, band),
                            "input": sample,
                        },
                    )
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                witness_counts[name] += bool(predicate(deepcopy(sample)))
        per_band_summary[band] = {
            "draws": per_band,
            "unique_inputs": len(unique),
            "rival_refutations": counts,
            "semantic_witness_hits": witness_counts,
        }

    return {
        "schema": "arcpuzzles-task-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": source_hash,
        "rule_hash": GEN.RULE_HASH,
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit": canonical_fit,
        "retained_production_witness": {
            "seed": retained["seed"],
            "sample_index": retained["sample_index"],
            "difficulty": retained["difficulty"],
            "profile": retained["profile"],
            "overrides": retained["overrides"],
            "input": grid,
            "intended_racket_output": intended,
            "shortcut_results": witness_results,
            "racket_receipt": "counterexamples/shortcut-racket.json",
        },
        "finite_probe": {
            "seed": seed,
            "sample_indices": [0, per_band - 1],
            "per_band": per_band,
            "total_draws": per_band * 3,
            "per_band_summary": per_band_summary,
            "first_generated_witness_by_rival": first_generated_witness,
        },
        "limits": (
            "Finite draws and declared rivals only. Canonical fit and Racket output "
            "are checked exactly; this does not prove universal identifiability."
        ),
        "reproduce": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/b8259d813f79/workspace/shortcut_probe.py",
                "--per-band",
                str(per_band),
                "--seed",
                str(seed),
                "--out",
                "generators/b8259d813f79/counterexamples/shortcut-probe.json",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(args.per_band, args.seed)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
