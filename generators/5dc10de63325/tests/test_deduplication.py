"""A retained production-sampler failure: duplicate removal lost a glyph witness."""
from collections import Counter
import importlib.util

from reviewer_support import find_root


def _generator():
    root = find_root(__file__)
    path = next(path for path in (
        root / "generators/5dc10de63325/generator.py",
        root / "puzzle_generators/per_puzzle/5dc10de63325/generator.py",
    ) if path.is_file())
    spec = importlib.util.spec_from_file_location("dedup_count_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_duplicate_filter_retains_two_examples_of_every_nontrivial_glyph():
    generator = _generator()
    accepted, seen = [], set()
    for index in range(1, 101):
        grid = generator.generate(319, index, difficulty="medium")
        fingerprint = tuple(tuple(row) for row in grid)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        accepted.append(grid)
        if len(accepted) == 11:
            break
    assert len(accepted) == 11
    buckets = Counter(sum(cell == 8 for row in grid for cell in row) // 4
                      for grid in accepted)
    assert all(buckets[q] >= 2 for q in (1, 2, 3)), buckets
