"""Regressions for the strict call contract and canonical palette support."""
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "0a7f0faace31"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("contract_hardening_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def _palette_roles(pair):
    # Mirror shared/runtime/review_diagnostics.py exactly.  That coarse
    # diagnostic treats zero as absent, even though zero is a lawful ARC color.
    before = {value for row in pair["input"] for value in row if value}
    after = {value for row in pair["output"] for value in row if value}
    return (
        len(before & after),
        len(after - before),
        len(before - after),
    )


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_an_exact_integer(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_requires_a_nonnegative_exact_integer(bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, bad_index, difficulty="hard")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_first_eight_lint_samples_overlap_canonical_palette_roles(band):
    # generator_defect_lint calibrates structural support from training pairs,
    # not from the labeled test pair returned by canonical_pairs().
    canonical_roles = {
        _palette_roles(pair)
        for pair in canonical_pairs(TASK_ID, root=ROOT)
        if pair["split"] == "train"
    }
    generated_roles = set()
    for seed in range(1, 9):
        grid = gen.generate(seed, seed, difficulty=band)
        output = gen._mirror(grid)
        assert output is not None
        generated_roles.add(_palette_roles({"input": grid, "output": output}))
    assert canonical_roles & generated_roles, (band, canonical_roles, generated_roles)
