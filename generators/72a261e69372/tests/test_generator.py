"""Task-local regression tests for the smallest-exact-enclosing-frame task."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    color_boxes,
    exact_frames,
    has_nested_choice,
    has_occluded_orphan,
    load_generator,
    observed,
    outline,
    pinned_seed,
    profile,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_canonical_inputs_and_oracle_matches_outputs(pair):
    assert gen.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_round_trip_in_every_band(band):
    options = {
        "grid_h": 18,
        "grid_w": 20,
        "n_frames": 3,
        "layout_kind": "overlap",
        "palette_kind": "mixed",
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 10),
        ("grid_h", 19),
        ("grid_w", 12),
        ("grid_w", 21),
        ("n_frames", 1),
        ("n_frames", 4),
        ("layout_kind", "disjoint"),
        ("palette_kind", "default"),
        ("grid_h", True),
        ("grid_w", 14.5),
        ("n_frames", "3"),
    ],
)
def test_rejects_unknown_out_of_domain_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_exact_support_in_every_band(band):
    canonical_profiles = {profile(pair["input"]) for pair in canonical_pairs()}
    hits = 0
    for index in range(20):
        seed = pinned_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        assert gen.self_check(grid) == []
        hits += profile(grid) in canonical_profiles
    assert hits >= 1


def test_overlap_layout_refutes_bbox_is_frame_shortcut():
    grid = gen.generate(
        91,
        7,
        grid_h=13,
        grid_w=15,
        n_frames=3,
        layout_kind="overlap",
        palette_kind="mixed",
    )
    assert gen.self_check(grid) == []
    assert has_occluded_orphan(grid)
    assert reference_output(grid) != reference_output(grid, use_bboxes=True)
    assert gen.SEMANTIC_WITNESSES["occluded_frame"](grid)
    assert gen.SEMANTIC_RIVALS["bbox_is_frame"](grid) == reference_output(grid, use_bboxes=True)


def test_nested_layout_refutes_outermost_frame_shortcut():
    grid = gen.generate(
        92,
        8,
        grid_h=13,
        grid_w=15,
        n_frames=3,
        layout_kind="nested",
        palette_kind="low",
    )
    assert gen.self_check(grid) == []
    assert has_nested_choice(grid)
    assert reference_output(grid) != reference_output(grid, outermost=True)
    assert gen.SEMANTIC_WITNESSES["smallest_not_outermost"](grid)
    assert gen.SEMANTIC_RIVALS["outermost_frame"](grid) == reference_output(grid, outermost=True)


def test_semantic_contract_names_and_rule_hash_are_pinned():
    assert gen.RULE_HASH == "d763a0664108"
    assert set(gen.SEMANTIC_WITNESSES) == {"occluded_frame", "smallest_not_outermost"}
    assert set(gen.SEMANTIC_RIVALS) == {"bbox_is_frame", "outermost_frame"}
    assert gen.WITNESS_RIVALS == {
        "occluded_frame": ["bbox_is_frame"],
        "smallest_not_outermost": ["outermost_frame"],
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(gen.SEMANTIC_RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)


def test_validator_rejects_unexplained_hole_in_occluded_outline():
    grid = gen.generate(5, 2, layout_kind="overlap", n_frames=3)
    exact_colors = {color for color, _ in exact_frames(grid)}
    broken = [(color, box) for color, box in color_boxes(grid) if color not in exact_colors]
    assert len(broken) == 1
    color, box = broken[0]
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    overwritten = [p for p in outline(box) - cells if grid[p[0]][p[1]] not in (0, 1)]
    assert overwritten
    r, c = overwritten[0]
    grid[r][c] = 0
    assert gen.self_check(grid)


@pytest.mark.parametrize("mutation", ["unknown_color_pixel", "erase_exact_frame", "remove_marker"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(4, 2, layout_kind="nested", n_frames=3, palette_kind="low")
    if mutation == "unknown_color_pixel":
        grid[0][0] = 9
    elif mutation == "erase_exact_frame":
        _, box = exact_frames(grid)[0]
        grid[box[0]][box[1]] = 0
    else:
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 1:
                    grid[r][c] = 0
                    break
            else:
                continue
            break
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 13 for _ in range(11)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_determinism_fresh_return_and_python_hash_independence():
    first = gen.generate(412, 111, difficulty="hard")
    second = gen.generate(412, 111, difficulty="hard")
    assert first == second and first is not second
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(412, 111, difficulty="hard") == second

    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


@pytest.mark.parametrize("turns,reflect", [(r, f) for r in range(4) for f in (False, True)])
def test_rule_and_validator_are_dihedrally_equivariant(turns, reflect):
    def transform(grid):
        result = deepcopy(grid)
        if reflect:
            result = [row[::-1] for row in result]
        for _ in range(turns):
            result = _rot90(result)
        return result

    for index in range(12):
        grid = gen.generate(900 + index, index, layout_kind="overlap" if index % 2 else "nested")
        changed = transform(grid)
        assert gen.self_check(changed) == []
        assert reference_output(changed) == transform(reference_output(grid))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_four_demo_lesson_is_identifiable(band):
    assert callable(gen.lesson_identifiable)
    for start in range(40):
        seed = 7000 + start
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(seed, start * 11 + offset, difficulty=band)
            demos.append({"input": grid, "output": reference_output(grid)})
        query_grid = gen.generate(seed, start * 11 + gen.EXAMPLES_NEEDED, difficulty=band)
        query = {"input": query_grid, "output": reference_output(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for rival in gen.LESSON_COMPETITORS.values():
            assert not all(rival(pair["input"]) == pair["output"] for pair in demos)


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(319 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(24))
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]
