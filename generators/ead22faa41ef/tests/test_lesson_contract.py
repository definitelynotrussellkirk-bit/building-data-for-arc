from __future__ import annotations

import importlib.util
from pathlib import Path


GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("ead22faa41ef_generator_under_test", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


def _pair(grid):
    return {"input": grid, "output": generator.rule_mirror(grid)}


def test_known_all_cells_shortcut_is_named_when_demos_do_not_refute_it():
    demos = [
        _pair([
            [3, 2, 0],
            [0, 0, 0],
            [0, 5, 0],
        ]),
        _pair([
            [0, 3, 0],
            [0, 2, 0],
            [5, 0, 0],
        ]),
        _pair([
            [0, 2, 3],
            [0, 0, 0],
            [0, 0, 5],
        ]),
    ]
    query = _pair([
        [3, 2, 0, 0],
        [0, 0, 0, 2],
        [5, 0, 0, 0],
    ])

    findings = generator.lesson_identifiable(demos, query)

    assert any("global_replacement" in finding for finding in findings)


def test_even_default_slots_emit_both_preserved_colors():
    assert generator.LESSON_SCHEDULE_PERIOD == 2
    assert tuple(generator.SCHEDULE_PROFILES) == (
        "preserved_lones",
        "free",
    )
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            sample_index = 2 * seed
            assert generator.schedule_profile(seed, sample_index, band) == "preserved_lones"
            grid = generator.generate(seed, sample_index, difficulty=band)
            features = generator._scene_features(grid)
            assert features["counts"][3] - len(features["paired3"]) >= 1
            assert features["counts"][2] - len(features["paired2"]) >= 1


def test_four_pair_windows_refute_global_shortcut_under_every_query_rotation():
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            for start in range(6):
                pairs = [
                    _pair(
                        generator.generate(
                            10_000 + seed,
                            start + offset,
                            difficulty=band,
                        )
                    )
                    for offset in range(generator.EXAMPLES_NEEDED + 1)
                ]
                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs)
                        if index != query_index
                    ]
                    assert generator.lesson_identifiable(demos, query) == [], (
                        band,
                        seed,
                        start,
                        query_index,
                    )
