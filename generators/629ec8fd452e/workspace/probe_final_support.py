#!/usr/bin/env python3
"""Source-bound semantic-support probe for generator 629ec8fd452e.

This is an authoring/review tool, not a blind-solve helper. It uses public
reviewer_support APIs so it runs from either the repository or a staged runtime.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "629ec8fd452e"
BANDS = ("easy", "medium", "hard")


def _component_sizes(analysis: dict[str, Any], role: str) -> list[int]:
    return sorted({len(component["cells"]) for component in analysis[role]})


def run_probe(draws_per_band: int) -> dict[str, Any]:
    root = find_root(__file__)
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_fit: dict[str, dict[str, Any]] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        per_pair = [
            rival(copy.deepcopy(pair["input"])) == pair["output"]
            for pair in canonical
        ]
        canonical_fit[name] = {
            "matched": sum(per_pair),
            "total": len(per_pair),
            "per_pair": per_pair,
        }

    witness_hits = defaultdict(int)
    rival_disagreements = defaultdict(int)
    role_sizes: dict[str, set[int]] = {
        "hollow": set(),
        "open_like": set(),
        "solid": set(),
    }
    validator_errors: list[dict[str, Any]] = []
    overlap_failures: list[dict[str, Any]] = []
    rival_agreements: list[dict[str, Any]] = []
    sampled = 0

    for band in BANDS:
        for sample_index in range(draws_per_band):
            seed = int.from_bytes(
                f"{TASK_ID}:{band}:{sample_index}".encode(), "little"
            ) % (2**63)
            grid = gen.generate(seed, sample_index, difficulty=band)
            sampled += 1
            errors = gen.self_check(grid) + gen.strict_canonical_like(grid)
            if errors:
                validator_errors.append(
                    {
                        "band": band,
                        "sample_index": sample_index,
                        "seed": seed,
                        "errors": errors,
                    }
                )

            analysis = gen._analysis(grid)
            per_scene_sizes = {
                role: _component_sizes(analysis, role)
                for role in role_sizes
            }
            for role, sizes in per_scene_sizes.items():
                role_sizes[role].update(sizes)
            if not (
                set(per_scene_sizes["hollow"])
                & set(per_scene_sizes["open_like"])
            ):
                overlap_failures.append(
                    {
                        "band": band,
                        "sample_index": sample_index,
                        "seed": seed,
                        "sizes": per_scene_sizes,
                    }
                )

            expected = gen.rule_true(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += int(bool(witness(copy.deepcopy(grid))))
            for name, rival in gen.SEMANTIC_RIVALS.items():
                differs = rival(copy.deepcopy(grid)) != expected
                rival_disagreements[name] += int(differs)
                if not differs:
                    rival_agreements.append(
                        {
                            "band": band,
                            "sample_index": sample_index,
                            "seed": seed,
                            "rival": name,
                        }
                    )

    scalar_cases = [
        ("seed_bool", lambda: gen.generate(True, 0)),
        ("seed_float", lambda: gen.generate(1.0, 0)),
        ("sample_index_bool", lambda: gen.generate(1, True)),
        ("sample_index_float", lambda: gen.generate(1, 0.0)),
        ("sample_index_negative", lambda: gen.generate(1, -1)),
        ("n_hollow_bool", lambda: gen.generate(1, 0, n_hollow=True)),
        ("n_hollow_float", lambda: gen.generate(1, 0, n_hollow=1.0)),
        ("n_hollow_string", lambda: gen.generate(1, 0, n_hollow="1")),
    ]
    scalar_rejections = {}
    for name, call in scalar_cases:
        try:
            call()
        except (TypeError, ValueError) as exc:
            scalar_rejections[name] = {
                "rejected": True,
                "exception": type(exc).__name__,
                "message": str(exc),
            }
        else:
            scalar_rejections[name] = {"rejected": False}

    return {
        "schema": "arcpuzzles-task-semantic-support-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha256,
        "source_path": str(source_path),
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "draws_per_band": draws_per_band,
        "sampled": sampled,
        "canonical_labeled_pairs": len(canonical),
        "canonical_shortcut_fit": canonical_fit,
        "declared_witnesses": list(gen.SEMANTIC_WITNESSES),
        "witness_hits": dict(witness_hits),
        "declared_rivals": list(gen.SEMANTIC_RIVALS),
        "rival_disagreements": dict(rival_disagreements),
        "observed_component_sizes": {
            role: sorted(sizes) for role, sizes in role_sizes.items()
        },
        "validator_errors": validator_errors,
        "size_overlap_failures": overlap_failures,
        "rival_agreements": rival_agreements,
        "scalar_rejections": scalar_rejections,
        "passed": (
            not validator_errors
            and not overlap_failures
            and not rival_agreements
            and all(count == sampled for count in witness_hits.values())
            and all(count == sampled for count in rival_disagreements.values())
            and all(item["rejected"] for item in scalar_rejections.values())
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws-per-band", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.draws_per_band <= 0:
        parser.error("--draws-per-band must be positive")
    result = run_probe(args.draws_per_band)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
