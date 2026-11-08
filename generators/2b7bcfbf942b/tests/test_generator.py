"""Task-local source-bound regression suite for 2b7bcfbf942b."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_PROFILES,
    canonical,
    canonical_pairs,
    canonical_sizes_only_output,
    frames_only_output,
    geometry_output,
    load_generator,
    novel_size_witness,
    observed,
    racket_outputs,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_accepts_every_canonical_input_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "de72b7a33ad3"


def test_active_authority_text_matches_canonical_program_exactly():
    authority = json.loads((ROOT / "shared/data/base/solutions/banks/0f1ff2289d6f/M73__2b7bcfbf942b.json").read_text())
    assert authority["racket_target"]["target_code"].strip() == canonical()["program_solution"].strip()


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("style", ["frame", "open", "cross"])
def test_exact_overrides_are_independent_in_every_band(band, style):
    options = {"grid_h": 8, "grid_w": 9, "n_objects": 3, "object_style": style}
    g = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(g) == []
    assert {key: observed(g)[key] for key in options} == options
    assert gen.observe_overrides(g) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 17),
        ("grid_w", 8),
        ("grid_w", 19),
        ("n_objects", 0),
        ("n_objects", 4),
        ("object_style", "solid"),
        ("grid_h", True),
        ("grid_w", 9.5),
        ("n_objects", "2"),
        ("object_style", 3),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_cycle_covers_canonical_profiles_and_rival_counterexamples(band):
    profiles = set()
    styles = set()
    counts = set()
    boxes = set()
    positions = set()
    inputs = set()
    for i in range(120):
        g = gen.generate(8000 + i, i, difficulty=band)
        assert gen.self_check(g) == []
        assert g == gen.generate(8000 + i, i, difficulty=band)
        obs = observed(g)
        profiles.add((obs["grid_h"], obs["grid_w"], obs["palette_size"]))
        styles.add(obs["object_style"])
        counts.add(obs["n_objects"])
        boxes.update((bh, bw) for bh, bw, _, _ in obs["bboxes"])
        positions.update((r, c) for _, _, r, c in obs["bboxes"])
        inputs.add(json.dumps(g, separators=(",", ":")))
    assert CANONICAL_PROFILES <= profiles
    assert styles == {"frame", "open", "cross"}
    assert counts == {1, 2, 3}
    assert len(boxes) >= 15
    assert len(positions) >= 12
    assert len(inputs) >= 110


def test_three_consecutive_demos_always_refute_frames_only_shortcut():
    for start in range(80):
        grids = [gen.generate(31 + start, start + offset) for offset in range(3)]
        assert any(geometry_output(g) != frames_only_output(g) for g in grids)
        demos = [{"input": g, "output": geometry_output(g)} for g in grids]
        query_grid = gen.generate(31 + start, start + 3)
        query = {"input": query_grid, "output": geometry_output(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_declared_shortcuts_fit_canonical_and_witnesses_disagree():
    assert all(frames_only_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
    assert all(canonical_sizes_only_output(pair["input"]) == pair["output"] for pair in canonical_pairs())

    frame_witness = witness_input()
    size_witness = novel_size_witness()
    assert gen.self_check(frame_witness) == []
    assert gen.self_check(size_witness) == []
    assert geometry_output(frame_witness) != frames_only_output(frame_witness)
    assert geometry_output(size_witness) != canonical_sizes_only_output(size_witness)
    assert gen.SEMANTIC_WITNESSES["non_frame_object"](frame_witness)
    assert gen.SEMANTIC_WITNESSES["novel_bbox_size"](size_witness)
    assert gen.SEMANTIC_RIVALS["complete_frames_only"](frame_witness) == frames_only_output(frame_witness)
    assert gen.SEMANTIC_RIVALS["canonical_bbox_sizes_only"](size_witness) == canonical_sizes_only_output(size_witness)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)], [[10] * 9 for _ in range(8)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_validator_rejects_destructive_mutations():
    base = gen.generate(440, 8, grid_h=12, grid_w=14, n_objects=2, object_style="frame")
    mutations = []
    g = deepcopy(base); g[0][0] = 9; mutations.append(g)
    g = deepcopy(base)
    hit = next((r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value)
    g[hit[0]][hit[1]] = 0; mutations.append(g)
    g = deepcopy(base)
    hit = next((r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value)
    g[hit[0]][hit[1]] = 10; mutations.append(g)
    for changed in mutations:
        assert gen.self_check(changed)


def test_keyed_rng_is_independent_of_python_hash_seed():
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


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [witness_input(), novel_size_witness()]
    grids += [gen.generate(1900 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(36)]
    assert racket_outputs(grids) == [geometry_output(g) for g in grids]


def test_lesson_probe_decodes_canonical_grids_for_shortcut_checks():
    import importlib.util
    path = HOME / "workspace" / "lesson_probe.py"
    spec = importlib.util.spec_from_file_location("lesson_probe_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    pairs = module._canonical_pairs(ROOT / "shared/data/canonical/puzzles.jsonl")
    assert pairs and isinstance(pairs[0]["input"][0], list)
    assert type(pairs[0]["input"][0][0]) is int
