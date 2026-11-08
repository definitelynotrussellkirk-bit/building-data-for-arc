"""Focused regression tests for generator 3108da8bf9e8."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_generator_3108da8bf9e8", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
AUTHORITY_PATH = (
    REPO_ROOT
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "dc2aa30b__3108da8bf9e8.json"
)


def _canonical_row() -> dict:
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {GEN.TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [*row["train"], *row["test"]]


def _normalized_rule_hash(code: str) -> str:
    normalized = " ".join(code.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def test_rule_hash_and_selected_authority_are_exactly_pinned():
    row = _canonical_row()
    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    canonical = row["program_solution"]
    assert GEN.RULE_HASH == _normalized_rule_hash(canonical) == "05977542b8d5"
    assert authority["racket_target"]["raw_code"] == canonical
    assert authority["racket_target"]["target_code"] == canonical


def test_all_canonical_pairs_are_accepted_and_python_mirror_matches():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("omitted_count", range(10))
def test_omitted_count_override_is_exact_and_observable(difficulty, omitted_count):
    grid = GEN.generate(
        4000 + omitted_count,
        omitted_count,
        difficulty=difficulty,
        omitted_count=omitted_count,
    )
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.observe_overrides(grid) == {"omitted_count": omitted_count}
    assert omitted_count not in GEN._block_one_counts(grid)


def test_invalid_and_unknown_overrides_fail_loudly():
    for value in (-1, 10, True, False, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError), match="omitted_count"):
            GEN.generate(1, 0, omitted_count=value)
    with pytest.raises((KeyError, ValueError), match="unknown override"):
        GEN.generate(1, 0, density="dense")


def test_default_corpus_covers_every_lawful_omission_and_all_bands_are_distinct():
    omissions = set()
    for sample_index in range(80):
        grid = GEN.generate(731, sample_index, difficulty="medium")
        assert GEN.self_check(grid) == []
        omissions.add(GEN.observe_overrides(grid)["omitted_count"])
    assert omissions == set(range(10))

    for sample_index in range(20):
        grids = [
            GEN.generate(991, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) == 3


def test_generated_lessons_refute_named_shortcuts_and_are_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(1451, sample_index, difficulty=difficulty)
            official = GEN.rule_mirror(grid)
            demos.append({"input": grid, "output": official})
            for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
                assert predicate(grid), witness_name
                named_rivals = GEN.WITNESS_RIVALS[witness_name]
                assert any(
                    GEN.SEMANTIC_RIVALS[name](copy.deepcopy(grid)) != official
                    for name in named_rivals
                ), witness_name

        query_grid = GEN.generate(
            1451,
            GEN.EXAMPLES_NEEDED,
            difficulty=difficulty,
        )
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []


def test_structural_impostors_are_rejected():
    base = GEN.generate(808, 3, difficulty="medium", omitted_count=4)

    broken_separator = copy.deepcopy(base)
    broken_separator[3][0] = 1
    assert GEN.self_check(broken_separator)

    duplicate_count = copy.deepcopy(base)
    # Copy one complete block over another, creating a duplicate sort key.
    for dr in range(3):
        for dc in range(3):
            duplicate_count[dr][4 + dc] = duplicate_count[dr][dc]
    assert any("unique" in reason for reason in GEN.self_check(duplicate_count))

    foreign_color = copy.deepcopy(base)
    foreign_color[0][0] = 3
    assert any("{1, 2}" in reason for reason in GEN.self_check(foreign_color))

    bool_cell = copy.deepcopy(base)
    bool_cell[0][0] = True
    assert any("literal integers" in reason for reason in GEN.self_check(bool_cell))

    ragged = copy.deepcopy(base)
    ragged[0].pop()
    assert GEN.self_check(ragged)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(998877)
    state = random.getstate()
    first = GEN.generate(2026, 10, difficulty="hard", omitted_count=7)
    assert random.getstate() == state
    second = GEN.generate(2026, 10, difficulty="hard", omitted_count=7)
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9
    assert second == GEN.generate(2026, 10, difficulty="hard", omitted_count=7)


def _rank_order_signature(grid) -> tuple[int, ...]:
    counts = GEN._block_one_counts(grid)
    ranks = {count: rank for rank, count in enumerate(sorted(counts))}
    return tuple(ranks[count] for count in counts)


def _target_rank_order() -> tuple[int, ...]:
    return (6, 7, 8, 3, 4, 5, 0, 1, 2)


def test_difficulty_bands_require_global_ranking_not_band_specific_shortcuts():
    expected_rivals = {"sort_within_macro_rows", "reverse_macro_rows"}
    assert expected_rivals <= set(GEN.SEMANTIC_RIVALS)
    assert expected_rivals <= set(GEN.LESSON_COMPETITORS)
    assert expected_rivals <= set(GEN.CANONICAL_SHORTCUTS)

    target = _target_rank_order()
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(120):
            grid = GEN.generate(8831, sample_index, difficulty=difficulty)
            signature = _rank_order_signature(grid)
            displacement = sum(
                actual != expected for actual, expected in zip(signature, target)
            )
            if difficulty == "easy":
                assert displacement == 4
            elif difficulty == "medium":
                assert 5 <= displacement <= 8
            else:
                assert displacement == 9

            official = GEN.rule_mirror(grid)
            for rival_name in expected_rivals:
                assert GEN.SEMANTIC_RIVALS[rival_name](copy.deepcopy(grid)) != official


def test_each_band_has_multiple_position_maps_instead_of_one_fixed_permutation():
    signatures = {
        difficulty: {
            _rank_order_signature(GEN.generate(1907, sample_index, difficulty=difficulty))
            for sample_index in range(240)
        }
        for difficulty in ("easy", "medium", "hard")
    }
    assert len(signatures["easy"]) >= 150
    assert len(signatures["medium"]) >= 180
    assert len(signatures["hard"]) >= 180


def test_texture_sampler_covers_every_singleton_and_single_hole_position():
    masks_by_count: dict[int, set[tuple[int, ...]]] = {
        count: set() for count in range(10)
    }
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(320):
            grid = GEN.generate(6121, sample_index, difficulty=difficulty)
            for block in GEN._extract_blocks(grid):
                count = GEN._block_count(block)
                mask = tuple(value for row in block for value in row)
                masks_by_count[count].add(mask)

    # Counts 1 and 8 each have exactly nine lawful textures.  Covering all nine
    # catches samplers that permanently reserve a location to manufacture a
    # texture-preservation witness, which leaks an avoidable visual shortcut.
    assert len(masks_by_count[1]) == 9
    assert len(masks_by_count[8]) == 9
    # Interior occupancies should also expose substantial combinatorial support.
    assert len(masks_by_count[2]) >= 30
    assert len(masks_by_count[3]) >= 70
    assert len(masks_by_count[4]) >= 110
    assert len(masks_by_count[5]) >= 110
    assert len(masks_by_count[6]) >= 70
    assert len(masks_by_count[7]) >= 30


def test_shortcut_census_tool_reports_layout_texture_and_lesson_risks():
    tool_path = GENERATOR_PATH.parent / "workspace" / "shortcut_census.py"
    spec = importlib.util.spec_from_file_location("shortcut_census_3108da8bf9e8", tool_path)
    assert spec is not None and spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    report = tool.build_report(GEN, per_band=40, lessons_per_band=12, seed=20261002)
    assert report["schema"] == "arc-generator-shortcut-census-v2"
    assert report["task_id"] == GEN.TASK_ID
    assert report["thresholds_passed"] is True
    assert report["failures"] == []
    for band in ("easy", "medium", "hard"):
        stats = report["bands"][band]
        assert stats["draws"] == 40
        assert stats["shortcut_exact_matches"]["sort_within_macro_rows"] == 0
        assert stats["shortcut_exact_matches"]["reverse_macro_rows"] == 0
        assert stats["unique_position_maps"] > 1
        lesson = report["lessons"][band]
        assert lesson["lessons"] == 12
        assert lesson["fixed_position_survives_all_examples"] == 0


def test_shortcut_census_valid_draws_counts_samples_not_error_messages():
    tool_path = GENERATOR_PATH.parent / "workspace" / "shortcut_census.py"
    spec = importlib.util.spec_from_file_location(
        "shortcut_census_valid_draws_3108da8bf9e8", tool_path
    )
    assert spec is not None and spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    class GeneratorWithBrokenRivals:
        SEMANTIC_RIVALS = {
            **GEN.SEMANTIC_RIVALS,
            "broken_a": lambda _grid: (_ for _ in ()).throw(RuntimeError("a")),
            "broken_b": lambda _grid: (_ for _ in ()).throw(RuntimeError("b")),
        }

        def __getattr__(self, name):
            return getattr(GEN, name)

    report = tool._band_report(
        GeneratorWithBrokenRivals(), "easy", per_band=3, seed=20261002
    )
    assert len(report["errors"]) == 6
    assert report["valid_draws"] == 3


def test_shortcut_census_rejects_collapsed_texture_support():
    tool_path = GENERATOR_PATH.parent / "workspace" / "shortcut_census.py"
    spec = importlib.util.spec_from_file_location(
        "shortcut_census_texture_support_3108da8bf9e8", tool_path
    )
    assert spec is not None and spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    class CollapsedTextureGenerator:
        TASK_ID = GEN.TASK_ID
        VERSION = GEN.VERSION
        SEMANTIC_RIVALS = GEN.SEMANTIC_RIVALS

        def __getattr__(self, name):
            return getattr(GEN, name)

        def generate(self, seed, sample_index, *, difficulty=None, **overrides):
            grid = GEN.generate(
                seed,
                sample_index,
                difficulty=difficulty,
                **overrides,
            )
            for (br, bc), block in zip(GEN.ROW_MAJOR_BLOCKS, GEN._extract_blocks(grid)):
                one_count = GEN._block_count(block)
                values = [2] * (9 - one_count) + [1] * one_count
                GEN._write_block(grid, br, bc, values)
            return grid

    report = tool.build_report(
        CollapsedTextureGenerator(),
        per_band=40,
        lessons_per_band=12,
        seed=20261002,
    )
    assert report["thresholds_passed"] is False
    assert any("texture count" in failure for failure in report["failures"])


def _all_three_groups_of_three() -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Every unlabeled partition of nine macro-positions into three triples."""
    import itertools

    positions = set(range(9))
    partitions = set()
    for first_tail in itertools.combinations(range(1, 9), 2):
        first = (0, *first_tail)
        remaining = positions - set(first)
        second_anchor = min(remaining)
        for second_tail in itertools.combinations(
            sorted(remaining - {second_anchor}), 2
        ):
            second = (second_anchor, *second_tail)
            third = tuple(sorted(remaining - set(second)))
            partitions.add(
                tuple(sorted((tuple(sorted(first)), tuple(sorted(second)), third)))
            )
    result = tuple(sorted(partitions))
    assert len(result) == 280
    return result


