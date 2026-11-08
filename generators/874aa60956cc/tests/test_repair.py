"""Behavior regressions for exact sampling and malformed-input rejection."""
import importlib.util
from collections import Counter
from pathlib import Path
import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "874aa60956cc"
HOME = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("reviewed_rectangle_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def counts(grid):
    return Counter(v for row in grid for v in row if v)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [(5,5), (5,18), (18,5), (18,18)])
def test_full_documented_dimensions_in_every_band(band, shape):
    h,w=shape
    g=gen.generate(17, 0, difficulty=band, grid_h=h, grid_w=w, rectangles=6)
    assert (len(g),len(g[0])) == shape
    assert sum(n == 2 for n in counts(g).values()) == 6


@pytest.mark.parametrize("number", range(1,7))
def test_requested_rectangles_are_never_silently_dropped(number):
    for i in range(12):
        g=gen.generate(29,i,grid_h=5,grid_w=5,rectangles=number)
        assert sum(n == 2 for n in counts(g).values()) == number


def test_all_count_controls_visible_together_at_smallest_canvas():
    g=gen.generate(43,0,grid_h=5,grid_w=5,rectangles=6,singletons=1,triples=1)
    assert sorted(counts(g).values()) == [1,2,2,2,2,2,2,3]


@pytest.mark.parametrize("overrides", [{"unknown_axis":1}, {"grid_h":True}, {"grid_w":5.5}, {"rectangles":0}, {"singletons":2}, {"triples":-1}])
def test_invalid_or_unknown_overrides_raise(overrides):
    with pytest.raises(ValueError):
        gen.generate(0,0,**overrides)


def test_validator_does_not_skip_bad_group_after_singleton():
    g=[[0]*5 for _ in range(5)]
    g[0][0]=1
    for c in range(4): g[1][c]=2
    g[2][0]=3;g[4][2]=3
    assert gen.self_check(g)


@pytest.mark.parametrize("value", [True, 1.5, -1, 10, "2"])
def test_validator_rejects_non_arc_cell_values(value):
    g=[[0]*5 for _ in range(5)]
    g[0][0]=value;g[3][3]=value
    assert gen.self_check(g)


def test_canonical_inputs_still_supported():
    for pair in canonical_pairs(TASK,root=find_root(__file__),labeled_only=True):
        assert not gen.self_check(pair["input"])
        assert not gen.strict_canonical_like(pair["input"])


def test_pixel_observer_reports_every_declared_axis():
    g=gen.generate(19,1,grid_h=7,grid_w=8,rectangles=4,singletons=1,triples=1)
    assert gen.observe_overrides(g) == {"grid_h":7,"grid_w":8,"rectangles":4,"singletons":1,"triples":1}


def test_default_curriculum_has_real_crossings_and_multiplicity_witnesses():
    # A positive-diagonal-only sampler, pair-completion painter, or clue
    # restorer must be rejected by every default lesson's demonstrations.
    for band in ("easy","medium","hard"):
        for i in range(4):
            g=gen.generate(17,i,difficulty=band)
            expected=gen._predict(g)
            assert all(f(g)!=expected for name,f in gen.LESSON_COMPETITORS.items()
                       if name != "bounding_boxes_for_many")
            if i % 2:
                assert gen.LESSON_COMPETITORS["bounding_boxes_for_many"](g)!=expected


def test_difficulty_changes_default_distribution_without_shrinking_overrides():
    draws = {band: [gen.generate(31,i,difficulty=band) for i in range(8)]
             for band in ("easy","medium","hard")}
    assert draws["easy"] != draws["medium"]
    assert draws["medium"] != draws["hard"]


def test_authoring_mirror_matches_all_canonical_labels():
    for pair in canonical_pairs(TASK,root=find_root(__file__),labeled_only=True):
        assert gen._predict(pair["input"]) == pair["output"]
        for rival in gen.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]


def test_overlap_witness_overwrites_original_clue_in_first_appearance_order():
    grid = [[8,0,0,0,6], [0,0,2,6,0], [0,0,0,0,0],
            [0,0,0,0,2], [0,0,8,0,0]]
    expected = [[8,8,8,6,6], [8,0,2,2,2], [8,0,2,0,2],
                [8,0,2,2,2], [8,8,8,0,0]]
    assert gen._predict(grid) == expected
    for name in ("completion_order", "restore_clues", "positive_diagonal_only", "min_side_three"):
        assert gen.LESSON_COMPETITORS[name](grid) != expected
