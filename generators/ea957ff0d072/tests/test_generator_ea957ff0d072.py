from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GEN_PATH = ROOT / "generators" / "ea957ff0d072" / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_generator_ea957ff0d072", GEN_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

TASK_ID = "ea957ff0d072"
CANONICAL_PROFILES = {(8, 12, 6), (9, 12, 6), (9, 13, 8)}


def _canonical_row() -> dict:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _grid(rows: list[str] | list[list[int]]) -> list[list[int]]:
    if rows and isinstance(rows[0], str):
        return [[int(value) for value in row] for row in rows]
    return copy.deepcopy(rows)


def _pairs() -> list[dict]:
    row = _canonical_row()
    test_pairs = row["test"] if isinstance(row["test"], list) else [row["test"]]
    pairs = [*row["train"], *test_pairs]
    return [
        {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
        for pair in pairs
    ]


def _normalized_rule_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def _palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})


def _lesson(seed: int, start: int, difficulty: str) -> tuple[list[dict], dict]:
    demos = []
    for offset in range(GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, start + offset, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(
        seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty
    )
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def test_rule_pin_and_every_canonical_pair():
    row = _canonical_row()
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == _normalized_rule_hash(row["program_solution"])
    assert GEN.RULE_HASH == "d849dec31c02"

    for pair in _pairs():
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_four_demo_schedule_teaches_direction_attachment_and_order():
    assert GEN.EXAMPLES_NEEDED == 4
    assert len(GEN.SCHEDULE_PROFILES) == 4

    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            for start in range(4):
                grids = [
                    GEN.generate(seed, start + offset, difficulty=difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                profiles = {
                    GEN.schedule_profile(seed, start + offset, difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                }
                assert profiles == set(GEN.SCHEDULE_PROFILES)
                assert all(GEN.self_check(grid) == [] for grid in grids)
                assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)

                marker_codes = {
                    value
                    for grid in grids
                    for row in grid
                    for value in row
                    if value in (1, 2, 3, 4)
                }
                assert marker_codes == {1, 2, 3, 4}
                assert any(
                    GEN.SEMANTIC_WITNESSES["row_major_order_visible"](grid)
                    for grid in grids
                )
                assert any(
                    GEN.SEMANTIC_WITNESSES[
                        "marker_attachment_color_key_visible"
                    ](grid)
                    for grid in grids
                )

                demos, query = _lesson(seed, start, difficulty)
                assert GEN.lesson_identifiable(demos, query) == []


def test_default_schedule_has_canonical_anchors_and_broad_exploration():
    anchors = [GEN.generate(17, index, difficulty="medium") for index in range(3)]
    observed = {
        (len(grid), len(grid[0]), _palette_size(grid)) for grid in anchors
    }
    assert observed == CANONICAL_PROFILES

    exploration = [
        GEN.generate(20_260_928 + seed, 3, difficulty=difficulty)
        for difficulty in ("easy", "medium", "hard")
        for seed in range(24)
    ]
    dimensions = {(len(grid), len(grid[0])) for grid in exploration}
    assert all(GEN.strict_canonical_like(grid) == [] for grid in exploration)
    assert any((h, w) not in {(8, 12), (9, 12), (9, 13)} for h, w in dimensions)
    assert max(h for h, _ in dimensions) >= 13
    assert max(w for _, w in dimensions) >= 17


def test_declared_overrides_are_exact_composable_observable_and_loud():
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (8, 16):
            for grid_w in (12, 20):
                for n_objects in (2, 3):
                    for wall_position in ("edge", "interior"):
                        for marker_attachment in ("trailing", "mixed"):
                            requested = {
                                "grid_h": grid_h,
                                "grid_w": grid_w,
                                "n_objects": n_objects,
                                "wall_position": wall_position,
                                "marker_attachment": marker_attachment,
                            }
                            grid = GEN.generate(
                                90_000 + case,
                                case % 13,
                                difficulty=difficulty,
                                **requested,
                            )
                            assert GEN.self_check(grid) == []
                            assert GEN.observe_overrides(grid) == requested
                            case += 1

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(0, 0, bogus_axis=1)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="nightmare")


def test_semantic_witnesses_refute_every_named_rival():
    grids = [
        GEN.generate(seed, index, difficulty=difficulty)
        for difficulty in ("easy", "medium", "hard")
        for seed in range(16)
        for index in range(8)
    ]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        candidates = [
            grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)
        ]
        assert candidates, witness_name
        for rival_name in rival_names:
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
                for grid in candidates
            ), (witness_name, rival_name)


def test_declared_canonical_shortcut_fits_public_pairs_but_not_generated_lesson():
    shortcut = GEN.CANONICAL_SHORTCUTS["move_away_from_marker"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _pairs())

    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(31337, index, difficulty=difficulty) for index in range(4)]
        assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in grids)


def test_replay_is_deterministic_fresh_and_global_rng_neutral():
    random.seed(20260928)
    state = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_attachment_profile_always_refutes_marker_position_shortcut():
    # Exact replay from the strict semantic gate's first unidentifiable lesson.
    replays = [(276603472566824, 3, "easy")]
    replays.extend(
        (seed, sample_index, difficulty)
        for difficulty in ("easy", "medium", "hard")
        for seed in range(32)
        for sample_index in (3, 7)
    )
    shortcut = GEN.CANONICAL_SHORTCUTS["move_away_from_marker"]
    for seed, sample_index, difficulty in replays:
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        assert (
            GEN.schedule_profile(seed, sample_index, difficulty)
            == "attachment_counterexample"
        )
        assert GEN.SEMANTIC_WITNESSES[
            "marker_attachment_color_key_visible"
        ](grid), (seed, sample_index, difficulty, GEN.observe_overrides(grid))
        assert shortcut(grid) != GEN.rule_mirror(grid)


def test_canonical_anchor_slots_vary_geometry_not_only_color_permutation():
    # Two-object anchors have only 4P2=12 color assignments and the three-object
    # anchor only 4P3=24.  Exceeding those ceilings proves the natural prior
    # changes geometry as well as relabeling payload colors.
    ceilings = {0: 12, 1: 12, 2: 24}
    for sample_index, color_only_ceiling in ceilings.items():
        grids = {
            tuple(map(tuple, GEN.generate(seed, sample_index, difficulty="medium")))
            for seed in range(128)
        }
        assert len(grids) > color_only_ceiling, (
            GEN.schedule_profile(0, sample_index, "medium"),
            len(grids),
            color_only_ceiling,
        )


def test_three_way_anchor_varies_vertical_orientation_too():
    # Horizontal reflection doubles this slot's 4P3 color ceiling to 48.
    # The three-way slot can also vary vertically while the independent slot
    # remains the guaranteed down-marker anchor for every four-demo lesson.
    grids = {
        tuple(map(tuple, GEN.generate(seed, 2, difficulty="medium")))
        for seed in range(256)
    }
    assert len(grids) > 48, (
        GEN.schedule_profile(0, 2, "medium"),
        len(grids),
        48,
    )


def test_independent_anchor_varies_vertical_under_complementary_schedule():
    # This slot can vary vertically too, provided its orientation is coupled to
    # the three-way slot so every four-demo lesson still exposes marker 4.
    grids = {
        tuple(map(tuple, GEN.generate(seed, 0, difficulty="medium")))
        for seed in range(256)
    }
    assert len(grids) > 24, (
        GEN.schedule_profile(0, 0, "medium"),
        len(grids),
        24,
    )
