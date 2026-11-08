"""Bounded, reproducible Python-only coverage probe for the proposed T family.

This tool validates sampler contracts and reports observed diversity/costs.
It does not execute Racket or certify reference labels or owner acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import time


REPO = Path(__file__).resolve().parents[2] / "repo"
HOME = REPO / "generators/e971e0773705"
PARAMETRIC = HOME / "workspace/parametric"


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_binding():
    paths = [PARAMETRIC / name for name in (
        "prototype.py", "adapter.py", "promotion.json", "canonical.rkt", "README.md"
    )]
    paths.extend((HOME / "generator.py", HOME / "tests/test_parametric_e971e0773705.py"))
    return {path.relative_to(REPO).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def run(seed_count):
    spec = importlib.util.spec_from_file_location("tally_sampler_probe_prototype", PARAMETRIC / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    binding = source_binding()
    started = time.monotonic()
    input_hashes, pair_hashes, query_hashes, first_query_hashes = set(), set(), set(), set()
    first_query_shapes, demo_profiles, dense_profiles, dense_residuals = set(), set(), set(), set()
    first_winners, small_winner_residuals = set(), {"top": set(), "bottom": set()}
    first_five_output_signatures = {mode: set() for mode in module.SETTINGS}
    max_teaching, max_placement, requests, complete_bank_pairs = 0, 0, 0, 0
    costs, failures = [], []
    for seed in range(seed_count):
        seed_banks = {}
        try:
            for mode in module.SETTINGS:
                settings = {"count_mode": mode}
                full = module.generate(seed, settings, demos=6, queries=4)
                short = module.generate(seed, settings, demos=5, queries=1)
                minimum = module.generate(seed, settings, demos=5, queries=4)
                requests += 3
                assert short["train"] == minimum["train"] == full["train"][:5]
                assert short["test"] == minimum["test"][:1] == full["test"][:1]
                assert minimum["test"] == full["test"]
                assert full["sampler"] == short["sampler"] == minimum["sampler"]
                pairs = full["train"] + full["test"]
                grids = [pair["input"] for pair in pairs]
                keys = [fingerprint(grid) for grid in grids]
                assert len(set(keys)) == 10, "full-bank input novelty failed"
                for pair in pairs:
                    assert module.validate_grid(pair["input"])
                    assert len(pair["output"]) == 3 and all(len(row) == 6 for row in pair["output"])
                    pair_hashes.add(fingerprint(pair))
                input_hashes.update(keys)
                query_hashes.update(keys[6:])
                complete_bank_pairs += len(pairs)
                seed_banks[mode] = grids
                first_five_output_signatures[mode].add(fingerprint([pair["output"] for pair in pairs[:5]]))
                if mode == module.SETTINGS[0]:
                    counts = [module.counts(grid) for grid in grids]
                    demos, queries = counts[:6], counts[6:]
                    assert abs(demos[0][0] - demos[0][1]) >= 4
                    assert abs(demos[1][0] - demos[1][1]) >= 4
                    assert (demos[0][0] > demos[0][1]) != (demos[1][0] > demos[1][1])
                    assert all(1 <= abs(a-b) <= 3 for a, b in demos[2:4])
                    assert (demos[2][0] > demos[2][1]) != (demos[3][0] > demos[3][1])
                    assert demos[4][0] == demos[4][1] > 0
                    first_winners.add("top" if demos[0][0] > demos[0][1] else "bottom")
                    for a, b in demos[2:4]:
                        small_winner_residuals["top" if a > b else "bottom"].add(abs(a-b))
                    large = grids[-1]
                    assert len(large) == len(large[0]) == 30
                    assert sum(queries[-1]) == 54
                    assert sum(value == 2 for row in large for value in row) == 216
                    assert any(large[0]) and any(large[-1])
                    assert any(row[0] for row in large) and any(row[-1] for row in large)
                    first_query_hashes.add(keys[6])
                    first_query_shapes.add((len(grids[6]), len(grids[6][0])))
                    demo_profiles.add(tuple(demos[:5]))
                    dense_profiles.add(queries[-1])
                    dense_residuals.add(module.residual_counts(*queries[-1], "cancel_opposites"))
                    sampler = full["sampler"]
                    max_teaching = max(max_teaching, sampler["teaching_attempts"])
                    max_placement = max(max_placement, *sampler["placement_attempts"])
                    costs.append({"seed": seed, **sampler})
            assert seed_banks["raw"] == seed_banks["cancel_opposites"], "settings changed input bank"
        except Exception as error:
            failures.append({"seed": seed, "type": type(error).__name__, "message": str(error)})
    if source_binding() != binding:
        failures.append({"type": "SourceChanged", "message": "family bytes changed during the probe"})
    return {
        "schema": "e971e0773705-bounded-sampler-v1",
        "status": "failed" if failures else "passed",
        "scope": "Python-only sampler contracts and claim-label diversity; no Racket label or acceptance certification.",
        "seed_range": [0, seed_count - 1],
        "settings": list(module.SETTINGS),
        "requests_per_seed_setting": [
            {"demos": 6, "queries": 4}, {"demos": 5, "queries": 1}, {"demos": 5, "queries": 4}
        ],
        "episode_request_count": requests,
        "complete_bank_pair_records": complete_bank_pairs,
        "unique_input_count": len(input_hashes),
        "unique_claim_labeled_pair_count": len(pair_hashes),
        "unique_query_input_count": len(query_hashes),
        "unique_first_query_input_count": len(first_query_hashes),
        "first_query_shapes": sorted(first_query_shapes),
        "unique_first_five_count_profile_sequences": len(demo_profiles),
        "unique_first_five_output_signatures": {mode: len(values) for mode, values in first_five_output_signatures.items()},
        "first_saturated_winner_orientations": sorted(first_winners),
        "nonsaturated_winner_residuals": {kind: sorted(values) for kind, values in small_winner_residuals.items()},
        "dense_query_count_profiles": sorted(dense_profiles),
        "dense_query_residual_profiles": sorted(dense_residuals),
        "dense_query_shape": [30, 30],
        "dense_query_component_count": 54,
        "dense_query_red_cell_count": 216,
        "dense_query_all_four_boundaries_occupied": not failures,
        "maximum_observed_teaching_attempts": max_teaching,
        "maximum_observed_placement_attempts": max_placement,
        "declared_attempt_limit": module.MAX_ATTEMPTS,
        "sampler_exhaustions": sum(failure["type"] == "RuntimeError" for failure in failures),
        "failures": failures,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "source_sha256": binding,
        "per_seed": costs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-count", type=int, default=24)
    args = parser.parse_args()
    if not 1 <= args.seed_count <= 1000:
        parser.error("seed-count must be 1..1000")
    if args.out.exists():
        raise FileExistsError(args.out)
    report = run(args.seed_count)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in ("per_seed", "source_sha256")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
