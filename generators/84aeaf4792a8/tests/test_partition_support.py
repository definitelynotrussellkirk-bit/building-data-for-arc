"""Check the complete small-component relation support, independently of draws."""
from importlib import util
import sys

from reviewer_support import find_root


def test_partition_enumeration_has_exact_stirling_counts_without_duplicates():
    # S(n, k): ways to divide n distinct positions into k nonempty, unlabeled
    # families. These counts follow S(n,k)=k*S(n-1,k)+S(n-1,k-1), independent
    # of the generator's restricted-growth-string enumeration.
    expected = {
        2: (1, 1),
        3: (1, 3, 1),
        4: (1, 7, 6, 1),
        5: (1, 15, 25, 10, 1),
        6: (1, 31, 90, 65, 15, 1),
    }
    root = find_root(__file__)
    source = next(path for path in (
        root / "generators/84aeaf4792a8/generator.py",
        root / "puzzle_generators/per_puzzle/84aeaf4792a8/generator.py",
    ) if path.is_file())
    spec = util.spec_from_file_location("partition_support_generator", source)
    assert spec is not None and spec.loader is not None
    generator = util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)

    for count, family_counts in expected.items():
        for families, expected_count in enumerate(family_counts, 1):
            partitions = generator._partitions(count, families)
            assert len(partitions) == len(set(partitions)) == expected_count
            for labels in partitions:
                assert len(labels) == count
                assert labels[0] == 0
                assert set(labels) == set(range(families))
                assert all(0 <= label <= 1 + max(labels[:position])
                           for position, label in enumerate(labels) if position)
