from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "5da2f80a4a4f"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _episode(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_mirror_matches_all_outputs():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_regression_profiles_cover_large_offset_and_non_two_scale_keys():
    large = gen.generate(
        91,
        1,
        difficulty="medium",
        grid_h=14,
        grid_w=14,
        scene_profile="canonical_large_blocks",
        palette_size=4,
    )
    large_analysis = gen._analyze(large)
    assert large_analysis["key_h"] == large_analysis["key_w"] == 4
    assert (large_analysis["key_offset_r"], large_analysis["key_offset_c"]) == (1, 1)
    assert large_analysis["palette_size"] == 4
    assert len({tuple(row) for row in large_analysis["key_matrix"]}) < 4

    variable = gen.generate(
        92,
        2,
        difficulty="hard",
        grid_h=18,
        grid_w=18,
        scene_profile="row_scale_three",
        palette_size=3,
    )
    variable_analysis = gen._analyze(variable)
    assert (variable_analysis["rscale"], variable_analysis["cscale"]) == (3, 2)
    assert gen._rival_fixed_2x(variable) != gen.rule_mirror(variable)
    assert gen._rival_four_quadrants(variable) != gen.rule_mirror(variable)


def test_every_declared_override_is_exact_and_unknown_axes_reject():
    for profile in gen.SCHEDULE_PROFILES:
        for grid_h, grid_w, palette_size in ((12, 12, 2), (18, 18, 4)):
            grid = gen.generate(
                1234,
                7,
                difficulty="medium",
                grid_h=grid_h,
                grid_w=grid_w,
                scene_profile=profile,
                palette_size=palette_size,
            )
            assert gen.observe_overrides(grid) == {
                "grid_h": grid_h,
                "grid_w": grid_w,
                "scene_profile": profile,
                "palette_size": palette_size,
            }
            assert gen.self_check(
                grid,
                meta={
                    "overrides": {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "scene_profile": profile,
                        "palette_size": palette_size,
                    }
                },
            ) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __override_contract_unknown_axis__=1)


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(
        2026,
        1,
        difficulty="medium",
        scene_profile="canonical_large_blocks",
    )
    analysis = gen._analyze(base)
    r0, c0, r1, c1 = analysis["frame"]
    kr0, kc0, kr1, kc1 = analysis["key_bbox"]

    missing_frame = copy.deepcopy(base)
    missing_frame[r0][c0] = 0
    assert gen.self_check(missing_frame)

    extra_frame = copy.deepcopy(base)
    outside = (0, 0)
    if r0 == 0 and c0 == 0:
        outside = (len(base) - 1, len(base[0]) - 1)
    extra_frame[outside[0]][outside[1]] = 2
    assert gen.self_check(extra_frame)

    key_hole = copy.deepcopy(base)
    key_hole[kr0 + 1][kc0 + 1] = 0
    assert any("key bounding box contains" in reason for reason in gen.self_check(key_hole))

    outside_key = copy.deepcopy(base)
    outside_key[0][0] = analysis["key_matrix"][0][0]
    assert any("outside frame" in reason for reason in gen.self_check(outside_key))

    nondivisible_key = copy.deepcopy(base)
    for c in range(kc0, kc1 + 1):
        nondivisible_key[kr0][c] = 0
    assert any("does not divide" in reason for reason in gen.self_check(nondivisible_key))


def test_three_demo_sliding_windows_eliminate_all_declared_rivals():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(8):
            demos = [
                _episode(7000 + band_index, start + offset, band)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = {
                "input": gen.generate(
                    7000 + band_index,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=band,
                )
            }
            assert gen.lesson_identifiable(demos, query) == []


def test_canonical_shortcuts_fit_canonical_but_generated_controls_refute_them():
    pairs = canonical_pairs(TASK_ID)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    controls = [
        gen.generate(81, 2, difficulty="medium"),
        gen.generate(82, 3, difficulty="medium"),
    ]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != gen.rule_mirror(grid) for grid in controls), name


