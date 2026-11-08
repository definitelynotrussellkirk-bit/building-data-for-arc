"""Focused semantic, schedule, and override tests for fae242ae157d."""
from __future__ import annotations

import hashlib
import importlib
import itertools
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "fae242ae157d"
ROOT = find_root(__file__)


GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _erase_component(grid, cells):
    result = [row[:] for row in grid]
    for row, col in cells:
        result[row][col] = 0
    return result


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    digest = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert digest == GENERATOR.RULE_HASH == "ce7e86577c99"

    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = [values[:] for values in pair["input"]]
        snapshot = [values[:] for values in source]
        assert GENERATOR.self_check(source) == []
        assert GENERATOR.strict_canonical_like(source) == []
        assert GENERATOR.rule_mirror(source) == pair["output"]
        assert source == snapshot
        observed = GENERATOR.observe_overrides(source)
        assert observed["scene_profile"] in GENERATOR.CANONICAL_PROFILES
        assert observed["color_mode"] == "distinct"
        assert observed["scan_order"] == "ascending"


def test_every_exact_override_combination_is_observable_in_every_band():
    cases = itertools.product(
        GENERATOR.SCENE_PROFILES,
        GENERATOR.COLOR_MODES,
        GENERATOR.SCAN_ORDERS,
    )
    case_values = list(cases)
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for case_index, (profile, color_mode, scan_order) in enumerate(case_values):
            overrides = {
                "scene_profile": profile,
                "color_mode": color_mode,
                "scan_order": scan_order,
            }
            grid = GENERATOR.generate(
                10_000 + band_index * 1_000 + case_index,
                29 * case_index + 7,
                difficulty=band,
                **overrides,
            )
            assert GENERATOR.self_check(grid) == []
            assert GENERATOR.observe_overrides(grid) == overrides


def test_200_per_band_linked_semantic_census_and_disjoint_stability():
    summaries = []
    for seed_base in (100_000, 700_000):
        run = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            colors = Counter()
            scans = Counter()
            witness_hits = Counter()
            strict = 0
            inputs = set()
            outputs = set()
            for offset in range(200):
                seed = seed_base + band_index * 10_000 + offset
                sample_index = offset + 3 * (seed % 97)
                grid = GENERATOR.generate(seed, sample_index, difficulty=band)
                assert GENERATOR.self_check(grid) == []
                observed = GENERATOR.observe_overrides(grid)
                profiles[observed["scene_profile"]] += 1
                colors[observed["color_mode"]] += 1
                scans[observed["scan_order"]] += 1
                strict += not bool(GENERATOR.strict_canonical_like(grid))
                for name, witness in GENERATOR.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += bool(witness(grid))
                output = GENERATOR.rule_mirror(grid)
                inputs.add(json.dumps(grid, separators=(",", ":")))
                outputs.add(json.dumps(output, separators=(",", ":")))

            assert sum(profiles.values()) == 200
            assert sum(colors.values()) == 200
            assert sum(scans.values()) == 200
            assert set(colors) == set(GENERATOR.COLOR_MODES)
            assert set(scans) == set(GENERATOR.SCAN_ORDERS)
            assert any(name in profiles for name in GENERATOR.CANONICAL_PROFILES)
            assert set(GENERATOR.GENERAL_PROFILES).issubset(profiles)
            assert strict >= 55
            assert min(witness_hits.values()) > 0
            assert len(inputs) >= 195
            assert len(outputs) >= 190
            run[band] = {
                "strict": strict,
                "unique_inputs": len(inputs),
                "unique_outputs": len(outputs),
                "colors": colors,
                "scans": scans,
            }
        summaries.append(run)

    for band in ("easy", "medium", "hard"):
        assert abs(summaries[0][band]["strict"] - summaries[1][band]["strict"]) <= 2
        assert abs(
            summaries[0][band]["unique_outputs"]
            - summaries[1][band]["unique_outputs"]
        ) <= 10


