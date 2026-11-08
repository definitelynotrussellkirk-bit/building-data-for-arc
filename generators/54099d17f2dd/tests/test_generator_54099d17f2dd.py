"""Task-local regressions for template-at-marker generator 54099d17f2dd."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

TASK_ID = "54099d17f2dd"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load(HOME / "generator.py", "reviewed_54099d17f2dd")
ROOT = find_root(__file__)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _load_probe():
    return _load(HOME / "workspace" / "reference_probe.py", "probe_54099d17f2dd")


def test_declares_small_honest_source_bound_contract():
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "4a6409bfdf9a"
    assert gen.EXAMPLES_NEEDED == 4
    assert set(gen.AXES) == {"grid_h", "grid_w", "template_shape"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "left_five_a",
        "right_tetromino",
        "left_five_b",
        "right_small",
    )


def test_all_canonical_pairs_are_accepted_and_mirror_matches_authority():
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("shape_name", ["l4", "t4", "s4", "z4", "square4", "i3", "l3", "zigzag5", "long_l5"])
def test_exact_overrides_are_observable_in_every_band(difficulty, shape_name):
    requested = {"grid_h": 11, "grid_w": 15, "template_shape": shape_name}
    grid = gen.generate(71, 19, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert grid == gen.generate(71, 19, difficulty=difficulty, **requested)


@pytest.mark.parametrize(
    "height,width,shape_name",
    itertools.product((8, 13), (10, 16), ("l4", "t4", "s4", "z4", "square4", "i3", "l3", "zigzag5", "long_l5")),
)
def test_every_boundary_override_combination_is_constructive(height, width, shape_name):
    requested = {"grid_h": height, "grid_w": width, "template_shape": shape_name}
    grid = gen.generate(901, 37, difficulty="hard", **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 14),
        ("grid_w", 9),
        ("grid_w", 17),
        ("template_shape", "missing"),
        ("grid_h", True),
        ("grid_w", 10.5),
        ("template_shape", 7),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 0]],
        [[True] * 10 for _ in range(8)],
        [[0] * 10 for _ in range(8)],
        [[1] + [0] * 9 for _ in range(8)],
        [[2] + [0] * 9 for _ in range(8)],
        [[8] + [0] * 9 for _ in range(8)],
    ],
)
def test_malformed_and_impostor_grids_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_destructive_mutations_are_rejected():
    grid = gen.generate(812, 9, difficulty="medium")
    mutations = []

    no_marker = deepcopy(grid)
    for row in no_marker:
        for c, value in enumerate(row):
            if value == 1:
                row[c] = 0
    mutations.append(no_marker)

    extra_marker = deepcopy(grid)
    extra_marker[0][0] = 1
    mutations.append(extra_marker)

    no_template = [[0 if value == 2 else value for value in row] for row in grid]
    mutations.append(no_template)

    illegal_colour = deepcopy(grid)
    illegal_colour[0][0] = 8
    mutations.append(illegal_colour)

    disconnected = deepcopy(grid)
    template = [(r, c) for r, row in enumerate(disconnected) for c, v in enumerate(row) if v == 2]
    disconnected[template[0][0]][template[0][1]] = 0
    disconnected[0][0] = 2
    mutations.append(disconnected)

    for index, mutation in enumerate(mutations):
        assert gen.self_check(mutation), index


def test_determinism_fresh_returns_and_global_rng_state():
    state = random.getstate()
    first = gen.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert gen.generate(901, 17, difficulty="hard") == second


def test_rule_and_rivals_do_not_mutate_inputs():
    grid = gen.generate(812, 9, difficulty="hard")
    original = deepcopy(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


def test_declared_shortcuts_fit_every_canonical_pair():
    pairs = _pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "mirror_when_marker_left",
        "copy_first_four_cells",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_scheduled_generated_cases_refute_both_canonical_shortcuts():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(5100, index, difficulty=band) for index in range(4)]
        assert {gen.schedule_profile(5100, index, band) for index in range(4)} == set(gen.SCHEDULE_PROFILES)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            matching = [grid for grid in grids if witness(grid)]
            assert matching, witness_name
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                rival = gen.SEMANTIC_RIVALS[rival_name]
                assert all(rival(grid) != gen.rule_mirror(grid) for grid in matching)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_four_demo_window_refutes_all_declared_competitors(band, start):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        index = start + offset
        grid = gen.generate(6200 + start, index, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(demos, demos[0]["input"]) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_five_pair_window_survives_all_query_rotations(band, start):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        index = start + offset
        grid = gen.generate(7300 + start, index, difficulty=band)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    for query_index in range(len(pairs)):
        demos = pairs[:query_index] + pairs[query_index + 1 :]
        assert gen.lesson_identifiable(demos, pairs[query_index]["input"]) == []


def test_pinned_profile_floor_hits_each_band():
    canonical_profiles = {_profile(pair["input"]) for pair in _pairs()}
    for band in ("easy", "medium", "hard"):
        grids = []
        for index in range(20):
            seed = _pinned_seed(band, index)
            grids.append(gen.generate(seed, seed % 7919 + index, difficulty=band))
        assert any(_profile(grid) in canonical_profiles for grid in grids), band
        assert all(gen.strict_canonical_like(grid) == [] for grid in grids)


def test_reference_probe_is_independent_and_matches_racket_on_canonical_and_generated():
    probe = _load_probe()
    canonical = _pairs()
    generated = [gen.generate(8800, index, difficulty="hard") for index in range(4)]
    grids = [pair["input"] for pair in canonical] + generated
    python_outputs = [probe.reference_output(grid) for grid in grids]
    assert python_outputs[: len(canonical)] == [pair["output"] for pair in canonical]
    assert python_outputs == probe.racket_outputs(grids)
    assert python_outputs == [gen.rule_mirror(grid) for grid in grids]


def test_shortcut_analysis_tool_reports_exact_emitted_counterexamples():
    tool = _load(HOME / "workspace" / "analyze_shortcuts.py", "shortcut_tool_54099d17f2dd")
    report = tool.analyze(use_racket=False)
    assert report["all_declared_shortcuts_fit_canonical"]
    assert report["generator_emits_counterexamples"]
    assert set(report["shortcuts"]) == set(gen.CANONICAL_SHORTCUTS)
    for name, finding in report["shortcuts"].items():
        assert finding["fits_all_canonical_pairs"], name
        witness = finding["first_generated_counterexample"]
        assert witness is not None, name
        assert witness["self_check_errors"] == []
        assert witness["authority_output"] != witness["rival_output"]
        assert witness["difference_cells"]


def test_shortcut_analysis_tool_runs_standalone():
    tool_path = HOME / "workspace" / "analyze_shortcuts.py"
    completed = subprocess.run(
        [sys.executable, str(tool_path), "--compact", "--no-racket"],
        cwd=HOME,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": ""},
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["all_declared_shortcuts_fit_canonical"]
    assert report["generator_emits_counterexamples"]
