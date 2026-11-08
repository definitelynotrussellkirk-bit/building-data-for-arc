from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.c5f62271ea44.generator")
TASK_ID = "c5f62271ea44"


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_all_canonical_pairs_are_accepted_and_solved_without_mutation():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(original) == []
        assert GEN.strict_canonical_like(original) == []
        assert GEN.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_all_eight_d4_symmetries_are_exactly_observable():
    outputs = {}
    for index, symmetry in enumerate(GEN.SYMMETRIES):
        grid = GEN.generate(
            8100 + index,
            index,
            difficulty="hard",
            symmetry=symmetry,
            profile_kind="canonical_1",  # non-square panel exposes axis swaps
            key_side="top",
        )
        observed = GEN.observe_overrides(grid)
        assert {key: observed[key] for key in ("symmetry", "profile_kind", "key_side")} == {
            "symmetry": symmetry,
            "profile_kind": "canonical_1",
            "key_side": "top",
        }
        assert GEN.self_check(grid, meta={"overrides": observed}) == []
        assert GEN.strict_canonical_like(grid) == []
        outputs[symmetry] = GEN.rule_mirror(grid)

    # Axis-swapping transforms must rotate 9x10 to 10x9; preserving transforms
    # keep 9x10. This protects against silently collapsing D4 to four flips.
    swapping = {"transpose", "anti_transpose", "rot_cw", "rot_ccw"}
    for name, output in outputs.items():
        expected_shape = (10, 9) if name in swapping else (9, 10)
        assert (len(output), len(output[0])) == expected_shape


def test_profile_and_key_side_axes_are_exact_and_unknown_overrides_fail_closed():
    for index, profile in enumerate(GEN.PROFILE_KINDS):
        grid = GEN.generate(9200 + index, index, profile_kind=profile, key_side="right")
        observed = GEN.observe_overrides(grid)
        assert observed["profile_kind"] == profile
        assert observed["key_side"] == "right"

    for index, side in enumerate(GEN.KEY_SIDES):
        grid = GEN.generate(9300 + index, index, key_side=side, symmetry="rot_cw")
        assert GEN.observe_overrides(grid)["key_side"] == side

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="silent_alias")
    with pytest.raises(ValueError, match="symmetry must be"):
        GEN.generate(1, 0, symmetry="rotate_45")


def test_structural_mutations_that_recreate_old_shortcuts_are_rejected():
    grid = GEN.generate(
        444,
        3,
        difficulty="medium",
        profile_kind="canonical_0",
        key_side="bottom",
        symmetry="transpose",
    )
    analysis = GEN._analyze(grid)
    assert analysis["errors"] == []

    # Old generator emitted four key dots. Reinsert blue at the missing key corner.
    four_dot_key = copy.deepcopy(grid)
    kr0, kc0, kr1, kc1 = analysis["key_box"]
    occupied = {(r, c) for r, c, _ in analysis["outside"]}
    missing = next(p for p in ((kr0, kc0), (kr0, kc1), (kr1, kc0), (kr1, kc1)) if p not in occupied)
    four_dot_key[missing[0]][missing[1]] = 1
    assert GEN.self_check(four_dot_key)

    # Remove one real key dot: the signature can no longer encode four corners.
    two_dot_key = copy.deepcopy(grid)
    r, c, _ = analysis["outside"][0]
    two_dot_key[r][c] = 0
    assert GEN.self_check(two_dot_key)

    # Punch a background hole through the solid panel grammar.
    hollow_panel = copy.deepcopy(grid)
    pr0, pc0, _, _ = analysis["panel_box"]
    hollow_panel[pr0 + 2][pc0 + 2] = 0
    assert any("holes" in error for error in GEN.self_check(hollow_panel))

    # Erase the asymmetric body entirely: corner-only scenes are not legal lessons.
    corner_only = copy.deepcopy(grid)
    texture = analysis["texture_color"]
    for rr, row in enumerate(corner_only):
        for cc, value in enumerate(row):
            if value == texture:
                corner_only[rr][cc] = 1 if pr0 <= rr <= analysis["panel_box"][2] and pc0 <= cc <= analysis["panel_box"][3] else value
    assert GEN.self_check(corner_only)