def test_replay_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(321)
    before = random.getstate()
    first = gen.generate(404, 3, difficulty="hard")
    after = random.getstate()
    second = gen.generate(404, 3, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


# Review regressions: deleting the variable-geometry controls, putting the
# palette prefix back, or reverting RULE_HASH must make these fail.
def _frame_lookup_rule(grid):
    """A rival that fits v4's complete support without deriving both scales."""
    a = gen._analyze(grid)
    rs, cs = {
        (6, 6): (2, 2), (10, 10): (2, 2),
        (8, 10): (3, 2), (10, 8): (2, 3),
    }.get((a["frame_h"], a["frame_w"]), (2, 2))
    interior = [
        [value for value in row for _ in range(cs)]
        for row in a["key_matrix"] for _ in range(rs)
    ]
    border = [2] * (len(interior[0]) + 2)
    return [border[:]] + [[2, *row, 2] for row in interior] + [border[:]]


def test_review_rule_hash_pins_the_current_canonical_source():
    from scripts.canonical_profile_gate import canonical_rule_hash
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)


def test_review_default_support_does_not_determine_key_shape_from_frame():
    from collections import defaultdict
    by_frame = defaultdict(set)
    relative = set()
    for seed in range(64):
        for index in range(8):
            a = gen._analyze(gen.generate(seed, index, difficulty="medium"))
            by_frame[(a["frame_h"], a["frame_w"])].add((a["key_h"], a["key_w"]))
            relative.add(a["geometry"])
    assert max(map(len, by_frame.values())) >= 2, dict(by_frame)
    assert len(relative) >= 40, len(relative)


def test_review_new_controls_eliminate_lookup_in_every_three_demo_window():
    canonical = canonical_pairs(TASK_ID)
    assert all(_frame_lookup_rule(p["input"]) == p["output"] for p in canonical)
    for seed in range(12):
        for band in ("easy", "medium", "hard"):
            episodes = [_episode(seed, i, band) for i in range(18)]
            for start in range(16):
                assert any(_frame_lookup_rule(p["input"]) != p["output"]
                           for p in episodes[start:start + 3]), (seed, band, start)


def test_review_pattern_is_shuffled_after_palette_coverage_is_established():
    palette = [1, 3, 4]
    patterns = [gen._pattern_for("row_scale_three", 2, 4, palette, random.Random(i))
                for i in range(100)]
    for key in patterns:
        assert {c for row in key for c in row} == set(palette)
    assert any(len(set(key[0][:3])) < 3 for key in patterns)


def test_review_default_has_more_than_four_canvas_geometry_combinations():
    # The varying families must not be identified by their background margins.
    by_canvas = {}
    for seed in range(32):
        for index in range(8):
            a = gen._analyze(gen.generate(seed, index, difficulty="medium"))
            by_canvas.setdefault((a["height"], a["width"]), set()).add(a["geometry"])
    assert len(by_canvas.get((14, 14), set())) >= 20, by_canvas


def test_review_literal_axis_metadata_and_schedule_cover_the_same_profiles():
    assert set(gen.SCENE_PROFILES) == set(gen._PROFILE_BY_NAME)
    assert set(gen.SCHEDULE_PROFILES) == set(gen.SCENE_PROFILES)
    assert gen.AXES["scene_profile"]["valid"].split("|") == list(gen.SCENE_PROFILES)


def test_review_quadrant_repair_preserves_every_color_count():
    from collections import Counter
    from itertools import product
    for cells in product((1, 3, 4), repeat=6):
        if len(set(cells)) < 2:
            continue
        key = [list(cells[:3]), list(cells[3:])]
        result = gen._break_quadrant_pattern(key)
        assert Counter(v for row in result for v in row) == Counter(cells)
        assert not gen._is_quadrant_pattern(result)


