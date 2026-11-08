"""Focused semantic, source, override, and mutation tests for e3f1bc75d654."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


ROOT = find_root(__file__)
generator, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    "e3f1bc75d654", root=ROOT
)
CANONICAL = canonical_path(ROOT)
_DATA_ROOT = ROOT / ("data" if (ROOT / "data").is_dir() else "shared/data")
BASE_FILES = (
    _DATA_ROOT / "base/solutions/training/f21745ec__e3f1bc75d654.json",
    _DATA_ROOT / "base/solutions/augmented/f21745ec__734b953a2d89.json",
)


def _canonical_rows():
    rows = []
    with CANONICAL.open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == generator.TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs():
    return canonical_pairs(generator.TASK_ID, root=ROOT, labeled_only=True)


def _normalized_rule(source: str) -> str:
    return " ".join(source.split())


def _normalize_pattern(pattern, interior_h, interior_w):
    variants = []
    for row_flip, col_flip in ((False, False), (True, False), (False, True), (True, True)):
        transformed = []
        for row, col in pattern:
            transformed.append((
                interior_h - 1 - row if row_flip else row,
                interior_w - 1 - col if col_flip else col,
            ))
        variants.append(tuple(sorted(transformed)))
    return min(variants)


def _strict_linked_profile(grid):
    facts = generator._analyze_scene(grid)
    assert facts["errors"] == []
    template = facts["template"]
    interior_h, interior_w = template["interior"]
    return (
        facts["grid_h"],
        facts["grid_w"],
        template["interior"],
        len(facts["matching"]),
        tuple(sorted(frame["interior"] for frame in facts["distractors"])),
        _normalize_pattern(template["pattern"], interior_h, interior_w),
    )


def _canonical_linked_profiles():
    return {_strict_linked_profile(pair["input"]) for pair in _canonical_pairs()}


def _clear_bbox(grid, bbox):
    r0, c0, r1, c1 = bbox
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            grid[row][col] = 0


def _negative_recombination():
    """Move the only pattern to a uniquely sized distractor.

    The new patterned frame's interior shape is absent from every remaining
    frame, so it has no legal receiver. This is malformed teaching data even
    though the permissive Racket program can still execute it.
    """
    grid = generator.generate(
        91_337,
        17,
        difficulty="medium",
        n_match=3,
        n_distract=1,
    )
    analysis = generator._analyze_scene(grid)
    template = analysis["template"]
    distractor = analysis["distractors"][0]
    mutation = copy.deepcopy(grid)
    tr0, tc0, _tr1, _tc1 = template["bbox"]
    for dr, dc in template["pattern"]:
        mutation[tr0 + 1 + dr][tc0 + 1 + dc] = 0
    dr0, dc0, _dr1, _dc1 = distractor["bbox"]
    mutation[dr0 + 1][dc0 + 1] = distractor["color"]
    return mutation


def test_all_canonical_pairs_are_accepted_and_exact_under_python_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert generator.self_check(source) == []
        assert generator.rule_mirror(source) == pair["output"]
        assert source == snapshot


def test_rule_hash_and_every_task_local_source_are_exactly_synchronized():
    rows = _canonical_rows()
    assert len(rows) == 2
    normalized = {_normalized_rule(row["program_solution"]) for row in rows}
    assert len(normalized) == 1
    canonical_rule = rows[0]["program_solution"]
    digest = hashlib.sha256(_normalized_rule(canonical_rule).encode()).hexdigest()
    assert generator.RULE_HASH == digest[:12]
    for path in BASE_FILES:
        racket = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        # raw_code is archival and may preserve older formatting; selected
        # target_code must be the exact canonical authority text.
        assert _normalized_rule(racket["raw_code"]) == _normalized_rule(canonical_rule)
        assert racket["target_code"] == canonical_rule


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_are_structural_deterministic_and_diverse(band):
    inputs = set()
    outputs = set()
    observed = []
    for offset in range(80):
        seed = 20_000 + 1_000 * ("easy", "medium", "hard").index(band) + offset
        grid = generator.generate(seed, seed * 17 + 3, difficulty=band)
        assert generator.self_check(grid, difficulty=band) == []
        assert generator.generate(seed, seed * 17 + 3, difficulty=band) == grid
        output = generator.rule_mirror(grid)
        assert output != grid
        facts = generator._analyze_scene(grid)
        assert facts["template"] in facts["matching"]
        assert len(facts["matching"]) >= 2
        assert facts["distractors"]
        inputs.add(json.dumps(grid, separators=(",", ":")))
        outputs.add(json.dumps(output, separators=(",", ":")))
        observed.append(generator.observe_overrides(grid))
    assert len(inputs) >= 78
    assert len(outputs) >= 78
    assert len({item["template_color"] for item in observed}) >= 7
    assert len({(item["frame_h"], item["frame_w"]) for item in observed}) >= 5


def test_complete_linked_canonical_profile_prior_is_present_in_every_band():
    canonical_profiles = _canonical_linked_profiles()
    assert len(canonical_profiles) == 4
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = {profile: 0 for profile in canonical_profiles}
        draws = 400
        for offset in range(draws):
            seed = 300_000 + band_index * 10_000 + offset
            grid = generator.generate(seed, seed * 29 + 5, difficulty=band)
            profile = _strict_linked_profile(grid)
            if profile in counts:
                counts[profile] += 1
        matches = sum(counts.values())
        assert 80 <= matches <= 160  # 20%..40% around the keyed 30% prior.
        assert all(count > 0 for count in counts.values())


def test_exact_boundary_overrides_and_observer_contract():
    cases = [
        {"grid_h": 10},
        {"grid_h": 28},
        {"grid_w": 10},
        {"grid_w": 28},
        {"frame_h": 4},
        {"frame_h": 8},
        {"frame_w": 4},
        {"frame_w": 8},
        {"n_match": 2},
        {"n_match": 4},
        {"n_distract": 1},
        {"n_distract": 3},
        {"template_color": 1},
        {"template_color": 9},
        {
            "grid_h": 10,
            "grid_w": 10,
            "frame_h": 4,
            "frame_w": 4,
            "n_match": 2,
            "n_distract": 1,
            "template_color": 1,
        },
        {
            "grid_h": 28,
            "grid_w": 28,
            "frame_h": 8,
            "frame_w": 8,
            "n_match": 4,
            "n_distract": 3,
            "template_color": 9,
        },
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = generator.generate(
                50_000 + index,
                700 + index,
                difficulty=band,
                **overrides,
            )
            observed = generator.observe_overrides(grid)
            assert generator.self_check(
                grid,
                difficulty=band,
                meta={"overrides": overrides},
            ) == []
            for key, value in overrides.items():
                assert observed[key] == value


def test_invalid_controls_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(1, 2, bogus_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError, match="outside"):
        generator.generate(1, 2, grid_h=9)
    with pytest.raises(ValueError, match="not bool"):
        generator.generate(1, 2, n_match=True)
    with pytest.raises(ValueError, match="incompatible overrides"):
        generator.generate(
            1,
            2,
            grid_h=10,
            grid_w=10,
            frame_h=8,
            frame_w=8,
        )


def test_self_check_rejects_at_least_four_targeted_impostors():
    source = generator.generate(
        60_001,
        19,
        difficulty="hard",
        n_match=4,
        n_distract=2,
    )
    analysis = generator._analyze_scene(source)
    template = analysis["template"]
    receiver = next(frame for frame in analysis["matching"] if frame is not template)
    distractor = analysis["distractors"][0]

    broken_border = copy.deepcopy(source)
    r0, c0, _r1, _c1 = template["bbox"]
    broken_border[r0][c0] = 0

    second_template = copy.deepcopy(source)
    rr0, rc0, _rr1, _rc1 = receiver["bbox"]
    second_template[rr0 + 1][rc0 + 1] = receiver["color"]

    no_distractor = copy.deepcopy(source)
    for frame in analysis["distractors"]:
        _clear_bbox(no_distractor, frame["bbox"])

    merged_color_roles = copy.deepcopy(source)
    dr0, dc0, dr1, dc1 = distractor["bbox"]
    for row in range(dr0, dr1 + 1):
        for col in range(dc0, dc1 + 1):
            if merged_color_roles[row][col] == distractor["color"]:
                merged_color_roles[row][col] = template["color"]

    touching_extension = copy.deepcopy(source)
    # Add a same-colored cell just outside a frame. It extends that color's
    # bounding box without completing a new border.
    if c0 > 0:
        touching_extension[r0][c0 - 1] = template["color"]
    else:
        touching_extension[r0][c0 + 1] = 0

    for mutation in (
        broken_border,
        second_template,
        no_distractor,
        merged_color_roles,
        touching_extension,
    ):
        assert generator.self_check(mutation) != []


def test_negative_recombination_has_no_remaining_size_match_and_is_rejected():
    mutation = _negative_recombination()
    analysis = generator._analyze_scene(mutation)
    assert analysis["templates"] and len(analysis["templates"]) == 1
    new_template = analysis["templates"][0]
    same_shape_others = [
        frame
        for frame in analysis["frames"]
        if frame is not new_template and frame["interior"] == new_template["interior"]
    ]
    assert same_shape_others == []
    assert generator.self_check(mutation) != []


def test_fresh_returns_and_process_global_rng_state_are_preserved():
    random.seed(1729)
    state = random.getstate()
    first = generator.generate(991, 17, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(991, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    third = generator.generate(991, 17, difficulty="hard")
    assert third == second


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_an_exact_integer(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        generator.generate(bad_seed, 2)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_sample_index_requires_an_exact_integer(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        generator.generate(1, bad_index)


def test_sample_index_rejects_negative_values():
    with pytest.raises(ValueError, match="sample_index"):
        generator.generate(1, -1)


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1, 0.0, 1.0])
def test_difficulty_accepts_only_declared_band_names_or_none(bad_difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(1, 2, difficulty=bad_difficulty)


@pytest.mark.parametrize(
    ("axis", "bad_value"),
    [
        ("grid_h", "10"),
        ("grid_h", 10.0),
        ("grid_w", "10"),
        ("grid_w", 10.0),
        ("frame_h", "4"),
        ("frame_h", 4.0),
        ("frame_w", "4"),
        ("frame_w", 4.0),
        ("n_match", "2"),
        ("n_match", 2.0),
        ("n_distract", "1"),
        ("n_distract", 1.0),
        ("template_color", "1"),
        ("template_color", 1.0),
    ],
)
def test_exact_integer_overrides_reject_strings_and_floats(axis, bad_value):
    with pytest.raises((TypeError, ValueError), match=axis):
        generator.generate(1, 2, **{axis: bad_value})


def test_declared_leftmost_frame_shortcut_fits_canonical_and_is_refuted_by_generation():
    assert generator.CANONICAL_SHORTCUTS == {
        "leftmost_frame_sets_size": generator._leftmost_frame_shortcut
    }
    assert generator.LESSON_COMPETITORS == generator.CANONICAL_SHORTCUTS
    assert generator.SEMANTIC_RIVALS == generator.CANONICAL_SHORTCUTS
    assert generator.WITNESS_RIVALS == {
        "leftmost_frame_is_distractor": ["leftmost_frame_sets_size"]
    }
    for pair in _canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert generator._leftmost_frame_shortcut(source) == pair["output"]
        assert source == pair["input"]

    grid = generator.generate(700_001, 21_700_038, difficulty="easy")
    assert generator.strict_canonical_like(grid) == []
    assert generator.SEMANTIC_WITNESSES["leftmost_frame_is_distractor"](grid)
    assert generator._leftmost_frame_shortcut(grid) != generator.rule_mirror(grid)


def test_every_four_pair_window_teaches_the_leftmost_shortcut_under_query_rotation():
    for band in ("easy", "medium", "hard"):
        for seed in (1, 17, 91):
            for start in range(generator.LESSON_SCHEDULE_PERIOD):
                pairs = []
                for sample_index in range(start, start + 4):
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    pairs.append(
                        {
                            "input": grid,
                            "output": generator.rule_mirror(grid),
                        }
                    )
                for query_index in range(len(pairs)):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    assert any(
                        generator._leftmost_frame_shortcut(pair["input"])
                        != pair["output"]
                        for pair in demos
                    )
                    assert generator.lesson_identifiable(
                        demos, pairs[query_index]
                    ) == []


def _load_parametric_prototype():
    path = ROOT / "generators/e3f1bc75d654/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("e3f1bc75d654_parametric", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parametric_native_family_preserves_canonical_default_and_composes_bbox_selection():
    prototype = _load_parametric_prototype()
    assert prototype.TARGET_BASES == ("template_interior", "pattern_bbox")
    assert prototype.DEFAULT_SETTINGS == {"target_basis": "template_interior"}
    canonical_rule = _canonical_rows()[0]["program_solution"]
    assert prototype.program({"target_basis": "template_interior"}) == canonical_rule
    assert prototype.program({"target_basis": "pattern_bbox"}) != canonical_rule

    for setting in prototype.TARGET_BASES:
        episode = prototype.generate(
            20_261_020,
            {"target_basis": setting},
            demos=3,
            queries=4,
        )
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert all(
            prototype.transform(pair["input"], {"target_basis": setting})
            == pair["output"]
            for pair in [*episode["train"], *episode["test"]]
        )


def test_retained_leftmost_counterexample_is_reproducible_and_source_bound():
    path = (
        ROOT
        / "generators/e3f1bc75d654/counterexamples/leftmost-frame-shortcut.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["task_id"] == generator.TASK_ID
    assert payload["generator_sha256"] == _GENERATOR_SHA256
    grid = generator.generate(
        payload["seed"],
        payload["sample_index"],
        difficulty=payload["difficulty"],
        **payload["overrides"],
    )
    assert grid == payload["input"]
    assert generator.rule_mirror(grid) == payload["intended_output"]
    assert (
        generator._leftmost_frame_shortcut(grid)
        == payload["leftmost_frame_rival_output"]
    )
    assert payload["intended_output"] != payload["leftmost_frame_rival_output"]
