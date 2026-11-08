"""Evidence tests for the canonical-compatible competing-seed rival."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
MODULE_PATH = HOME / "workspace" / "competing_seed_rival.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing helper: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_rival_diverges_on_exact_competing_seed_witness():
    rival = _load(MODULE_PATH, "competing_seed_rival")
    assert rival.nearest_seed_within_component([[1, 0, 0, 2]]) == [
        [1, 1, 2, 2]
    ]


def test_rival_fits_every_canonical_pair():
    rival = _load(MODULE_PATH, "competing_seed_rival_canonical")
    pairs = canonical_pairs("6c8eefa043e1", root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        assert rival.nearest_seed_within_component(pair["input"]) == pair["output"]


def test_selected_sampler_never_emits_the_disagreement_domain():
    rival = _load(MODULE_PATH, "competing_seed_rival_sampler")
    gen = _load(HOME / "generator.py", "selected_flood_generator")
    probe = _load(HOME / "workspace" / "review_probe.py", "selected_review_probe")
    witness = [[1, 0, 0, 2]]
    assert gen.self_check(witness)
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            grid = gen.generate(20261020, index, difficulty=band)
            assert rival.nearest_seed_within_component(grid) == probe.oracle(grid)