def test_review_variable_support_is_bounded_disjoint_and_position_observable():
    assert len(gen._WIDE_GEOMETRIES) == 11
    variable = gen._VARIABLE_GEOMETRY_TO_PROFILE
    assert len(variable) == 22
    assert not set(variable).intersection(p["geometry"][:4] for p in gen._PROFILES)
    for (fh, fw, kh, kw), name in variable.items():
        assert 4 < kh * kw and max(fh, fw) <= 12
        assert (fh - 2) % kh == (fw - 2) % kw == 0
        assert (fh - 2) // kh != (fw - 2) // kw
        assert name == ("variable_wide_frame" if fh < fw else "variable_tall_frame")


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_request_contract_rejects_coercible_seed_scalars(bad_seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_request_contract_rejects_coercible_sample_index_scalars(bad_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        gen.generate(991, bad_index, difficulty="easy")


def test_request_contract_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.generate(991, -1, difficulty="easy")


@pytest.mark.parametrize("axis,value", [
    ("grid_h", "12"),
    ("grid_h", 12.0),
    ("grid_h", 12.75),
    ("grid_w", "18"),
    ("grid_w", 18.0),
    ("grid_w", 18.75),
    ("palette_size", "2"),
    ("palette_size", 2.0),
    ("palette_size", 2.75),
])
def test_request_contract_rejects_coercible_integer_overrides(axis, value):
    with pytest.raises(TypeError, match="override must be an integer"):
        gen.generate(991, 0, difficulty="easy", **{axis: value})


def _load_parametric_prototype():
    import importlib.util
    from pathlib import Path
    import sys

    path = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
    spec = importlib.util.spec_from_file_location("task_5da2_parametric_prototype", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parametric_identity_setting_preserves_the_canonical_rule():
    proto = _load_parametric_prototype()
    episode = proto.generate_episode(20261019, key_transform="identity")
    assert episode["meta"]["key_transform"] == "identity"
    assert episode["meta"]["canonical_default"] is True
    for pair in [*episode["train"], *episode["test"]]:
        assert gen.self_check(pair["input"]) == []
        assert proto.apply_rule(pair["input"], "identity") == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_parametric_transpose_setting_is_fixed_and_identifiable_per_episode():
    proto = _load_parametric_prototype()
    episode = proto.generate_episode(20261020, key_transform="transpose")
    assert episode["meta"]["key_transform"] == "transpose"
    assert episode["meta"]["canonical_default"] is False
    assert all(
        proto.apply_rule(pair["input"], "transpose") == pair["output"]
        for pair in [*episode["train"], *episode["test"]]
    )
    assert any(
        proto.apply_rule(pair["input"], "identity") != pair["output"]
        for pair in episode["train"]
    )
    assert proto.surviving_parameter_values(episode["train"]) == ["transpose"]

    public = proto.public_challenge(episode)
    assert "key_transform" not in public.get("meta", {})
    assert "program" not in public
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])


def test_parametric_programs_are_materialized_for_both_bounded_settings():
    proto = _load_parametric_prototype()
    assert proto.PARAMETER_VALUES == ("identity", "transpose")
    assert proto.DEFAULT_PARAMETER == "identity"
    programs = {value: proto.racket_program(value) for value in proto.PARAMETER_VALUES}
    assert programs["identity"] != programs["transpose"]
    assert all(program.startswith("(rule!") for program in programs.values())


def test_strict_scalar_counterexample_manifest_replays_against_final_contract():
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "counterexamples" / "strict-scalar-contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["task_id"] == TASK_ID
    assert manifest["final_generator_sha256"] == "ff819cc96803491d7e32f1f2fd8cd6a2b9bcae826ee64328ad5e8d5c424e561b"

    expected = {"TypeError": TypeError, "ValueError": ValueError}
    for case in manifest["cases"]:
        error = expected[case["exception"]]
        if case["location"] == "call_argument":
            seed = case["value"] if case["axis"] == "seed" else 991
            sample_index = case["value"] if case["axis"] == "sample_index" else 0
            with pytest.raises(error):
                gen.generate(seed, sample_index, difficulty="easy")
        else:
            with pytest.raises(error):
                gen.generate(991, 0, difficulty="easy", **{case["axis"]: case["value"]})