def _partition_local_sort_solves(
    signature: tuple[int, ...], partition: tuple[tuple[int, ...], ...]
) -> bool:
    target = _target_rank_order()
    return all(
        {signature[index] for index in group}
        == {target[index] for index in group}
        for group in partition
    )


def test_column_local_sort_is_an_explicit_rival_and_never_solves_a_draw():
    assert "sort_within_macro_columns" in GEN.SEMANTIC_RIVALS
    assert "requires_cross_column_ranking" in GEN.SEMANTIC_WITNESSES
    assert GEN.WITNESS_RIVALS["requires_cross_column_ranking"] == [
        "sort_within_macro_columns"
    ]

    rival = GEN.SEMANTIC_RIVALS["sort_within_macro_columns"]
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(160):
            grid = GEN.generate(32041, sample_index, difficulty=difficulty)
            assert rival(copy.deepcopy(grid)) != GEN.rule_mirror(grid)


def test_easy_four_cycles_touch_every_macro_row_and_column():
    target = _target_rank_order()
    signatures = set()
    for sample_index in range(400):
        grid = GEN.generate(44521, sample_index, difficulty="easy")
        signature = _rank_order_signature(grid)
        signatures.add(signature)
        moved = [
            index
            for index, (actual, expected) in enumerate(zip(signature, target))
            if actual != expected
        ]
        assert len(moved) == 4
        assert {index // 3 for index in moved} == {0, 1, 2}
        assert {index % 3 for index in moved} == {0, 1, 2}
    assert len(signatures) >= 190


def test_no_generated_draw_is_solved_by_any_three_groups_of_three_local_sort():
    partitions = _all_three_groups_of_three()
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(180):
            signature = _rank_order_signature(
                GEN.generate(55001, sample_index, difficulty=difficulty)
            )
            assert not any(
                _partition_local_sort_solves(signature, partition)
                for partition in partitions
            )


def test_shortcut_census_models_the_full_three_group_local_sort_class():
    tool_path = GENERATOR_PATH.parent / "workspace" / "shortcut_census.py"
    spec = importlib.util.spec_from_file_location(
        "shortcut_census_locality_3108da8bf9e8", tool_path
    )
    assert spec is not None and spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    partitions = tool.three_groups_of_three()
    assert len(partitions) == 280

    target = _target_rank_order()
    transposition = list(target)
    transposition[0], transposition[4] = transposition[4], transposition[0]
    assert len(tool.solving_three_group_partitions(tuple(transposition))) == 70

    four_cycle = list(target)
    cycle = (0, 4, 8, 2)
    values = [four_cycle[index] for index in cycle]
    for offset, destination in enumerate(cycle):
        four_cycle[cycle[(offset + 1) % 4]] = values[offset]
    assert tool.solving_three_group_partitions(tuple(four_cycle)) == ()

    report = tool.build_report(GEN, per_band=60, lessons_per_band=18, seed=20261002)
    assert report["schema"] == "arc-generator-shortcut-census-v2"
    assert report["thresholds_passed"] is True
    for band in ("easy", "medium", "hard"):
        assert report["bands"][band]["draws_with_three_group_local_solver"] == 0
        assert report["lessons"][band]["three_group_survives_all_demos"] == 0
