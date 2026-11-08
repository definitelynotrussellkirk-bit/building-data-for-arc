from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

TASK_ID = "e42b0a4cc753"
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
gen = _load(GENERATOR_PATH, "review_generator_e42b0a4cc753")
probe = _load(
    LIBRARY / "generators" / TASK_ID / "workspace" / "voronoi_probe.py",
    "review_voronoi_probe_e42b0a4cc753",
)


def test_pins_authority_and_validates_every_canonical_input() -> None:
    assert hasattr(gen, "RULE_HASH"), "generator must pin the selected Racket authority"
    assert gen.RULE_HASH == "f23844d6433c"
    assert hasattr(gen, "self_check")
    assert hasattr(gen, "strict_canonical_like")

    pairs = canonical_pairs(TASK_ID, root=LIBRARY)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert probe.fill(pair["input"]) == pair["output"]


def test_only_exact_observable_axes_are_declared_and_honored() -> None:
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_seeds"}
    assert getattr(gen, "HELPFUL_TEXTURES", ()) == ()
    assert getattr(gen, "DEGENERATE_TEXTURES", ()) == ()
    assert getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == []
    assert hasattr(gen, "observe_overrides")

    for band in (None, "easy", "medium", "hard"):
        for h, w, n_seeds in ((6, 7, 2), (7, 9, 3), (10, 12, 5)):
            grid = gen.generate(
                41000 + h + w + n_seeds,
                h + w + n_seeds,
                difficulty=band,
                grid_h=h,
                grid_w=w,
                n_seeds=n_seeds,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {
                "grid_h": h,
                "grid_w": w,
                "n_seeds": n_seeds,
            }


def test_invalid_and_unknown_overrides_are_rejected() -> None:
    bad_cases = [
        {"__override_contract_unknown_axis__": 1},
        {"grid_h": 5},
        {"grid_h": 11},
        {"grid_w": 6},
        {"grid_w": 13},
        {"n_seeds": 1},
        {"n_seeds": 6},
        {"grid_h": True},
        {"grid_w": 8.5},
        {"n_seeds": "3"},
    ]
    for overrides in bad_cases:
        try:
            gen.generate(1, 0, **overrides)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {overrides!r}")


def _demo(seed: int, sample_index: int, difficulty):
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_declared_shortcuts_really_fit_all_canonical_examples() -> None:
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "tie_order",
        "extra_seed",
        "metric_diff",
    )
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "lower_color_tie",
        "ignore_after_first_two",
    }

    pairs = canonical_pairs(TASK_ID, root=LIBRARY)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(
            rival(pair["input"]) == pair["output"] for pair in pairs
        ), f"{name} is not a canonical-fitting shortcut"


def test_each_schedule_role_has_a_consequential_counterexample() -> None:
    for difficulty in (None, "easy", "medium", "hard"):
        samples = {
            gen.schedule_profile(83001, index, difficulty): gen.generate(
                83001, index, difficulty=difficulty
            )
            for index in range(3)
        }
        assert set(samples) == set(gen.SCHEDULE_PROFILES)

        tie_grid = samples["tie_order"]
        extra_grid = samples["extra_seed"]
        metric_grid = samples["metric_diff"]

        assert gen.rule_mirror(tie_grid) != probe.lower_color_rival(tie_grid)
        assert len(probe.seed_cells(extra_grid)) >= 3
        assert gen.rule_mirror(extra_grid) != probe.ignore_after_first_two_rival(extra_grid)
        assert gen.rule_mirror(metric_grid) != probe.euclidean_rival(metric_grid)

        for grid in samples.values():
            assert gen.self_check(grid) == []
            owner_indices = set(probe.owner_counts(grid))
            assert owner_indices == set(range(len(probe.seed_cells(grid))))


def test_every_cyclic_three_demo_window_is_identifiable() -> None:
    assert set(gen.LESSON_COMPETITORS) >= {
        "lower_color_tie",
        "ignore_after_first_two",
        "euclidean_distance",
    }
    assert set(gen.SEMANTIC_WITNESSES) == {
        "reading_order_over_lower_color",
        "third_seed_controls_blank",
        "manhattan_over_euclidean",
    }
    assert set(gen.WITNESS_RIVALS) == set(gen.SEMANTIC_WITNESSES)

    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(6):
            demos = [
                _demo(91000 + start, index, difficulty)
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            ]
            roles = {
                gen.schedule_profile(91000 + start, index, difficulty)
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            }
            assert roles == set(gen.SCHEDULE_PROFILES)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), f"window {start} does not refute {name}"

            query = {
                "input": gen.generate(
                    92000 + start,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=difficulty,
                )
            }
            assert gen.lesson_identifiable(demos, query) == []

    too_short = [_demo(93000, index, None) for index in range(2)]
    assert gen.lesson_identifiable(too_short, {"input": too_short[0]["input"]})
