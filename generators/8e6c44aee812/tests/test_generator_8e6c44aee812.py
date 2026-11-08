from __future__ import annotations

import copy
import json
import random
from collections import Counter

import pytest

from arc_repl.racket_bridge import RacketBridge
from arcpuzzles import Catalog
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

ROOT = find_root(__file__)
TASK_ID = "8e6c44aee812"
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
DATA_ROOT = canonical_path(ROOT).parent.parent
BASE_PATH = DATA_ROOT / "base/solutions/training/539a4f51__8e6c44aee812.json"
CATALOG = Catalog(root=ROOT)
BANDS = ("easy", "medium", "hard")


def _canonical_rule_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]
    sources = [row["program_solution"] for row in records if row.get("task_id") == TASK_ID]
    assert len(sources) == 1
    return sources[0]


def _reference_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    before = copy.deepcopy(grids)
    report = CATALOG.apply(TASK_ID, grids, timeout=120)
    assert grids == before
    results = report["results"]
    assert len(results) == len(grids)
    assert all(row["error"] is None and row["valid_output"] for row in results)
    return [row["output"] for row in results]


def _purity_expression(source: str, first_grid, second_grid) -> str:
    def literal(grid) -> str:
        return "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"

    # Reuse one rule closure and the same original grid object for A, B, A.
    # Returning that object preserves the original in-runtime mutation check.
    return f"""(let* ((rule! (lambda (f) f))
                      (transform {source})
                      (original '{literal(first_grid)})
                      (other '{literal(second_grid)})
                      (first (transform original))
                      (ignored (transform other))
                      (again (transform original)))
                 (list first again original))"""


def _pair(seed: int, sample_index: int, band: str) -> dict[str, list[list[int]]]:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN._expected_output(grid)}


def _staircase(diagonal: list[int]) -> list[list[int]]:
    return [
        [diagonal[max(row, col)] for col in range(len(diagonal))]
        for row in range(len(diagonal))
    ]


def test_rule_hash_authorities_and_all_canonical_pairs_are_exact() -> None:
    source = _canonical_rule_source()
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = base["racket_target"]

    assert GEN.VERSION == "3.1.0"
    assert GEN.RULE_HASH == CATALOG.describe(TASK_ID)["rule_hash"] == "2f49d92711a1"
    assert target["target_code"] == source
    assert target["raw_code"] == source
    assert ";; Each nested L-band" in source
    assert ";; Trailing zero bands are padding" in source
    assert ";; Continue the staircase" in source

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._expected_output(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_canonical_racket_rule_is_exact_input_pure_and_reentrant() -> None:
    source = _canonical_rule_source()
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    before = copy.deepcopy(pairs)
    outputs = _reference_outputs([pair["input"] for pair in pairs])
    for pair, actual in zip(pairs, outputs, strict=True):
        assert actual == pair["output"] == GEN._expected_output(pair["input"])
    assert pairs == before

    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        a_b_a = bridge.eval_text(
            _purity_expression(source, pairs[0]["input"], pairs[1]["input"])
        )
        assert a_b_a[0] == pairs[0]["output"]
        assert a_b_a[1] == pairs[0]["output"]
        assert a_b_a[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


def test_short_complex_repeats_have_real_reference_bound_witnesses() -> None:
    diagonals = [[1, 1, 2, 2], [1, 2, 1, 2]]
    grids = [_staircase(diagonal + padding)
             for diagonal in diagonals for padding in ([], [0])]
    # AABB is reference-lawful but outside the original three-run complex
    # teaching grammar. It is unnecessary for exact period-four support.
    for grid in grids[:2]:
        assert GEN.self_check(grid)
    for grid in grids[2:]:
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid)["pattern_class"] == "complex_repeat"
    for grid, official in zip(grids, _reference_outputs(grids), strict=True):
        assert official == GEN._expected_output(grid)
        if GEN.self_check(grid) == []:
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != official
                       for name in GEN.WITNESS_RIVALS["pattern_complex_repeat"])
    # ABAB and AB have the same continuation: merely observing a repeat must
    # not be reported as a disagreement with either of these two rivals.
    for grid in grids[2:]:
        assert GEN.SEMANTIC_RIVALS["first_run_per_color"](grid) == GEN._expected_output(grid)
        assert GEN.SEMANTIC_RIVALS["deduplicate_active_diagonal"](grid) == GEN._expected_output(grid)
        for name in ("first_color_exempt_first_run", "other_colors_exempt_first_run"):
            assert GEN.SEMANTIC_RIVALS[name](grid) != GEN._expected_output(grid)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(1234, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(1234, 9, difficulty="hard")
    assert random.getstate() == state

    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0 if first[0][0] else 9
    assert second == GEN.generate(1234, 9, difficulty="hard")


@pytest.mark.parametrize("band", BANDS)
def test_exact_override_boundaries_are_observable_and_invalid_values_reject(
    band: str,
) -> None:
    case_index = 0
    for period in (4, 9):
        for padding in GEN.PADDING_MODES:
            for pattern_class in GEN.PATTERN_CLASSES:
                overrides = {
                    "period": period,
                    "padding": padding,
                    "pattern_class": pattern_class,
                }
                grid = GEN.generate(
                    8100 + case_index,
                    900 + case_index,
                    difficulty=band,
                    **overrides,
                )
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == overrides
                case_index += 1

    for period in range(4, 10):
        grid = GEN.generate(
            9100 + period,
            period,
            difficulty=band,
            period=period,
            padding="none",
            pattern_class="distinct",
        )
        assert GEN.observe_overrides(grid)["period"] == period

    with pytest.raises(ValueError):
        GEN.generate(1, 1, difficulty=band, period=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 1, difficulty=band, period=10)
    with pytest.raises(ValueError):
        GEN.generate(1, 1, difficulty=band, padding="two")
    with pytest.raises(ValueError):
        GEN.generate(1, 1, difficulty=band, pattern_class="random")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 1, difficulty=band, texture="checker")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        GEN.generate(1, 1, difficulty="expert")


