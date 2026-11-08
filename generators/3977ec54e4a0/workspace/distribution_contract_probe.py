#!/usr/bin/env python3
"""Reproduce the two distribution-contract bugs repaired in generator 4.1.1.

Run from any checkout containing ``generators/3977ec54e4a0/generator.py``:

    python3 generators/3977ec54e4a0/workspace/distribution_contract_probe.py

The probe deliberately uses the generator's decoder and the Racket authority's
published marker-nearness relation, but it does not need a Racket process.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "3977ec54e4a0"


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "generators" / TASK_ID / "generator.py").is_file():
            return parent
    raise RuntimeError("could not locate repository root")


def _load_generator(repo_root: Path):
    runtime = repo_root / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
    source = repo_root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source


class PreferredApexRng:
    """Minimal RNG stub that places requested apex candidates first."""

    def __init__(self, *apices: tuple[int, int]):
        self._apices = iter(apices)

    def shuffle(self, candidates) -> None:
        desired = next(self._apices)
        candidates.sort(key=lambda candidate: candidate[:2] != desired)


def main() -> int:
    repo_root = _find_repo_root()
    generator, source = _load_generator(repo_root)

    axis_failures: list[dict[str, object]] = []
    draws = 0
    for requested in (False, True):
        for seed in range(64):
            grid = generator.generate(
                seed,
                seed * 29 + 7,
                difficulty="hard",
                grid_h=22,
                grid_w=22,
                chevron_count=4,
                max_depth=3,
                asymmetric_arms=requested,
            )
            chevrons, errors = generator._decode_grid(grid)
            actual = bool(chevrons) and any(
                item.left_mask != item.right_mask for item in chevrons
            )
            draws += 1
            if errors or actual != requested:
                axis_failures.append(
                    {
                        "requested": requested,
                        "seed": seed,
                        "errors": errors,
                        "actual_asymmetric_masks": actual,
                        "descriptors": [item.descriptor for item in chevrons],
                    }
                )

    descriptor = (0, 1, (True,), (True,))
    placed = generator._place_descriptors(
        12,
        12,
        [descriptor, descriptor],
        PreferredApexRng((2, 2), (3, 6)),
    )
    close_witness = {
        "requested_apices": [[2, 2], [3, 6]],
        "actual_apices": [list(item.apex) for item in placed],
        "markers": [sorted(map(list, item.markers)) for item in placed],
        "cross_near_edges": [
            [list(a), list(b)]
            for a in placed[0].markers
            for b in placed[1].markers
            if generator._near(a, b)
        ],
        "minimum_chebyshev_distance": min(
            max(abs(a[0] - b[0]), abs(a[1] - b[1]))
            for a in placed[0].markers
            for b in placed[1].markers
        ),
    }

    witness_grid = [[0 for _ in range(12)] for _ in range(12)]
    witness_grid[0][1] = 1
    for item in placed:
        for r, c in item.markers:
            witness_grid[r][c] = 3
    close_witness["self_check_errors"] = generator.self_check(witness_grid)

    passed = (
        not axis_failures
        and close_witness["actual_apices"] == close_witness["requested_apices"]
        and not close_witness["cross_near_edges"]
        and close_witness["self_check_errors"] == []
    )

    report = {
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "axis_draws": draws,
        "axis_failures": axis_failures,
        "close_component_witness": close_witness,
        "status": "PASS" if passed else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
