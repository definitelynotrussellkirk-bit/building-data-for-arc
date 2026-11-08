"""Task-local regressions for 3799ce10ce15.

The oracle/probes live in workspace/reference_probe.py and do not share
implementation helpers with generator.py.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    exactly_once_presence,
    fixed_canonical_windows,
    intended_output,
    load_generator,
    observed,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_accepts_every_canonical_pair_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_metadata_pins_the_authority_and_declares_real_axes():
    assert gen.RULE_HASH == "7962236ae928"
    assert gen.VERSION != "1.3.1"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "palette_size",
        "n_frames",
        "copies_per_present",
    }
    assert 2 <= gen.EXAMPLES_NEEDED <= 5


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    options = {
        "grid_h": 13,
        "grid_w": 18,
        "palette_size": 4,
        "n_frames": 4,
        "copies_per_present": 3,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) | {} == options | {
        "legend_columns": observed(grid)["legend_columns"],
        "frame_bboxes": observed(grid)["frame_bboxes"],
    }
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 12),
        ("grid_h", 19),
        ("grid_w", 17),
        ("grid_w", 26),
        ("palette_size", 1),
        ("palette_size", 5),
        ("n_frames", 1),
        ("n_frames", 5),
        ("copies_per_present", 0),
        ("copies_per_present", 4),
        ("n_frames", 2.5),
        ("grid_h", True),
        ("palette_size", "3"),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_covers_profiles_layouts_and_multiplicity(band):
    shapes = set()
    palettes = set()
    frame_counts = set()
    copies = set()
    frame_boxes = set()
    canonical_profiles = 0
    duplicate_evidence = 0
    for index in range(72):
        grid = gen.generate(1900 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(1900 + index, index, difficulty=band)
        stats = observed(grid)
        assert stats["copies_per_present"] in (1, 2, 3)
        assert intended_output(grid)
        assert fixed_canonical_windows(grid) != intended_output(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        palettes.add(stats["palette_size"])
        frame_counts.add(stats["n_frames"])
        copies.add(stats["copies_per_present"])
        frame_boxes.update(stats["frame_bboxes"])
        canonical_profiles += (
            stats["grid_h"], stats["grid_w"], stats["palette_size"] + 2
        ) == (13, 18, 5)
        duplicate_evidence += exactly_once_presence(grid) != intended_output(grid)
    assert len(shapes) >= 8
    assert palettes == {2, 3, 4}
    assert frame_counts == {2, 3, 4}
    assert copies == {1, 2, 3}
    assert len(frame_boxes) >= 30
    assert canonical_profiles >= 12
    assert duplicate_evidence >= 40


@pytest.mark.parametrize(
    "mutation",
    [
        "blank",
        "duplicate_legend",
        "erase_frame_cell",
        "unknown_interior_color",
        "colored_cell_outside_frame",
        "empty_first_frame",
        "extra_nine",
    ],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        41,
        5,
        grid_h=13,
        grid_w=18,
        palette_size=3,
        n_frames=3,
        copies_per_present=2,
    )
    boxes = observed(grid)["frame_bboxes"]
    pal_cols = list(observed(grid)["legend_columns"])
    pal = [grid[0][c] for c in pal_cols]
    if mutation == "blank":
        grid = [[0 for _ in row] for row in grid]
    elif mutation == "duplicate_legend":
        grid[0][pal_cols[1]] = grid[0][pal_cols[0]]
    elif mutation == "erase_frame_cell":
        r0, c0, _, _ = boxes[0]
        grid[r0][c0] = 0
    elif mutation == "unknown_interior_color":
        r0, c0, _, _ = boxes[0]
        unknown = next(color for color in range(1, 9) if color not in pal)
        grid[r0 + 1][c0 + 1] = unknown
    elif mutation == "colored_cell_outside_frame":
        grid[1][0] = pal[0]
    elif mutation == "empty_first_frame":
        r0, c0, r1, c1 = boxes[0]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                grid[r][c] = 0
    elif mutation == "extra_nine":
        grid[1][0] = 9
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 18 for _ in range(13)]])
def test_malformed_grid_returns_diagnostics_instead_of_raising(bad):
    assert gen.self_check(bad)


def test_fixed_window_shortcut_fits_all_canonical_pairs_but_not_generation():
    assert all(
        fixed_canonical_windows(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )
    for index in range(24):
        grid = gen.generate(712 + index, index)
        assert gen.SEMANTIC_WITNESSES["fixed_canonical_windows_break"](grid)
        assert gen.SEMANTIC_RIVALS["fixed_canonical_windows"](grid) == fixed_canonical_windows(grid)
        assert fixed_canonical_windows(grid) != intended_output(grid)


def test_duplicate_witness_refutes_exactly_once_rival():
    for index in (1, 2, 4, 5):
        grid = gen.generate(888, index)
        assert gen.SEMANTIC_WITNESSES["repeated_presence_cells"](grid)
        assert gen.SEMANTIC_RIVALS["exactly_once_presence"](grid) == exactly_once_presence(grid)
        assert exactly_once_presence(grid) != intended_output(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_demo_lessons_are_identifiable_against_declared_rivals(band):
    pairs = []
    for index in range(4):
        grid = gen.generate(5001, index, difficulty=band)
        pairs.append({"input": grid, "output": intended_output(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_rule_application_does_not_mutate_input():
    grid = gen.generate(92, 8)
    before = deepcopy(grid)
    intended_output(grid)
    fixed_canonical_windows(grid)
    exactly_once_presence(grid)
    assert grid == before


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319 + index, index, difficulty="hard") for index in range(18)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(12))
def test_every_cyclic_schedule_start_refutes_declared_rivals(band, start):
    pairs = []
    for offset in range(4):
        sample_index = start + offset
        grid = gen.generate(9100 + start, sample_index, difficulty=band)
        pairs.append({"input": grid, "output": intended_output(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
    for competitor in gen.LESSON_COMPETITORS.values():
        assert not all(
            competitor(pair["input"]) == pair["output"] for pair in pairs[:3]
        )


def test_reference_probe_finds_portable_root_without_fixed_parent_depth(tmp_path):
    """The copied probe must bind canonical data by content, not parents[N]."""
    import shutil

    runtime = tmp_path / "runtime"
    nested = runtime / "odd" / "extra" / "depth" / "workspace"
    nested.mkdir(parents=True)
    (runtime / "data" / "canonical").mkdir(parents=True)

    pair = canonical_pairs()[0]
    row = {
        "task_id": gen.TASK_ID,
        "train": [{"input": pair["input"], "output": pair["output"]}],
        "test": [],
    }
    (runtime / "data" / "canonical" / "puzzles.jsonl").write_text(
        json.dumps(row) + "\n", encoding="utf-8"
    )

    support_source = None
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "shared" / "runtime" / "reviewer_support.py"
        if candidate.is_file():
            support_source = candidate
            break
        candidate = ancestor / "reviewer_support.py"
        if candidate.is_file():
            support_source = candidate
            break
    assert support_source is not None
    shutil.copy2(support_source, runtime / "reviewer_support.py")
    copied_probe = nested / "reference_probe.py"
    shutil.copy2(HOME / "workspace" / "reference_probe.py", copied_probe)

    script = f"""
import importlib.util
from pathlib import Path
path = Path({str(copied_probe)!r})
spec = importlib.util.spec_from_file_location('copied_reference_probe', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
pairs = module.canonical_pairs()
assert module.ROOT == Path({str(runtime)!r}).resolve(), (module.ROOT, {str(runtime)!r})
assert len(pairs) == 1
assert pairs[0]['input'] == {pair['input']!r}
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