def test_every_four_consecutive_scheduled_demos_identify_the_lesson():
    for start in range(len(GEN.SYMMETRIES)):
        demos = [
            _pair(GEN.generate(seed=77, sample_index=start + offset, difficulty="medium"))
            for offset in range(GEN.EXAMPLES_NEEDED)
        ]
        query_grid = GEN.generate(
            seed=77,
            sample_index=start + GEN.EXAMPLES_NEEDED,
            difficulty="medium",
        )
        assert GEN.lesson_identifiable(demos, _pair(query_grid)) == []
        for rival in GEN.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_negative_recombination_is_rejected():
    grid = GEN.generate(5150, 5, difficulty="hard", key_side="left")
    analysis = GEN._analyze(grid)
    bad = copy.deepcopy(grid)
    # Recolor one key dot with the unrelated body color. Marginals remain ARC-like,
    # but the panel/key relational signature is impossible.
    r, c, _ = analysis["outside"][0]
    bad[r][c] = analysis["texture_color"]
    assert GEN.self_check(bad)
    assert GEN.strict_canonical_like(bad)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(seed=321, sample_index=5, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(seed=321, sample_index=5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(seed=321, sample_index=5, difficulty="hard") == second


def test_fixed_episode_positions_do_not_determine_the_answer_transform():
    """A default 3-demo query must not always be clockwise rotation."""
    for index in range(8):
        counts = {}
        for seed in range(128):
            name = GEN.schedule_profile(seed, index, 'medium')
            counts[name] = counts.get(name, 0) + 1
        assert set(counts) == set(GEN.SYMMETRIES), (index, counts)
        assert max(counts.values()) <= 40, (index, counts)


def test_seeded_schedule_keeps_all_eight_transforms_and_every_lesson_window():
    swapping = {'transpose', 'anti_transpose', 'rot_cw', 'rot_ccw'}
    quarter_turns = {'rot_cw', 'rot_ccw'}
    period = GEN.LESSON_SCHEDULE_PERIOD
    orders = set()
    for seed in range(64):
        order = tuple(GEN.schedule_profile(seed, i, 'medium') for i in range(period))
        orders.add(order)
        assert set(order) == set(GEN.SYMMETRIES)
        assert order == tuple(GEN.schedule_profile(seed, i + period, 'hard') for i in range(period))
        for start in range(period):
            window = {order[(start + j) % period] for j in range(4)}
            # The strengthened teaching cycle repeats quarter turns to refute
            # inverse mapping in every query rotation. Four demos still expose
            # at least three transforms, as required by the lesson contract.
            assert len(window) >= 3
            assert window & swapping and window - swapping
            assert window & quarter_turns
    assert len(orders) >= 32


def test_default_sampling_reaches_disconnected_bodies_and_canonical_key_extents():
    """Coverage must be measured on geometric roles, not just shape/palette."""
    connected = set()
    reached = set()
    for seed in range(256):
        grid = GEN.generate(seed, seed % 8, difficulty='medium')
        a = GEN._analyze(grid)
        connected.add(GEN._connected(set(a['body_cells'])))
        r0, c0, r1, c1 = a['key_box']
        reached.add((r1 - r0 + 1, c1 - c0 + 1))
    assert connected == {False, True}, connected
    assert any(max(span) > 5 for span in reached), reached
    for pair in canonical_pairs(TASK_ID):
        a = GEN._analyze(pair['input'])
        r0, c0, r1, c1 = a['key_box']
        support = GEN._key_span_options(a['height'], a['width'], a['panel_h'],
                                        a['panel_w'], a['key_side'], 'extended')
        assert (r1 - r0 + 1, c1 - c0 + 1) in support


@pytest.mark.parametrize('profile', GEN.PROFILE_KINDS)
@pytest.mark.parametrize('side', GEN.KEY_SIDES)
@pytest.mark.parametrize('body_kind', ['connected', 'fragmented'])
@pytest.mark.parametrize('key_extent', ['compact', 'extended'])
def test_new_geometry_axes_are_observable_and_jointly_feasible(profile, side, body_kind, key_extent):
    requested = dict(profile_kind=profile, key_side=side,
                     body_kind=body_kind, key_extent=key_extent)
    for difficulty in ['easy', 'medium', 'hard']:
        grid = GEN.generate(1867, 3, difficulty=difficulty, **requested)
        a = GEN._analyze(grid)
        assert a['errors'] == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN._connected(set(a['body_cells'])) == (body_kind == 'connected')
        r0, c0, r1, c1 = a['key_box']
        assert (max(r1 - r0 + 1, c1 - c0 + 1) > 5) == (key_extent == 'extended')
        observed = GEN.observe_overrides(grid)
        assert all(observed[k] == v for k, v in requested.items())
        assert GEN.self_check(grid, meta={'overrides': requested}) == []


def test_new_geometry_axes_fail_closed_and_check_mismatched_metadata():
    for overrides in ({'body_kind': 'missing'}, {'key_extent': 'infinite'}):
        with pytest.raises(ValueError):
            GEN.generate(0, 0, **overrides)
    grid = GEN.generate(17, 2, body_kind='fragmented', key_extent='extended')
    errors = GEN.self_check(grid, meta={'overrides': {'body_kind': 'connected', 'key_extent': 'compact'}})
    assert any('body_kind' in e for e in errors)
    assert any('key_extent' in e for e in errors)


def test_main_draw_context_is_last_and_records_every_exact_axis():
    # The shared override checker inspects captured_contexts[-1]. A schedule
    # helper must not leave a later, empty context that hides the real draws.
    from puzzle_generators.base import set_ctx_observer
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        GEN.generate(0, 0, difficulty='medium')
    finally:
        set_ctx_observer(None)
    assert contexts
    assert set(GEN.AXES) <= set(contexts[-1].recorded_draws())
