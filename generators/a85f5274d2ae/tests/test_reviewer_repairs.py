from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
for candidate in (HERE.parent, *HERE.parents):
    helper = candidate / "shared/runtime/reviewer_support.py"
    if helper.is_file():
        import sys

        sys.path.insert(0, str(helper.parent))
        break
else:  # pragma: no cover - a broken copied runtime should fail loudly
    raise RuntimeError("cannot locate reviewer_support.py")

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "a85f5274d2ae"
ROOT = find_root(__file__)
MOD, SOURCE_PATH, _SOURCE_HASH = load_selected_generator(TASK, root=ROOT)
RAW_AUTHORITY_SHA256 = "bba3b44960f207d2307568b0ce738c1631580b3372e9bcaaf1e8797de2eab789"


def _base_path() -> Path:
    for relative in (
        "shared/data/base/solutions/training/18286ef8__a85f5274d2ae.json",
        "data/base/solutions/training/18286ef8__a85f5274d2ae.json",
    ):
        path = ROOT / relative
        if path.is_file():
            return path
    raise FileNotFoundError("task base record")


def _canonical_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    return row["program_solution"]
    raise KeyError(TASK)


def _episode(seed: int, start: int, difficulty: str):
    pairs = []
    for sample_index in range(start, start + 4):
        grid = MOD.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": MOD.rule_mirror(grid)})
    return pairs


def test_generate_rejects_non_exact_or_negative_scalar_arguments():
    for bad_seed in (True, False, 1.5, "1"):
        with pytest.raises((TypeError, ValueError)):
            MOD.generate(bad_seed, 0)
    for bad_index in (True, False, 1.5, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            MOD.generate(0, bad_index)

    assert MOD.generate(0, 0) == MOD.generate(0, 0)


def test_selected_target_is_exact_canonical_text_while_archival_raw_is_preserved():
    source = _canonical_source()
    record = json.loads(_base_path().read_text(encoding="utf-8"))
    racket = record["racket_target"]

    assert racket["target_code"] == source
    assert hashlib.sha256(racket["raw_code"].encode()).hexdigest() == RAW_AUTHORITY_SHA256
    assert " ".join(racket["raw_code"].split()) == " ".join(source.split())


def test_default_curriculum_has_exact_public_support_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        signatures = [
            MOD.canonical_profile_signature(MOD.generate(417, sample_index, difficulty=difficulty))
            for sample_index in range(20)
        ]
        assert any(signature in MOD.PUBLIC_PROFILES for signature in signatures), difficulty


def test_declared_panel_shortcut_fits_canonical_and_generated_witness_refutes_it():
    rival = MOD.CANONICAL_SHORTCUTS["panel_direction_only"]
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert MOD.strict_canonical_like(pair["input"]) == []
        assert rival(pair["input"]) == pair["output"]

    witness = MOD.SEMANTIC_WITNESSES["same_panel_far_axis"]
    generated = MOD.generate(913, 0, difficulty="hard")
    assert MOD.strict_canonical_like(generated) == []
    assert witness(generated)
    assert rival(generated) != MOD.rule_mirror(generated)


def test_every_four_example_window_is_rotation_safe_and_refutes_panel_shortcut():
    witness = MOD.SEMANTIC_WITNESSES["same_panel_far_axis"]
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            episode = _episode(1200 + start, start, difficulty)
            assert sum(witness(pair["input"]) for pair in episode) >= 2
            for held_out in range(4):
                demos = [pair for index, pair in enumerate(episode) if index != held_out]
                query = episode[held_out]
                assert MOD.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    start,
                    held_out,
                    MOD.lesson_identifiable(demos, query),
                )


def _load_parametric_prototype():
    path = ROOT / f"generators/{TASK}/workspace/parametric/prototype.py"
    if not path.is_file():
        path = SOURCE_PATH.parent / "workspace/parametric/prototype.py"
    assert path.is_file(), f"missing runnable parametric prototype: {path}"
    spec = importlib.util.spec_from_file_location("_a85f5274d2ae_parametric", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_parametric_axis_tolerance_preserves_default_and_is_identifiable():
    prototype = _load_parametric_prototype()
    assert prototype.PARAMETER_NAME == "axis_tolerance"
    assert prototype.ALLOWED_TOLERANCES == (0, 1, 2)
    assert prototype.DEFAULT_TOLERANCE == 1

    canonical = _canonical_source()
    programs = {
        value: prototype.instantiate_program(canonical, value)
        for value in prototype.ALLOWED_TOLERANCES
    }
    assert programs[prototype.DEFAULT_TOLERANCE] == canonical
    assert len(set(programs.values())) == len(prototype.ALLOWED_TOLERANCES)

    probes = prototype.distinguishing_inputs(MOD)
    assert len(probes) >= 2
    for grid in probes:
        assert MOD.strict_canonical_like(grid) == []
        assert prototype.rule_mirror(grid, prototype.DEFAULT_TOLERANCE) == MOD.rule_mirror(grid)

    for selected in prototype.ALLOWED_TOLERANCES:
        labels = [prototype.rule_mirror(grid, selected) for grid in probes]
        for rival in prototype.ALLOWED_TOLERANCES:
            if rival == selected:
                continue
            rival_labels = [prototype.rule_mirror(grid, rival) for grid in probes]
            assert any(_freeze(left) != _freeze(right) for left, right in zip(labels, rival_labels))