def test_self_check_rejects_targeted_task_specific_impostors() -> None:
    valid = GEN.generate(
        717,
        5,
        difficulty="medium",
        period=5,
        padding="none",
        pattern_class="distinct",
    )

    broken_band = copy.deepcopy(valid)
    broken_band[0][1] = next(
        color for color in range(1, 10) if color != broken_band[0][1]
    )

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()

    non_square = [row[:-1] for row in valid]
    invalid = {
        "broken staircase band": broken_band,
        "ragged": ragged,
        "non-square": non_square,
        "internal zero": _staircase([1, 0, 2, 3, 4]),
        "monochrome active diagonal": _staircase([2, 2, 2, 2]),
        "two trailing zero bands": _staircase([1, 2, 3, 4, 0, 0]),
        "period below four": _staircase([1, 2, 3]),
        "boolean ARC cell": [[False if (r, c) == (0, 0) else valid[r][c] for c in range(5)] for r in range(5)],
    }
    for name, grid in invalid.items():
        assert GEN.self_check(grid), name


def test_strict_linked_census_is_count_backed_for_200_draws_per_band() -> None:
    for band in BANDS:
        observations: list[dict[str, object]] = []
        strict_hits = 0
        generated: list[list[list[int]]] = []
        for sample_index in range(200):
            grid = GEN.generate(
                100_000 + 17 * sample_index,
                sample_index,
                difficulty=band,
            )
            assert GEN.self_check(grid) == []
            generated.append(grid)
            observations.append(GEN.observe_overrides(grid))
            strict_hits += int(GEN.strict_canonical_like(grid) == [])

        assert len(generated) == 200
        assert strict_hits == 100
        assert Counter(item["padding"] for item in observations) == {
            "one": 100,
            "none": 100,
        }
        assert Counter(item["pattern_class"] for item in observations) == {
            "distinct": 67,
            "prefix_run": 67,
            "complex_repeat": 66,
        }
        assert sum(int(item["period"]) > 5 for item in observations) == 100
        assert sum(len(grid) == 5 for grid in generated) == 100
        assert sum(len(grid) != 5 for grid in generated) == 100
        assert len({json.dumps(grid, separators=(",", ":")) for grid in generated}) >= 190


def test_disjoint_seed_stability_and_variation_census() -> None:
    for band in BANDS:
        for sample_index in range(12):
            seed = 200_000 + sample_index
            assert GEN.generate(seed, sample_index, difficulty=band) == GEN.generate(
                seed, sample_index, difficulty=band
            )

        for sample_index in (0, 1, 2, 3):
            variants = {
                json.dumps(
                    GEN.generate(seed, sample_index, difficulty=band),
                    separators=(",", ":"),
                )
                for seed in range(300_000, 300_030)
            }
            assert len(variants) >= 20, (band, sample_index, len(variants))


def test_every_sliding_five_demo_lesson_refutes_all_named_competitors() -> None:
    demo_count = GEN.EXAMPLES_NEEDED
    for band in BANDS:
        for start in range(24):
            demos = [
                _pair(410_000 + start, start + offset, band)
                for offset in range(demo_count)
            ]
            query = _pair(410_000 + start, start + demo_count, band)
            assert GEN.lesson_identifiable(demos, query) == [], (band, start)

            observed = [GEN.observe_overrides(demo["input"]) for demo in demos]
            assert {item["padding"] for item in observed} == set(GEN.PADDING_MODES)
            # Rich repeat evidence survives every lesson; distinct examples
            # remain a global support requirement checked by the census.
            assert {"prefix_run", "complex_repeat"} <= {item["pattern_class"] for item in observed}
            assert {len(demo["input"]) == 5 for demo in demos} == {False, True}
            assert any(int(item["period"]) > 5 for item in observed)

            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(demo["input"]) != demo["output"] for demo in demos
                ), (band, start, name)


def test_every_semantic_witness_fires_and_has_a_real_rival_disagreement() -> None:
    for band in BANDS:
        grids = [GEN.generate(500_000 + index, index, difficulty=band) for index in range(80)]
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            firing = [grid for grid in grids if witness(grid)]
            assert firing, (band, name)
            for grid in firing:
                official = GEN._expected_output(grid)
                assert any(
                    GEN.SEMANTIC_RIVALS[rival](grid) != official
                    for rival in GEN.WITNESS_RIVALS[name]
                ), (band, name)


def test_negative_recombination_is_rejected_by_distribution_but_oracle_executes() -> None:
    valid = GEN.generate(
        73,
        2,
        difficulty="medium",
        period=5,
        padding="none",
        pattern_class="distinct",
    )
    used = {value for row in valid for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)

    # Recolor only the bottom half of the outer L-band. The diagonal still gives
    # the Racket rule a period, but the scene is no longer one coherent band.
    recombined = copy.deepcopy(valid)
    last = len(recombined) - 1
    for col in range(len(recombined)):
        recombined[last][col] = replacement

    assert GEN.self_check(recombined)
    before = copy.deepcopy(recombined)
    output = _reference_outputs([recombined])[0]
    assert isinstance(output, list) and output
    assert recombined == before
