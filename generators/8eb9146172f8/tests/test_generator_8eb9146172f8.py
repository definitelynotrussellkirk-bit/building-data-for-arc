from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared/runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

GENERATOR_PATH = REPO_ROOT / "generators/8eb9146172f8/generator.py"
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "review_8eb9146172f8", GENERATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


@pytest.fixture(scope="module")
def canonical_pairs():
    pairs = []
    seen = set()
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != "8eb9146172f8":
            continue
        for split in ("train", "test"):
            examples = row.get(split) or []
            if isinstance(examples, dict):
                examples = [examples]
            for example in examples:
                key = json.dumps(example, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    pairs.append(example)
    assert len(pairs) == 4
    return pairs


def test_contract_metadata_and_probe_hooks_are_present(gen):
    assert gen.RULE_HASH == "5592536df499"
    assert gen.VERSION != "2.1.0"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "cyan_edge",
        "red_edge",
        "n_red",
        "n_cyan",
    }
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.rule_mirror)
    assert gen.CANONICAL_SHORTCUTS
    assert gen.SEMANTIC_WITNESSES


def test_all_distinct_canonical_pairs_pass_contract_and_python_mirror(
    gen, canonical_pairs
):
    for pair in canonical_pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_ordinary_generation_is_deterministic_valid_and_rule_fires(gen):
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(16):
            first = gen.generate(8128, sample_index, difficulty=difficulty)
            second = gen.generate(8128, sample_index, difficulty=difficulty)
            assert first == second
            assert gen.self_check(first, difficulty=difficulty) == []
            facts = gen.observe_overrides(first)
            assert facts["cyan_edge"] != facts["red_edge"]
            assert gen.rule_mirror(first) != first


def test_exact_override_boundaries_and_all_orientation_families_are_realized(gen):
    cases = (
        {
            "grid_h": 9,
            "grid_w": 9,
            "cyan_edge": "top",
            "red_edge": "left",
            "n_red": 4,
            "n_cyan": 4,
        },
        {
            "grid_h": 20,
            "grid_w": 22,
            "cyan_edge": "bottom",
            "red_edge": "right",
            "n_red": 1,
            "n_cyan": 1,
        },
        {
            "grid_h": 9,
            "grid_w": 22,
            "cyan_edge": "left",
            "red_edge": "top",
            "n_red": 4,
            "n_cyan": 4,
        },
        {
            "grid_h": 20,
            "grid_w": 9,
            "cyan_edge": "right",
            "red_edge": "bottom",
            "n_red": 4,
            "n_cyan": 4,
        },
    )
    for sample_index, expected in enumerate(cases):
        grid = gen.generate(991, sample_index, difficulty="hard", **expected)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == expected


def test_single_edge_override_constrains_the_other_edge_perpendicularly(gen):
    for edge in gen.EDGES:
        cyan_grid = gen.generate(17, 3, cyan_edge=edge)
        cyan_facts = gen.observe_overrides(cyan_grid)
        assert cyan_facts["cyan_edge"] == edge
        assert gen._perpendicular(cyan_facts["cyan_edge"], cyan_facts["red_edge"])

        red_grid = gen.generate(29, 5, red_edge=edge)
        red_facts = gen.observe_overrides(red_grid)
        assert red_facts["red_edge"] == edge
        assert gen._perpendicular(red_facts["cyan_edge"], red_facts["red_edge"])


def test_unknown_invalid_and_parallel_edge_overrides_fail_loudly(gen):
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 0, grid_h=8)
    with pytest.raises(ValueError, match="cyan_edge.*red_edge|red_edge.*cyan_edge"):
        gen.generate(1, 0, cyan_edge="top", red_edge="bottom")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_canonical_shortcuts_really_fit_canonical_but_generated_witnesses_refute_them(
    gen, canonical_pairs
):
    for shortcut in gen.CANONICAL_SHORTCUTS.values():
        for pair in canonical_pairs:
            assert shortcut(pair["input"]) == pair["output"]

    horizontal = gen.generate(
        7,
        0,
        grid_h=12,
        grid_w=14,
        cyan_edge="left",
        red_edge="top",
        n_red=3,
        n_cyan=2,
    )
    assert gen.SEMANTIC_WITNESSES["horizontal_top_deflectors_shift_down"](
        horizontal
    )
    assert (
        gen.CANONICAL_SHORTCUTS["horizontal_always_shifts_up"](horizontal)
        != gen.rule_mirror(horizontal)
    )

    bottom = gen.generate(
        11,
        0,
        grid_h=14,
        grid_w=12,
        cyan_edge="bottom",
        red_edge="left",
        n_red=3,
        n_cyan=2,
    )
    assert gen.SEMANTIC_WITNESSES["bottom_emitters_travel_upward"](bottom)
    assert (
        gen.CANONICAL_SHORTCUTS["vertical_emitters_always_travel_down"](bottom)
        != gen.rule_mirror(bottom)
    )


def test_self_check_rejects_wrong_palette_parallel_edges_and_off_edge_markers(gen):
    wrong_palette = gen.generate(3, 0)
    wrong_palette[1][1] = 5
    assert any("colors" in message or "palette" in message for message in gen.self_check(wrong_palette))

    parallel = [[0] * 10 for _ in range(10)]
    parallel[0][2] = 8
    parallel[0][7] = 8
    parallel[9][3] = 2
    parallel[9][6] = 2
    assert any("perpendicular" in message for message in gen.self_check(parallel))

    off_edge = [[0] * 9 for _ in range(9)]
    off_edge[0][2] = 8
    off_edge[3][3] = 8
    off_edge[2][0] = 2
    off_edge[6][0] = 2
    assert any("exactly one edge" in message for message in gen.self_check(off_edge))


def test_default_dimensions_anchor_every_band_to_canonical_profiles(gen, canonical_pairs):
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0])) for pair in canonical_pairs
    }
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(3301, sample_index, difficulty=difficulty)
            assert (len(grid), len(grid[0])) in canonical_profiles
