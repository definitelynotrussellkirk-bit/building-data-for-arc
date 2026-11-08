"""Regression contract for the repaired 0832c700ffb9 generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_0832c700ffb9", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(GEN.TASK_ID, root=find_root(HERE))
CANONICAL_SHAPES = {(17, 16), (17, 14), (14, 14), (17, 18)}
TEXTURES = {"plain", "same_rows", "two_rects", "border_rect", "two_rects_border"}


def _pair(grid):
    return {"input": deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_is_pinned_and_public_contract_is_truthful():
    assert GEN.RULE_HASH == "781d2d53fe4d"
    assert GEN.VERSION == "2.1.0"
    assert GEN.DEGENERATE_TEXTURES == ()
    assert set(GEN.AXES) == {"grid_h", "grid_w", "texture"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert GEN.EXAMPLES_NEEDED == 5
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "two_rects", "border_rect", "two_rects_border"
    )


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_accepts_every_canonical_input_and_mirror_matches_labels(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("h", range(14, 19))
@pytest.mark.parametrize("w", range(14, 19))
@pytest.mark.parametrize("texture", sorted(TEXTURES))
def test_all_joint_overrides_are_exact_observable_and_lawful(difficulty, h, w, texture):
    grid = GEN.generate(871, 13, difficulty=difficulty,
                        grid_h=h, grid_w=w, texture=texture)
    assert len(grid) == h
    assert len(grid[0]) == w
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": h,
        "grid_w": w,
        "texture": texture,
    }


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 13}, {"grid_h": 19}, {"grid_w": 13}, {"grid_w": 19},
        {"grid_h": True}, {"grid_w": 14.5}, {"grid_w": "14"},
        {"texture": "no_dots"}, {"texture": "lone_dot"}, {"texture": 1},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_schedule_has_exact_canonical_profiles_and_all_four_teaching_scenes(difficulty):
    for start in range(8):
        observed = []
        pairs = []
        for offset in range(6):
            index = start + offset
            grid = GEN.generate(1000 + start, index, difficulty=difficulty)
            assert GEN.self_check(grid) == []
            assert (len(grid), len(grid[0])) in CANONICAL_SHAPES
            assert len({cell for row in grid for cell in row}) == 3
            observed.append(GEN.observe_overrides(grid)["texture"])
            pairs.append(_pair(grid))
        assert set(observed[:3]) == set(GEN.SCHEDULE_PROFILES)
        for query_index in range(6):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not all(
                    rival(demo["input"]) == demo["output"] for demo in demos
                ), (difficulty, start, query_index, name)


def test_structural_validator_rejects_minimal_impostors():
    assert GEN.self_check([[1] * 14 for _ in range(14)])
    assert GEN.self_check([[0] * 14 for _ in range(14)])
    malformed = [[0] * 14 for _ in range(14)]
    malformed[1][1] = malformed[1][6] = malformed[7][1] = 2
    malformed[7][6] = 4
    assert GEN.self_check(malformed)  # not a legal two-color rectangle arrangement


def test_witnesses_fire_and_their_named_rivals_really_disagree():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(12):
        grid = GEN.generate(2200 + index, index)
        truth = GEN.rule_mirror(grid)
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            if witness(grid):
                hits[name] += 1
                for rival_name in GEN.WITNESS_RIVALS[name]:
                    assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(hits.values()), hits


def test_observed_texture_is_unambiguous_for_every_public_value():
    for texture in TEXTURES:
        seen = {
            GEN.observe_overrides(
                GEN.generate(3000 + i, i, grid_h=14 + i % 5,
                             grid_w=14 + (i * 2) % 5, texture=texture)
            )["texture"]
            for i in range(10)
        }
        assert seen == {texture}


def test_difficulty_bands_use_distinct_keyed_layout_streams():
    grids = [
        GEN.generate(444, 7, difficulty=band)
        for band in ("easy", "medium", "hard")
    ]
    assert len({repr(grid) for grid in grids}) == 3


def test_reusable_workspace_probe_reports_closed_declared_curriculum():
    workspace = HERE.parents[1] / "workspace"
    if str(workspace) not in sys.path:
        sys.path.insert(0, str(workspace))
    from probe_curriculum import audit  # noqa: E402

    report = audit(per_band=6)
    assert report["canonical"]["mirror_mismatches"] == []
    assert report["canonical"]["shortcut_failures"] == []
    assert report["joint_overrides"]["failures"] == []
    assert report["lessons"]["ambiguous"] == []
    assert report["lessons"]["rotations_checked"] > 0
    assert all(report["witness_hits"].values())


def test_production_domain_excludes_unpaired_dots_that_emit_racket_false_cells():
    assert "lone_dot" not in GEN.TEXTURES
    assert "two_rects_border" in GEN.TEXTURES
    for index in range(18):
        grid = GEN.generate(6100 + index, index, difficulty="medium")
        assert all(len(component) == 4 for component in GEN._components(grid))
        assert all(type(value) is int for row in GEN.rule_mirror(grid) for value in row)
    unpaired = GEN.generate(1, 1, texture="plain", grid_h=14, grid_w=14)
    unpaired[13][13] = next(iter({1, 2, 3, 4, 6, 7, 8, 9} - {v for row in unpaired for v in row}))
    assert GEN.self_check(unpaired)
