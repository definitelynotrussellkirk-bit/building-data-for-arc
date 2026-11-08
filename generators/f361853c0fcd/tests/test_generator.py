"""Focused semantic and contract regressions for f361853c0fcd."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    any_border_marker_rival,
    canonical_pairs,
    columns_always_win_rival,
    intended_output,
    load_generator,
    observed,
    opposite_anywhere_rival,
    racket_outputs,
    rows_always_win_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _pair(grid):
    return {"input": grid, "output": intended_output(grid)}


def test_authority_pin_and_exact_axis_surface():
    assert gen.RULE_HASH == "cffc010305aa"
    assert set(gen.AXES) == {
        "frame_h",
        "frame_w",
        "n_v_only",
        "n_h_only",
        "n_cross",
        "n_decoys",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_canonical_pairs_are_accepted_and_independently_reproduced():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert any_border_marker_rival(pair["input"]) == pair["output"]
        assert opposite_anywhere_rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(frame_h=7, frame_w=8, n_v_only=1, n_h_only=1, n_cross=0, n_decoys=0),
        dict(frame_h=8, frame_w=10, n_v_only=2, n_h_only=1, n_cross=1, n_decoys=1),
        dict(frame_h=9, frame_w=11, n_v_only=1, n_h_only=3, n_cross=0, n_decoys=3),
        dict(frame_h=11, frame_w=12, n_v_only=3, n_h_only=3, n_cross=1, n_decoys=4),
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, options):
    grid = gen.generate(211, 17, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert {key: observed(grid)[key] for key in options} == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("frame_h", 6),
        ("frame_h", 12),
        ("frame_w", 7),
        ("frame_w", 13),
        ("n_v_only", 0),
        ("n_v_only", 4),
        ("n_h_only", 0),
        ("n_h_only", 4),
        ("n_cross", -1),
        ("n_cross", 2),
        ("n_decoys", -1),
        ("n_decoys", 5),
        ("frame_h", True),
        ("frame_w", "9"),
        ("n_v_only", 2.0),
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_lawful_and_adversarial(band):
    shapes = set()
    inputs = set()
    for index in range(90):
        grid = gen.generate(3000 + index, index, difficulty=band)
        assert grid == gen.generate(3000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        info = observed(grid)
        assert info["n_cross"] == 1
        assert 2 <= info["n_decoys"] <= 4
        truth = intended_output(grid)
        for rival in (
            any_border_marker_rival,
            opposite_anywhere_rival,
            rows_always_win_rival,
            columns_always_win_rival,
        ):
            assert rival(grid) != truth
        shapes.add((len(grid), len(grid[0])))
        inputs.add(json.dumps(grid, separators=(",", ":")))
    assert len(shapes) >= 6
    assert len(inputs) == 90


def test_schedule_reaches_all_canonical_canvas_and_palette_profiles_in_each_band():
    wanted = {
        (11, 13, 5),
        (12, 12, 5),
        (12, 14, 5),
        (13, 12, 5),
        (12, 13, 5),
    }
    for band in ("easy", "medium", "hard"):
        found = set()
        for index in range(len(gen.SCHEDULE_PROFILES)):
            grid = gen.generate(91, index, difficulty=band)
            info = observed(grid)
            found.add((info["grid_h"], info["grid_w"], len(info["palette"])))
        assert wanted <= found


def test_declared_rivals_and_witnesses_are_executable():
    grid = gen.generate(77, 0, n_decoys=4, n_cross=1)
    truth = intended_output(grid)
    independent = {
        "any_border_marker": any_border_marker_rival,
        "opposite_anywhere": opposite_anywhere_rival,
        "rows_always_win": rows_always_win_rival,
        "columns_always_win": columns_always_win_rival,
    }
    assert set(gen.SEMANTIC_RIVALS) == set(independent)
    for name, rival in independent.items():
        assert gen.SEMANTIC_RIVALS[name](grid) == rival(grid)
        assert rival(grid) != truth
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        assert gen.SEMANTIC_WITNESSES[witness_name](grid)
        assert all(gen.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)


def test_every_four_pair_window_is_identifiable_under_every_query_rotation():
    window = gen.EXAMPLES_NEEDED + 1
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            lesson = [_pair(gen.generate(600 + start, start + offset, difficulty=band)) for offset in range(window)]
            for query_index in range(window):
                query = lesson[query_index]
                demos = lesson[:query_index] + lesson[query_index + 1 :]
                assert gen.lesson_identifiable(demos, query) == []
                for competitor in gen.LESSON_COMPETITORS.values():
                    fits = all(competitor(pair["input"]) == pair["output"] for pair in demos)
                    changes_query = competitor(query["input"]) != query["output"]
                    assert not (fits and changes_query)


def test_validator_rejects_destructive_mutations():
    base = gen.generate(18, 2, frame_h=9, frame_w=10, n_v_only=2, n_h_only=2, n_cross=1, n_decoys=4)
    r1, c1, r2, c2 = observed(base)["frame_bounds"]

    gap = deepcopy(base)
    gap[r1][c1 + 1] = 0
    assert gen.self_check(gap)

    dirty_inside = deepcopy(base)
    dirty_inside[r1 + 1][c1 + 1] = 9
    assert gen.self_check(dirty_inside)

    dirty_outside = deepcopy(base)
    dirty_outside[0][0] = 4
    assert gen.self_check(dirty_outside)

    corner = deepcopy(base)
    corner[r1][c1] = 3
    assert gen.self_check(corner)

    duplicate_pair = deepcopy(base)
    pair_color = base[r1][next(col for col in range(c1 + 1, c2) if base[r1][col] == base[r2][col] != 5)]
    free = next(col for col in range(c1 + 1, c2) if base[r1][col] == base[r2][col] == 5)
    duplicate_pair[r1][free] = duplicate_pair[r2][free] = pair_color
    assert gen.self_check(duplicate_pair)


@pytest.mark.parametrize(
    "malformed",
    [None, [], [[]], [[0], [0, 0]], [[True] * 8 for _ in range(7)], [[10] * 8 for _ in range(7)]],
)
def test_malformed_grid_is_diagnostic_not_exception(malformed):
    assert gen.self_check(malformed)


def test_generation_oracles_and_rivals_do_not_mutate_inputs_or_global_rng():
    random.seed(12345)
    before = random.getstate()
    grid = gen.generate(98, 3)
    after = random.getstate()
    assert before == after
    original = deepcopy(grid)
    assert gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        assert rival(grid)
    assert grid == original
    assert grid is not gen.generate(98, 3)


def test_real_racket_reference_matches_canonical_and_generated_cases():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(700 + index, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(18)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_contract_report_finds_replayable_witnesses():
    from reference_probe import build_contract_report

    report = build_contract_report(gen, seeds=range(3), sample_indices=range(8))
    for name in ("any_border_marker", "opposite_anywhere"):
        shortcut = report["canonical_shortcuts"][name]
        assert shortcut["fits_all_canonical"] is True
        assert shortcut["witness"] is not None
    for name in gen.LESSON_COMPETITORS:
        witness = report["lesson_competitors"][name]["witness"]
        assert witness is not None
        assert witness["different_cells"]


def test_retained_shortcut_counterexample_replays():
    path = HOME / "counterexamples/any_border_marker.json"
    data = json.loads(path.read_text())
    grid = data["input"]
    assert gen.self_check(grid) == []
    assert intended_output(grid) == data["intended_output"]
    assert any_border_marker_rival(grid) == data["rival_output"]
    assert data["different_cells"]
    assert data["intended_output"] != data["rival_output"]


def test_reference_probe_finds_canonical_root_after_relocation(tmp_path):
    """Portable task tooling must not depend on its source-directory depth."""
    import importlib.util

    from reviewer_support import canonical_path, find_root

    runtime = tmp_path / "portable-runtime"
    ledger = runtime / "data/canonical/puzzles.jsonl"
    ledger.parent.mkdir(parents=True)
    source_ledger = canonical_path(find_root(__file__))
    task_rows = [
        line
        for line in source_ledger.read_text().splitlines()
        if json.loads(line).get("task_id") == gen.TASK_ID
    ]
    ledger.write_text("\n".join(task_rows) + "\n")

    relocated = runtime / "portable_tools/reference_probe.py"
    relocated.parent.mkdir(parents=True)
    relocated.write_text((HOME / "workspace/reference_probe.py").read_text())
    spec = importlib.util.spec_from_file_location("relocated_reference_probe", relocated)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.ROOT == runtime.resolve()
    assert len(module.canonical_pairs()) == 5


def test_schedule_probe_covers_all_starts_and_rotations():
    from schedule_probe import build_schedule_report

    report = build_schedule_report(gen, seeds=range(2), difficulties=("easy",))
    period = len(gen.SCHEDULE_PROFILES)
    window = gen.EXAMPLES_NEEDED + 1
    assert report["summary"] == {
        "lessons": 2 * period,
        "rotations": 2 * period * window,
        "ambiguous_rotations": 0,
        "hook_failures": 0,
    }
    assert report["starts"] == list(range(period))
    assert report["counterexamples"] == []