def test_every_three_demo_window_is_identifiable():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(9):
            pairs = []
            for offset in range(4):
                grid = GENERATOR.generate(
                    900_000 + band_index * 100 + start,
                    start + offset,
                    difficulty=band,
                )
                pairs.append({"input": grid, "output": GENERATOR.rule_mirror(grid)})
            assert GENERATOR.lesson_identifiable(pairs[:3], pairs[3]) == []
            assert {
                GENERATOR.schedule_profile(0, start + offset, band)
                for offset in range(3)
            } == set(GENERATOR.SCHEDULE_PROFILES)


def test_targeted_impostors_and_negative_recombination_are_rejected():
    valid = GENERATOR.generate(
        424_242,
        0,
        difficulty="medium",
        scene_profile="canonical_10x12",
        color_mode="distinct",
        scan_order="ascending",
    )
    analysis = GENERATOR._analysis(valid)
    ranked = sorted(analysis["components"], key=len)

    blank = [[0 for _ in row] for row in valid]
    two_objects = _erase_component(valid, ranked[2])

    polychrome = [row[:] for row in valid]
    row, col = ranked[0][0]
    polychrome[row][col] = next(
        color for color in range(1, 10) if color != valid[row][col]
    )

    duplicate_two_colours = [row[:] for row in valid]
    first_color = valid[ranked[0][0][0]][ranked[0][0][1]]
    for row, col in ranked[1]:
        duplicate_two_colours[row][col] = first_color

    hidden_transform = [row[:] for row in valid]
    for rank, cells in enumerate(ranked):
        for row, col in cells:
            hidden_transform[row][col] = 2 + rank

    for name, impostor in {
        "blank": blank,
        "two_objects": two_objects,
        "polychrome_object": polychrome,
        "duplicate_two_colours": duplicate_two_colours,
        "hidden_transform": hidden_transform,
    }.items():
        assert GENERATOR.self_check(impostor), name

    # The replacement colour is absent from every remaining scene part; this
    # is a true negative recombination rather than a copied cue elsewhere.
    replacement = 9
    while replacement in {value for row in valid for value in row}:
        replacement -= 1
    recombined = [row[:] for row in valid]
    for row, col in ranked[1]:
        recombined[row][col] = replacement
    # All-distinct remains lawful; making only two objects share that absent
    # replacement creates the malformed recombination the checker must reject.
    for row, col in ranked[2]:
        recombined[row][col] = replacement
    assert GENERATOR.self_check(recombined)


def test_declared_rivals_have_generated_counterexamples():
    witnesses = {
        "generalized_size_triplet": GENERATOR.generate(7, 1, difficulty="medium"),
        "scan_order_conflict": GENERATOR.generate(8, 1, difficulty="medium"),
        "rank_palette_permuted": GENERATOR.generate(9, 1, difficulty="medium"),
        "ascending_differs_from_descending": GENERATOR.generate(10, 0, difficulty="medium"),
    }
    for witness_name, grid in witnesses.items():
        expected = GENERATOR.rule_mirror(grid)
        assert GENERATOR.SEMANTIC_WITNESSES[witness_name](grid)
        for rival_name in GENERATOR.WITNESS_RIVALS[witness_name]:
            assert GENERATOR.SEMANTIC_RIVALS[rival_name](grid) != expected


