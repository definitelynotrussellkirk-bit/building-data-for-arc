"""Behavioral regressions for position leakage and truthful rival declarations."""
from collections import defaultdict
import importlib.util
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "004ca3500787"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parent.parent / "generator.py"
SPEC = importlib.util.spec_from_file_location("position_shortcuts_target", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_every_declared_canonical_shortcut_fits_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], (
                name, pair["split"], pair["pair_index"]
            )


def test_default_count_and_dimensions_do_not_determine_target_rank():
    ranks = defaultdict(set)
    canonical_ranks = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            for index in range(4):
                grid = GEN.generate(seed, index, difficulty=band)
                analysis = GEN._analysis(grid)
                assert not analysis["errors"]
                count = len(analysis["components"])
                key = (band, count, len(grid), len(grid[0]))
                rank = analysis["outlier"]["index"]
                ranks[key].add(rank)
                if count == 3:
                    canonical_ranks.add(rank)
    for key, observed in ranks.items():
        count = key[1]
        if count == 3:
            assert len(observed) >= 2, (key, observed)
        else:
            assert observed == set(range(count)), (key, observed)
    assert canonical_ranks == {0, 1, 2}


def test_each_consecutive_four_examples_refutes_actual_declared_rivals():
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            scenes = [GEN.generate(seed, i, difficulty=band) for i in range(8)]
            pairs = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in scenes]
            for start in range(4):
                demos = pairs[start:start + 4]
                query = pairs[start + 4]
                assert GEN.lesson_identifiable(demos, query) == [], (band, seed, start)
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band, seed, start, name
                    )
                for name, witness in GEN.SEMANTIC_WITNESSES.items():
                    assert any(witness(pair["input"]) for pair in demos), (
                        band, seed, start, name
                    )


def test_default_axis_provenance_uses_the_instance_context():
    from puzzle_generators.base import set_ctx_observer

    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            index = seed * 17 + 3
            contexts = []
            set_ctx_observer(contexts.append)
            try:
                grid = GEN.generate(seed, index, difficulty=band)
            finally:
                set_ctx_observer(None)
            assert contexts
            current = contexts[-1]
            assert current.sample_index == index
            assert current.difficulty == band
            recorded = current.recorded_draws()
            for axis, actual in GEN.observe_overrides(grid).items():
                assert axis in recorded, (band, seed, axis)
                assert recorded[axis] == actual, (band, seed, axis)
