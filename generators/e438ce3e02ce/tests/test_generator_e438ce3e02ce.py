from __future__ import annotations

import copy
import importlib.util
import os
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "e438ce3e02ce"
HERE = Path(__file__).resolve()
LIBRARY = next(path for path in HERE.parents if (path / "shared/runtime").is_dir())
sys.path.insert(0, str(LIBRARY / "shared/runtime"))

from reviewer_support import canonical_pairs  # noqa: E402


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATOR_PATH = Path(
    os.environ.get(
        "GENERATOR_UNDER_TEST",
        LIBRARY / "generators" / TASK_ID / "generator.py",
    )
).resolve()
gen = _load(GENERATOR_PATH, "review_generator_e438ce3e02ce")
probe = _load(
    LIBRARY / "generators" / TASK_ID / "workspace" / "voronoi_probe.py",
    "review_voronoi_probe_e438ce3e02ce",
)


def _pair(seed: int, sample_index: int, band: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": probe.fill(grid)}


def test_rule_hash_and_all_canonical_pairs_are_owned_exactly() -> None:
    assert gen.RULE_HASH == "866bf2f14b22"
    pairs = canonical_pairs(TASK_ID, root=LIBRARY)
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert probe.fill(source) == pair["output"]
        assert gen.rule_mirror(source) == pair["output"]


def test_only_exact_observable_axes_are_declared() -> None:
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_seeds"}
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()
    for band in ("easy", "medium", "hard"):
        for h in (9, 10):
            for w in (9, 12):
                for n_seeds in (3, 5):
                    grid = gen.generate(
                        44000 + h + w + n_seeds,
                        0,
                        difficulty=band,
                        grid_h=h,
                        grid_w=w,
                        n_seeds=n_seeds,
                    )
                    assert gen.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "n_seeds": n_seeds,
                    }
                    assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(44001, 0, __override_contract_unknown_axis__=1)


def test_every_cyclic_four_sample_window_is_identifiable_in_every_band() -> None:
    assert gen.EXAMPLES_NEEDED == 4
    assert len(gen.SCHEDULE_PROFILES) == 8
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            demos = [_pair(45000 + start, start + offset, band) for offset in range(4)]
            query = _pair(45000 + start, start + 4, band)
            assert gen.lesson_identifiable(demos, query) == []


def test_three_demos_are_not_claimed_sufficient() -> None:
    demos = [_pair(45100, offset, "medium") for offset in range(3)]
    query = _pair(45100, 3, "medium")
    reasons = gen.lesson_identifiable(demos, query)
    assert any("need at least 4 demonstrations" in reason for reason in reasons)


def test_schedule_exposes_seed_count_metric_and_multiway_tie_controls() -> None:
    expected_counts = [3, 4, 3, 5, 3, 4, 3, 5]
    metric_same_slots = {2, 6}
    triple_tie_slots = {0, 4}
    for band in ("easy", "medium", "hard"):
        for slot in range(8):
            grid = gen.generate(46000, slot, difficulty=band)
            info, errors = gen._analyse(grid)
            assert errors == []
            assert info["n_seeds"] == expected_counts[slot]
            disagreements = probe.disagreement_count(grid)
            if slot in metric_same_slots:
                assert disagreements == 0
            else:
                assert disagreements > 0
            tie_arities = probe.tie_arity_counts(grid)
            if slot in triple_tie_slots:
                assert max(tie_arities, default=0) >= 3
            owners = probe.owner_counts(grid)
            assert set(owners) == set(range(expected_counts[slot]))


def test_canonical_shortcuts_fit_public_pairs_but_each_lesson_refutes_them() -> None:
    shortcuts = gen.CANONICAL_SHORTCUTS
    assert {"ignore_after_first_three", "ignore_after_first_four"} <= set(shortcuts)
    canonical = canonical_pairs(TASK_ID, root=LIBRARY)
    for pair in canonical:
        for shortcut in shortcuts.values():
            assert shortcut(copy.deepcopy(pair["input"])) == pair["output"]

    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [_pair(47000 + start, start + offset, band) for offset in range(4)]
            for name, shortcut in shortcuts.items():
                assert any(
                    shortcut(pair["input"]) != pair["output"] for pair in demos
                ), f"shortcut {name} survived band={band} start={start}"


def test_semantic_rivals_are_refuted_in_every_four_example_window() -> None:
    assert gen.LESSON_COMPETITORS
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [_pair(48000 + start, start + offset, band) for offset in range(4)]
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    f"rival {name} survived band={band} start={start}"
                )


def test_structural_impostors_are_rejected() -> None:
    base = gen.generate(49000, 0, difficulty="medium")
    info, errors = gen._analyse(base)
    assert errors == []

    duplicate = copy.deepcopy(base)
    first, second = info["seeds"][:2]
    duplicate[second[0]][second[1]] = first[2]
    assert any("pairwise distinct" in reason for reason in gen.self_check(duplicate))

    cyan_seed = copy.deepcopy(base)
    cyan_seed[first[0]][first[1]] = 8
    assert any("exclude" in reason for reason in gen.self_check(cyan_seed))

    bool_cell = copy.deepcopy(base)
    blank = next((r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value == 0)
    bool_cell[blank[0]][blank[1]] = False
    assert any("integer colors" in reason for reason in gen.self_check(bool_cell))

    ragged = copy.deepcopy(base)
    ragged[0].pop()
    assert gen.self_check(ragged)

    too_short = copy.deepcopy(base[:-1])
    assert any("canonical" in reason or "height" in reason for reason in gen.self_check(too_short))


def test_deterministic_fresh_and_global_random_pure() -> None:
    random.seed(1234567)
    before = random.getstate()
    first = gen.generate(50000, 7, difficulty="hard")
    after_first = random.getstate()
    second = gen.generate(50000, 7, difficulty="hard")
    after_second = random.getstate()
    assert before == after_first == after_second
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert gen.generate(50000, 7, difficulty="hard") == second


def test_probe_matches_generator_mirror_over_schedule() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(51000, 51010):
            for slot in range(8):
                grid = gen.generate(seed, slot, difficulty=band)
                assert probe.fill(grid) == gen.rule_mirror(grid)


def test_difficulty_bands_change_layout_without_changing_schedule_contract() -> None:
    distinct_cases = 0
    total_cases = 0
    for seed in range(52000, 52012):
        for slot in range(8):
            grids = [
                gen.generate(seed, slot, difficulty=band)
                for band in ("easy", "medium", "hard")
            ]
            for grid in grids:
                assert gen.self_check(grid) == []
            observations = [gen.observe_overrides(grid) for grid in grids]
            assert observations[0] == observations[1] == observations[2]
            total_cases += 1
            distinct_cases += len({repr(grid) for grid in grids}) > 1
    assert distinct_cases >= total_cases * 0.9
