from __future__ import annotations

import copy
import hashlib
import importlib
import random
import json

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.9c0ccdf0d414.generator"
)
TASK_ID = "9c0ccdf0d414"
ROOT = find_root(__file__)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_rows():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _canonical_programs():
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    return programs


def test_rule_hash_and_python_mirror_match_every_labeled_canonical_pair():
    rows = _canonical_rows()
    programs = _canonical_programs()
    assert rows and programs
    assert {GEN.RULE_HASH} == {
        _normalized_hash(program) for program in programs
    } == {"559cd5677fd5"}
    for pair in rows:
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_control_surface_is_small_explicit_and_repaired():
    assert GEN.VERSION == "2.0.0"
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_motifs",
        "palette_kind",
        "position_style",
    }
    assert GEN.EXAMPLES_NEEDED == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "omit_tl",
        "omit_tr",
        "omit_bl",
        "omit_br",
        "all_four",
    )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draws_are_lossless_one_object_per_selected_quadrant(difficulty):
    seen_counts = set()
    seen_profiles = set()
    for sample_index in range(25):
        grid = GEN.generate(7001, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        analysis = GEN.analyze_grid(grid)
        seen_counts.add(analysis["n_motifs"])
        seen_profiles.add(GEN.schedule_profile(7001, sample_index, difficulty))
        assert len(analysis["quadrants"]) == analysis["n_motifs"]
        assert len(set(analysis["quadrants"])) == analysis["n_motifs"]
        output = GEN.rule_mirror(grid)
        assert {value for row in grid for value in row if value} == {
            value for row in output for value in row if value
        }
        assert GEN.strict_canonical_like(grid) == []
    assert seen_counts == {3, 4}
    assert seen_profiles == set(GEN.SCHEDULE_PROFILES)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_exact_override_is_recoverable_from_returned_pixels(difficulty):
    case = 0
    for grid_h in (8, 14):
        for grid_w in (8, 14):
            for n_motifs in (3, 4):
                for palette_kind in GEN.PALETTE_KINDS:
                    for position_style in GEN.POSITION_STYLES:
                        overrides = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_motifs": n_motifs,
                            "palette_kind": palette_kind,
                            "position_style": position_style,
                        }
                        grid = GEN.generate(
                            8100 + case,
                            case,
                            difficulty=difficulty,
                            **overrides,
                        )
                        observed = GEN.observe_overrides(grid)
                        assert observed == overrides
                        assert GEN.self_check(
                            grid,
                            difficulty=difficulty,
                            meta={"overrides": overrides},
                        ) == []
                        case += 1


@pytest.mark.parametrize("bad", [True, False, 8.0, "8", -1])
def test_invalid_integer_scalars_reject_loudly(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, grid_h=bad)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, n_motifs=bad)


def test_invalid_calls_and_enum_overrides_reject_loudly():
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.generate(0, True)
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(0, 0, bogus_axis=1)
    with pytest.raises((TypeError, ValueError), match="palette_kind"):
        GEN.generate(0, 0, palette_kind="unknown")
    with pytest.raises((TypeError, ValueError), match="position_style"):
        GEN.generate(0, 0, position_style="random")


def test_position_style_changes_translation_but_not_normalized_answer():
    common = {
        "grid_h": 12,
        "grid_w": 13,
        "n_motifs": 4,
        "palette_kind": "mixed",
    }
    outer = GEN.generate(123, 9, position_style="outer", **common)
    inner = GEN.generate(123, 9, position_style="inner", **common)
    assert outer != inner
    assert GEN.rule_mirror(outer) == GEN.rule_mirror(inner)
    assert GEN.observe_overrides(outer)["position_style"] == "outer"
    assert GEN.observe_overrides(inner)["position_style"] == "inner"


def test_every_five_pair_window_covers_profiles_and_rotation_safe_rival_refutation():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            pairs = []
            profiles = []
            for offset in range(5):
                index = start + offset
                grid = GEN.generate(5050, index, difficulty=difficulty)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
                profiles.append(GEN.schedule_profile(5050, index, difficulty))
            assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
            for query_index in range(5):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for rival in GEN.LESSON_COMPETITORS.values():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    )


def test_declared_canonical_shortcuts_fit_canonical_and_generated_witnesses_refute():
    canonical = _canonical_rows()
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical), name

    fired = {name: False for name in GEN.WITNESS_RIVALS}
    for sample_index in range(10):
        grid = GEN.generate(9090, sample_index, difficulty="medium")
        for name in fired:
            if GEN.SEMANTIC_WITNESSES[name](grid):
                fired[name] = True
                expected = GEN.rule_mirror(grid)
                assert any(
                    GEN.SEMANTIC_RIVALS[rival_name](grid) != expected
                    for rival_name in GEN.WITNESS_RIVALS[name]
                )
    assert all(fired.values()), fired


def test_self_check_rejects_known_semantic_impostors():
    blank = [[0] * 8 for _ in range(8)]

    duplicate_quadrant = copy.deepcopy(blank)
    for color, cells in {
        1: [(0, 0), (0, 1), (1, 0)],
        2: [(1, 2), (1, 3), (2, 2)],
        3: [(0, 6), (0, 7), (1, 7)],
        4: [(6, 0), (7, 0), (7, 1)],
    }.items():
        for row, col in cells:
            duplicate_quadrant[row][col] = color

    repeated_color = copy.deepcopy(blank)
    for cells in (
        [(0, 0), (0, 1), (1, 0)],
        [(0, 6), (0, 7), (1, 7)],
        [(6, 0), (7, 0), (7, 1)],
    ):
        for row, col in cells:
            repeated_color[row][col] = 2

    too_small = copy.deepcopy(blank)
    for color, point in zip((1, 2, 3), ((0, 0), (0, 7), (7, 0))):
        too_small[point[0]][point[1]] = color

    cases = {
        "blank": blank,
        "duplicate_quadrant": duplicate_quadrant,
        "repeated_color": repeated_color,
        "too_small": too_small,
    }
    assert all(GEN.self_check(grid) for grid in cases.values()), {
        name: GEN.self_check(grid) for name, grid in cases.items()
    }


def test_deterministic_fresh_returns_and_global_random_state_is_untouched():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(44, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(44, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
