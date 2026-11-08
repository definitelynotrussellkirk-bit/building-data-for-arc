"""Regression tests for the task-local semantic census tool."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import semantic_census


RUNTIME = Path(os.environ.get("ARCP_RUNTIME_ROOT", Path.cwd())).resolve()


def test_small_census_is_source_bound_and_refutes_declared_rivals():
    report = semantic_census.run_census(
        runtime_root=RUNTIME,
        lessons_per_band=5,
        bands=("easy",),
        base_seed=730_000,
    )

    generator_path = (
        RUNTIME
        / "puzzle_generators"
        / "per_puzzle"
        / semantic_census.TASK_ID
        / "generator.py"
    )
    assert report["generator_sha256"] == hashlib.sha256(generator_path.read_bytes()).hexdigest()
    assert report["source_bound"] is True
    assert report["passed"] is True
    assert report["counts"]["lessons"] == 5
    assert report["counts"]["ambiguous_lessons"] == 0
    assert report["counts"]["invalid_inputs"] == 0
    assert report["bands"]["easy"]["cyclic_start_counts"] == {
        str(index): 1 for index in range(5)
    }
    assert all(
        row["fits_all_canonical_pairs"]
        for row in report["canonical_shortcuts"].values()
    )
    assert all(
        row["lessons_refuted"] == 5
        for row in report["lesson_competitors"].values()
    )
    assert all(
        row["first_generated_counterexample"] is not None
        for row in report["canonical_shortcuts"].values()
    )
