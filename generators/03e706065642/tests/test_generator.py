from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "03e706065642"
EXPECTED_RULE_HASH = "ae585f1eb109"
EXPECTED_CLASS_SCHEDULE = (
    (2, 2, 0),
    (1, 3, 1),
    (0, 2, 2),
)

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _signature(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_public_contract_is_rule_bound_and_axes_are_orthogonal() -> None:
    generator = _load_generator()
    assert generator.RULE_HASH == EXPECTED_RULE_HASH
    assert generator.EXAMPLES_NEEDED == 4
    assert generator.LESSON_SCHEDULE_PERIOD == 5
    assert generator.MIN_STRICT_FRAC == 1.0
    assert generator.EXPECTED_OUTPUT_CODOMAIN == 5
    assert set(generator.AXES) == {"frame_n", "layout", "texture"}
    assert generator.AXES["layout"]["valid"] == "pair|all_same|all_distinct"
    assert generator.AXES["texture"]["valid"] == "same_color|mixed_colors"
    assert generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert callable(generator.observe_overrides)
    assert callable(generator.analyze_grid)
    assert callable(generator.rule_mirror)
    assert callable(generator.lesson_identifiable)
    assert generator.WITNESS_RIVALS == {
        name: [name] for name in generator.SEMANTIC_RIVALS
    }


def test_unknown_and_invalid_overrides_fail_loudly() -> None:
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, typo_layout="pair")
    with pytest.raises(ValueError, match="frame_n"):
        generator.generate(0, 0, frame_n=9)
    with pytest.raises(ValueError, match="layout"):
        generator.generate(0, 0, layout="sometimes_pair")
    with pytest.raises(ValueError, match="texture"):
        generator.generate(0, 0, texture="pair")
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(0, 0, difficulty="nightmare")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("frame_n", [5, 6, 7, 8])
def test_every_frame_override_is_honored_in_every_band(
    band: str, frame_n: int
) -> None:
    generator = _load_generator()
    grid = generator.generate(
        19,
        7,
        difficulty=band,
        frame_n=frame_n,
        layout="pair",
        texture="same_color",
    )
    observed = generator.observe_overrides(grid)
    assert observed == {
        "frame_n": frame_n,
        "layout": "pair",
        "texture": "same_color",
    }
    assert generator.self_check(grid, difficulty=band) == []


def test_layout_and_texture_controls_have_independent_visible_effects() -> None:
    generator = _load_generator()
    for layout in ("pair", "all_same", "all_distinct"):
        same = generator.generate(31, 8, layout=layout, texture="same_color")
        mixed = generator.generate(31, 8, layout=layout, texture="mixed_colors")
        assert generator.observe_overrides(same)["layout"] == layout
        assert generator.observe_overrides(mixed)["layout"] == layout
        assert generator.observe_overrides(same)["texture"] == "same_color"
        assert generator.observe_overrides(mixed)["texture"] == "mixed_colors"
        assert same != mixed


def test_default_stream_recurrently_hits_the_exact_canonical_profile() -> None:
    generator = _load_generator()
    canonical_signatures = {_signature(pair["input"]) for pair in _canonical_pairs()}
    assert canonical_signatures == {(9, 23, 3)}
    for band in ("easy", "medium", "hard"):
        hits = [
            _signature(generator.generate(seed, index, difficulty=band))
            for seed, index in zip(range(20), range(20))
        ]
        assert (9, 23, 3) in hits


def test_canonical_pairs_are_lawful_and_python_mirror_matches_authority() -> None:
    generator = _load_generator()
    for pair in _canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_strongest_canonical_shortcut_fits_all_canonical_pairs() -> None:
    generator = _load_generator()
    rival = generator.CANONICAL_SHORTCUTS["collapse_ud_with_none"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())


def test_default_schedule_exposes_vertical_only_symmetry_and_refutes_shortcut() -> None:
    generator = _load_generator()
    rival = generator.CANONICAL_SHORTCUTS["collapse_ud_with_none"]
    witness_slots = []
    for slot, expected in enumerate(EXPECTED_CLASS_SCHEDULE):
        grid = generator.generate(73, slot, difficulty="medium")
        assert tuple(generator.analyze_grid(grid)["classes"]) == expected
        if rival(grid) != generator.rule_mirror(grid):
            witness_slots.append(slot)
    # Slot 1 is deliberately (1, 3, 1), so a rival that changes only class 2
    # must agree there.  Slots 0 and 2 are independent vertical-only witnesses.
    assert witness_slots == [0, 2]


def test_every_query_rotation_refutes_every_declared_lesson_competitor() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(10):
            pairs = []
            for offset in range(generator.EXAMPLES_NEEDED + 1):
                grid = generator.generate(101, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert generator.lesson_identifiable(demos, query) == []
                for name, rival in generator.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (band, start, query_index, name)


def test_large_frames_generate_larger_motifs_and_repeated_classes_use_new_shapes() -> None:
    generator = _load_generator()
    saw_large = False
    for seed in range(24):
        grid = generator.generate(
            seed,
            seed % 5,
            frame_n=8,
            layout="all_same",
            texture="mixed_colors",
        )
        analysis = generator.analyze_grid(grid)
        shapes = analysis["shapes"]
        assert len(set(shapes)) == 3
        saw_large |= any(
            max(max(r for r, _ in shape), max(c for _, c in shape)) >= 3
            for shape in shapes
        )
    assert saw_large


def test_generation_and_semantic_helpers_are_deterministic_and_input_pure() -> None:
    generator = _load_generator()
    grid = generator.generate(211, 17, difficulty="hard")
    assert grid == generator.generate(211, 17, difficulty="hard")
    original = copy.deepcopy(grid)
    generator.analyze_grid(grid)
    generator.observe_overrides(grid)
    generator.rule_mirror(grid)
    for rival in generator.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


def test_retained_canonical_shortcut_counterexample_is_lawful_and_rule_bound() -> None:
    generator = _load_generator()
    path = TASK_DIR / "counterexamples" / "collapse_ud_with_none.json"
    record = json.loads(path.read_text())

    assert record["schema"] == "arcpuzzles-generator-counterexample-v1"
    assert record["task_id"] == TASK_ID
    assert record["rule_hash"] == EXPECTED_RULE_HASH
    assert record["rival_name"] == "collapse_ud_with_none"
    grid = record["input"]
    assert generator.self_check(grid) == []
    assert tuple(generator.analyze_grid(grid)["classes"]) == (2, 2, 0)
    assert generator.rule_mirror(grid) == record["racket_output"]
    assert generator.CANONICAL_SHORTCUTS[record["rival_name"]](grid) == record["rival_output"]
    assert record["racket_output"] != record["rival_output"]
