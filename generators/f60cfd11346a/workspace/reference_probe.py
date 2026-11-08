#!/usr/bin/env python3
"""Reproduce the canonical-fitting shortcut and a generated counterexample.

Run from a review packet with Racket evidence:

    python3 run_with_racket.py python3 \
      repo/generators/f60cfd11346a/workspace/reference_probe.py \
      --racket --out checks/shortcut-probe.json

Without ``--racket`` the probe remains portable and compares the generator's
pure mirror against every declared canonical shortcut.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "f60cfd11346a"
HOME = Path(__file__).resolve().parents[1]
DEFAULT_OVERRIDES = {
    "grid_h": 9,
    "grid_w": 11,
    "layout_style": "vertical",
    "accent_color": 1,
}


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ordinary_sampler_probe(gen, *, draws: int = 64) -> dict[str, Any]:
    bands = ("easy", "medium", "hard")
    competitors = dict(gen.LESSON_COMPETITORS)
    disagreements = {name: 0 for name in competitors}
    unseen_accent_draws = 0
    for index in range(draws):
        grid = gen.generate(70000 + index, index * 19 + 5, difficulty=bands[index % 3])
        observed = gen.observe_overrides(grid)
        unseen_accent_draws += observed["accent_color"] in (1, 9)
        intended = gen.rule_mirror(grid)
        for name, rival in competitors.items():
            disagreements[name] += intended != rival(grid)
    palette_disagreements = disagreements["canonical_blocker_palette_only"]
    return {
        "draws": draws,
        "seed_range": [70000, 70000 + draws - 1],
        "sample_index_formula": "index*19+5",
        "unseen_accent_draws": unseen_accent_draws,
        "rival_disagreements": palette_disagreements,
        "all_draws_refute_rival": palette_disagreements == draws,
        "competitors": {
            name: {
                "disagreements": count,
                "all_draws_refute": count == draws,
            }
            for name, count in sorted(disagreements.items())
        },
    }


def build_report(
    *,
    include_racket: bool = False,
    seed: int = 43,
    sample_index: int = 2,
    difficulty: str = "medium",
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a source-bound shortcut report with one exact generated witness."""
    gen = _load_generator()
    root = find_root(__file__)
    pairs = canonical_pairs(TASK_ID, root=root)
    requested = dict(DEFAULT_OVERRIDES if overrides is None else overrides)
    grid = gen.generate(
        seed,
        sample_index,
        difficulty=difficulty,
        **requested,
    )
    intended = gen.rule_mirror(grid)

    rivals: dict[str, Any] = {}
    all_rivals = dict(gen.LESSON_COMPETITORS)
    for name, rival_fn in all_rivals.items():
        pair_results = []
        for pair in pairs:
            predicted = rival_fn(pair["input"])
            pair_results.append(
                {
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "fits": predicted == pair["output"],
                }
            )
        rival_output = rival_fn(grid)
        rivals[name] = {
            "declared_as_canonical_shortcut": name in gen.CANONICAL_SHORTCUTS,
            "declared_as_lesson_competitor": name in gen.LESSON_COMPETITORS,
            "canonical_pairs_checked": len(pair_results),
            "fits_all_canonical_pairs": all(item["fits"] for item in pair_results),
            "canonical_pair_results": pair_results,
            "witness_output": rival_output,
            "witness_disagrees": rival_output != intended,
        }

    sampler = _ordinary_sampler_probe(gen)
    report: dict[str, Any] = {
        "schema": "f60cfd11346a-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _sha256(HOME / "generator.py"),
        "declared_rule_hash": gen.RULE_HASH,
        "witness": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": requested,
            "observed_overrides": gen.observe_overrides(grid),
            "self_check": gen.self_check(grid),
            "input": grid,
            "intended_mirror_output": intended,
            "ordinary_sampler_emits_this_class": all(
                item["all_draws_refute"] for item in sampler["competitors"].values()
            ),
        },
        "ordinary_sampler_probe": sampler,
        "rivals": rivals,
        "racket": None,
    }

    if include_racket:
        from arcpuzzles import Catalog

        receipt = Catalog(root).apply(
            TASK_ID,
            [grid],
            reference="canonical",
            timeout=180,
        )
        result = receipt["results"][0]
        racket_output = result["output"]
        report["racket"] = {
            "executed_rule_hash": receipt.get("executed_rule_hash"),
            "catalog_rule_hash": receipt.get("catalog_rule_hash"),
            "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
            "error": result.get("error"),
            "output": racket_output,
            "matches_intended_mirror": racket_output == intended,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write JSON report here")
    parser.add_argument("--racket", action="store_true", help="execute selected Racket authority")
    args = parser.parse_args()

    report = build_report(include_racket=args.racket)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