def test_determinism_fresh_returns_global_rng_and_invalid_requests():
    random.seed(20260726)
    state = random.getstate()
    first = GENERATOR.generate(73, 109, difficulty="hard")
    assert random.getstate() == state
    second = GENERATOR.generate(73, 109, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GENERATOR.generate(73, 109, difficulty="hard") == second

    with pytest.raises(TypeError, match="unknown override"):
        GENERATOR.generate(1, 2, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GENERATOR.generate(1, 2, difficulty="nightmare")
    with pytest.raises(ValueError):
        GENERATOR.generate(1, 2, scene_profile="not_a_profile")


def _legacy_schedule_cue_output(grid):
    """Shortcut supported by the old profile/mode/scan coupling."""
    analysis = GENERATOR._analysis(grid)
    assert analysis["errors"] == []
    scan_components = sorted(analysis["components"], key=min)
    if analysis["scene_profile"] in GENERATOR.CANONICAL_PROFILES:
        ranks_at_scan_position = (0, 1, 2)
    elif analysis["scene_profile"] == "general_11x14":
        ranks_at_scan_position = (2, 1, 0)
    else:
        assert analysis["scene_profile"] == "general_13x16"
        ranks_at_scan_position = (1, 2, 0)
    output = [[0 for _ in row] for row in grid]
    for cells, rank in zip(scan_components, ranks_at_scan_position):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def test_six_slot_schedule_breaks_exposed_schedule_cue_shortcut():
    seed = 20261007
    records = []
    for sample_index in range(6):
        grid = GENERATOR.generate(seed, sample_index, difficulty="medium")
        analysis = GENERATOR._analysis(grid)
        records.append((grid, analysis))

    canonical = [
        analysis
        for _, analysis in records
        if analysis["scene_profile"] in GENERATOR.CANONICAL_PROFILES
    ]
    assert {analysis["scan_order"] for analysis in canonical} == set(
        GENERATOR.SCAN_ORDERS
    )
    assert {tuple(sorted(analysis["sizes"])) for analysis in canonical} != {
        (4, 5, 6)
    }

    scans_by_color_mode = {
        mode: {
            analysis["scan_order"]
            for _, analysis in records
            if analysis["color_mode"] == mode
        }
        for mode in GENERATOR.COLOR_MODES
    }
    assert len(scans_by_color_mode["distinct"]) >= 2
    assert len(scans_by_color_mode["rank_permuted"]) >= 2

    # Every possible three-demo window must already contradict the old shortcut,
    # rather than relying on a later query to expose it.
    for start in range(6):
        demos = [
            GENERATOR.generate(seed, start + offset, difficulty="medium")
            for offset in range(3)
        ]
        assert any(
            _legacy_schedule_cue_output(grid) != GENERATOR.rule_mirror(grid)
            for grid in demos
        )


def test_schedule_cue_shortcut_is_declared_and_refuted_in_every_demo_window():
    rival_name = "rank from scene dimensions and top-left position"
    assert rival_name in GENERATOR.SEMANTIC_RIVALS
    rival = GENERATOR.SEMANTIC_RIVALS[rival_name]

    seed = 20261007
    for start in range(6):
        demos = [
            GENERATOR.generate(seed, start + offset, difficulty="medium")
            for offset in range(3)
        ]
        assert any(rival(grid) != GENERATOR.rule_mirror(grid) for grid in demos)


def test_schedule_cue_counterexample_is_a_declared_witness():
    witness_name = "schedule_cue_decoupled"
    rival_name = "rank from scene dimensions and top-left position"

    assert witness_name in GENERATOR.SEMANTIC_WITNESSES
    assert rival_name in GENERATOR.WITNESS_RIVALS[witness_name]

    witnessed = [
        GENERATOR.generate(20261007, sample_index, difficulty="medium")
        for sample_index in range(6)
        if GENERATOR.SEMANTIC_WITNESSES[witness_name](
            GENERATOR.generate(20261007, sample_index, difficulty="medium")
        )
    ]
    assert witnessed
    for grid in witnessed:
        assert (
            GENERATOR.SEMANTIC_RIVALS[rival_name](grid)
            != GENERATOR.rule_mirror(grid)
        )


def test_feature_presence_witnesses_are_declared_as_branches():
    feature_only = {
        "canonical_anchor",
        "descending_scan_order",
        "mixed_scan_order",
        "distinct_input_colours",
        "monochrome_input",
    }
    assert feature_only <= set(GENERATOR.BRANCH_WITNESSES)
    assert feature_only.isdisjoint(GENERATOR.WITNESS_RIVALS)
