from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "02fcd49e49d6"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER = HOME / "adapter.py"


def load_probe():
    path = HOME / "probe.py"
    spec = importlib.util.spec_from_file_location("_test_midpoint_cue_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_prototype():
    path = HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("_test_midpoint_cue_prototype", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_adapter():
    if not ADAPTER.is_file():
        pytest.fail(f"missing native adapter: {ADAPTER}")
    spec = importlib.util.spec_from_file_location("_test_midpoint_cue_adapter", ADAPTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def pair_columns(row: list[int]) -> tuple[int, int] | None:
    hits = [index for index, value in enumerate(row) if value == 8]
    return tuple(hits) if len(hits) == 2 else None


def cue_gap(grid: list[list[int]]) -> int:
    gaps = []
    for row in grid:
        pair = pair_columns(row)
        if pair is None:
            continue
        c1, c2 = pair
        if (c1 + c2) % 2 == 0 and row[(c1 + c2) // 2] == 1:
            gaps.append(c2 - c1)
    assert len(gaps) == 1
    return gaps[0]


def apply_rule(grid: list[list[int]], mode: str, *, forced_gap: int | None = None):
    selected_gap = cue_gap(grid) if mode == "cue_gap" else forced_gap
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        pair = pair_columns(row)
        if pair is None:
            continue
        c1, c2 = pair
        if (c1 + c2) % 2:
            continue
        midpoint = (c1 + c2) // 2
        if row[midpoint] != 0:
            continue
        if mode == "all_pairs" or (mode in {"cue_gap", "fixed_gap"} and c2 - c1 == selected_gap):
            output[r][midpoint] = 2
    return output


def first_n_only(grid: list[list[int]], count: int, *, reverse: bool = False):
    expected = apply_rule(grid, "cue_gap")
    output = [row[:] for row in grid]
    changed = [r for r, (before, after) in enumerate(zip(grid, expected)) if before != after]
    if reverse:
        changed.reverse()
    for r in changed[:count]:
        output[r] = expected[r][:]
    return output


def first_only(grid: list[list[int]]):
    return first_n_only(grid, 1)


def _eligible_rows(grid: list[list[int]]) -> list[tuple[int, int]]:
    rows = []
    for r, row in enumerate(grid):
        pair = pair_columns(row)
        if pair is None:
            continue
        c1, c2 = pair
        if (c1 + c2) % 2 == 0 and row[(c1 + c2) // 2] == 0:
            rows.append((r, c2 - c1))
    return rows


def modal_gap_min(grid: list[list[int]]):
    eligible = []
    for row in grid:
        pair = pair_columns(row)
        if pair is None:
            continue
        c1, c2 = pair
        if (c1 + c2) % 2 == 0 and row[(c1 + c2) // 2] == 0:
            eligible.append(c2 - c1)
    counts = Counter(eligible)
    best = max(counts.values())
    selected = min(gap for gap, count in counts.items() if count == best)
    return apply_rule(grid, "fixed_gap", forced_gap=selected)


def positional_gap_rule(grid: list[list[int]], position: str):
    cue_row = next(
        r
        for r, row in enumerate(grid)
        if (pair := pair_columns(row)) is not None
        and (pair[0] + pair[1]) % 2 == 0
        and row[(pair[0] + pair[1]) // 2] == 1
    )
    eligible = []
    for r, row in enumerate(grid):
        pair = pair_columns(row)
        if pair is None:
            continue
        c1, c2 = pair
        if (c1 + c2) % 2 == 0 and row[(c1 + c2) // 2] == 0:
            eligible.append((r, c2 - c1))
    if position == "top":
        selected = min(eligible)[1]
    elif position == "bottom":
        selected = max(eligible)[1]
    elif position == "above":
        selected = max(item for item in eligible if item[0] < cue_row)[1]
    elif position == "below":
        selected = min(item for item in eligible if item[0] > cue_row)[1]
    else:
        raise ValueError(position)
    return apply_rule(grid, "fixed_gap", forced_gap=selected)


def all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_bytes_and_alternative_is_distinct():
    adapter = load_adapter()
    default = adapter.program({"selection": "all_pairs"})
    alternate = adapter.program({"selection": "cue_gap"})
    assert default == canonical_program()
    assert alternate != default
    assert alternate.strip().startswith("(rule!")


def test_generation_is_deterministic_matched_across_settings_and_prefix_stable():
    adapter = load_adapter()
    all_pairs = adapter.generate(17, {"selection": "all_pairs"}, 3, 4)
    cue = adapter.generate(17, {"selection": "cue_gap"}, 3, 4)
    cue_again = adapter.generate(17, {"selection": "cue_gap"}, 3, 4)
    cue_one_query = adapter.generate(17, {"selection": "cue_gap"}, 3, 1)

    assert cue == cue_again
    assert all_inputs(all_pairs) == all_inputs(cue)
    assert cue_one_query["train"] == cue["train"]
    assert cue_one_query["test"] == cue["test"][:1]
    assert len({json.dumps(grid) for grid in all_inputs(cue)}) == 7


def test_labels_match_independent_oracle_and_two_demos_reject_cheap_rivals():
    adapter = load_adapter()
    for setting in ("all_pairs", "cue_gap"):
        episode = adapter.generate(0, {"selection": setting}, 2, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == apply_rule(pair["input"], setting)

        demos = episode["train"]
        declared_survivors = [
            candidate
            for candidate in ("all_pairs", "cue_gap")
            if all(apply_rule(pair["input"], candidate) == pair["output"] for pair in demos)
        ]
        assert declared_survivors == [setting]

        rivals = {
            "identity": lambda grid: [row[:] for row in grid],
            "fixed_gap_2": lambda grid: apply_rule(grid, "fixed_gap", forced_gap=2),
            "fixed_gap_4": lambda grid: apply_rule(grid, "fixed_gap", forced_gap=4),
            "fixed_gap_6": lambda grid: apply_rule(grid, "fixed_gap", forced_gap=6),
            "first_only": first_only,
        }
        for name, rival in rivals.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_two_demo_lessons_reject_smallest_and_largest_gap_shortcuts():
    adapter = load_adapter()
    for seed in range(12):
        episode = adapter.generate(seed, {"selection": "cue_gap"}, 2, 1)
        for choose in (min, max):
            assert any(
                apply_rule(
                    pair["input"],
                    "fixed_gap",
                    forced_gap=choose(gap for _row, gap in _eligible_rows(pair["input"])),
                )
                != pair["output"]
                for pair in episode["train"]
            ), (seed, choose.__name__)


def test_two_demo_seed_41_rejects_modal_gap_shortcut():
    adapter = load_adapter()
    episode = adapter.generate(41, {"selection": "cue_gap"}, 2, 4)
    assert any(
        modal_gap_min(pair["input"]) != pair["output"]
        for pair in episode["train"]
    )


def test_two_demo_lesson_rejects_two_match_caps_from_both_directions():
    adapter = load_adapter()
    episode = adapter.generate(0, {"selection": "cue_gap"}, 2, 4)
    for reverse in (False, True):
        assert any(
            first_n_only(pair["input"], 2, reverse=reverse) != pair["output"]
            for pair in episode["train"]
        )


def test_candidate_gap_frequencies_force_multiple_cue_matches_and_frequency_decoys():
    adapter = load_adapter()
    for seed in (0, 17, 41):
        episode = adapter.generate(seed, {"selection": "cue_gap"}, 2, 1)
        for pair in episode["train"]:
            grid = pair["input"]
            selected = cue_gap(grid)
            eligible = []
            for row in grid:
                endpoints = pair_columns(row)
                if endpoints is None:
                    continue
                c1, c2 = endpoints
                if (c1 + c2) % 2 == 0 and row[(c1 + c2) // 2] == 0:
                    eligible.append(c2 - c1)
            counts = Counter(eligible)
            assert counts[selected] >= 2
            assert max(counts.values()) > counts[selected]
            assert min(counts.values()) < counts[selected]


@pytest.mark.parametrize(
    ("seed", "position"),
    [(143, "top"), (34, "bottom"), (22, "above"), (9, "below")],
)
def test_two_demo_lessons_reject_position_gap_shortcuts(seed, position):
    adapter = load_adapter()
    episode = adapter.generate(seed, {"selection": "cue_gap"}, 2, 4)
    assert any(
        positional_gap_rule(pair["input"], position) != pair["output"]
        for pair in episode["train"]
    )


def test_authoring_rival_catalog_covers_and_rejects_adversarial_shortcuts():
    prototype = load_prototype()
    expected = {
        "identity",
        "all_pairs",
        "cue_gap",
        "fixed_gap_2",
        "fixed_gap_4",
        "fixed_gap_6",
        "fixed_gap_8",
        "fixed_gap_10",
        "fixed_gap_12",
        "first_only",
        "last_only",
        "first_two",
        "last_two",
        "min_gap",
        "max_gap",
        "modal_gap_min",
        "modal_gap_max",
        "rarest_gap_min",
        "rarest_gap_max",
        "top_gap",
        "bottom_gap",
        "nearest_above_gap",
        "nearest_below_gap",
        "nearest_gap",
        "farthest_gap",
    }
    for seed in range(32):
        for setting in ("all_pairs", "cue_gap"):
            episode = prototype.generate(seed, {"selection": setting}, 2, 1)
            catalogs = [prototype.rival_outputs(pair["input"]) for pair in episode["train"]]
            assert set(catalogs[0]) == expected
            survivors = [
                name
                for name in expected
                if all(catalog[name] == pair["output"] for catalog, pair in zip(catalogs, episode["train"]))
            ]
            assert survivors == [setting], (seed, setting, survivors)


def test_probe_adversarial_census_is_compact_and_intended_only():
    prototype = load_prototype()
    probe = load_probe()
    report = probe._adversarial_census(prototype, 32)
    assert report["status"] == "passed"
    assert report["seed_count"] == 32
    assert report["minimum_demos"] == 2
    assert report["rival_count"] == 25
    assert tuple(report["settings"]) == ('all_pairs', 'cue_gap')
    assert report["case_count"] == 64
    assert report["unexpected_survivors"] == []
    assert len(report["census_sha256"]) == 64


def test_supported_counts_boundaries_and_exact_types():
    adapter = load_adapter()
    for demos in range(2, 7):
        episode = adapter.generate(123, {"selection": "cue_gap"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
    for queries in range(1, 5):
        assert len(adapter.generate(123, {"selection": "all_pairs"}, 2, queries)["test"]) == queries

    bad_calls = [
        (True, {"selection": "cue_gap"}, 2, 4),
        (-1, {"selection": "cue_gap"}, 2, 4),
        (0, {"selection": "unknown"}, 2, 4),
        (0, {"selection": "cue_gap", "extra": 1}, 2, 4),
        (0, {"selection": "cue_gap"}, 1, 4),
        (0, {"selection": "cue_gap"}, 7, 4),
        (0, {"selection": "cue_gap"}, 2, 0),
        (0, {"selection": "cue_gap"}, 2, 5),
        (0, {"selection": "cue_gap"}, 2.0, 4),
    ]
    for args in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(*args)


def test_fourth_query_is_substantive_exact_30_by_30_boundary_stress():
    adapter = load_adapter()
    pair = adapter.generate(17, {"selection": "cue_gap"}, 2, 4)["test"][3]
    grid = pair["input"]
    assert len(grid) == 30 and len(grid[0]) == 30
    active = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(active) >= 50
    assert len({r for r, _ in active}) >= 18
    assert max(r for r, _ in active) - min(r for r, _ in active) >= 29
    assert max(c for _, c in active) - min(c for _, c in active) >= 29
    assert pair["output"] == apply_rule(grid, "cue_gap")
