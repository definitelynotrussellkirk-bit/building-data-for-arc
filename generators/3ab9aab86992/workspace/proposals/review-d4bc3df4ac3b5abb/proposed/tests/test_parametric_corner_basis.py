"""Focused tests for the proposed episode-level ``corner_basis`` prototype."""
from __future__ import annotations

from functools import cache
import hashlib
import importlib.util
import json
from pathlib import Path

import sys

import pytest

from reviewer_support import find_root


TASK_ID = "3ab9aab86992"
ROOT = find_root(__file__)
SELECTED_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
_SOURCE_SHA = hashlib.sha256(SELECTED_SOURCE.read_bytes()).hexdigest()


def _load_task_generator():
    dependency_root = ROOT / "shared" / "runtime"
    spec = importlib.util.spec_from_file_location(
        f"parametric_test_generator_{_SOURCE_SHA}", SELECTED_SOURCE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    try:
        sys.path.insert(0, str(dependency_root))
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = before
    return module


GEN = _load_task_generator()
MANIFEST = ROOT / "RUNTIME_MANIFEST.json"
if MANIFEST.is_file():
    identity = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    entries = [
        row
        for row in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
        if row.get("library_path") == identity
    ]
    entries.sort(key=lambda row: row.get("runtime_path") == identity)
    assert entries, "portable runtime must retain the parametric prototype"
    PROTOTYPE_PATH = ROOT / entries[0]["runtime_path"]
else:
    PROTOTYPE_PATH = SELECTED_SOURCE.parent / "workspace/parametric/prototype.py"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "corner-basis parametric prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "3ab9aab86992_corner_basis_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_episode_level_seed_choice():
    p = prototype()
    assert p.PARAMETER == {
        "name": "corner_basis",
        "values": ["elbow", "missing"],
        "default": "elbow",
        "input_constraints": (
            "unchanged tiny-L grammar; demonstrations use incomplete orientation sets "
            "or distinct colors so opposite-corner settings differ"
        ),
    }
    assert {p.choose_parameters(seed)["corner_basis"] for seed in range(16)} == {
        "elbow",
        "missing",
    }
    assert p.choose_parameters(19) == p.choose_parameters(19)
    with pytest.raises(TypeError, match="episode seed"):
        p.choose_parameters(True)


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    p = prototype()
    canonical = p.canonical_record()
    assert p.racket_program("elbow") == canonical["program_solution"]
    assert p.racket_program("missing") != p.racket_program("elbow")
    assert p.rule_sha256("elbow") == hashlib.sha256(
        canonical["program_solution"].encode()
    ).hexdigest()
    with pytest.raises(ValueError, match="corner_basis"):
        p.racket_program("random")


def test_shared_lawful_inputs_distinguish_both_settings():
    p = prototype()
    for sample_index, n_corners in enumerate((1, 2, 3, 4)):
        grid = GEN.generate(
            601,
            sample_index,
            canvas_size=(5, 7, 9, 11)[sample_index],
            n_corners=n_corners,
            palette_size=n_corners,
        )
        assert GEN.self_check(grid) == []
        elbow = p.python_reference(grid, corner_basis="elbow")
        missing = p.python_reference(grid, corner_basis="missing")
        assert elbow == GEN.rule_mirror(grid)
        assert elbow != missing


@pytest.mark.parametrize("basis", ["elbow", "missing"])
def test_complete_episode_is_parameter_identifiable_and_public_view_is_redacted(basis):
    p = prototype()
    episode = p.build_episode(73, corner_basis=basis)
    public = p.public_challenge(episode)
    rival = next(value for value in p.ALLOWED_CORNER_BASES if value != basis)

    assert episode["parameter"] == {"corner_basis": basis}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert p.parameter_rival_findings(episode) == []
    assert all(
        p.python_reference(pair["input"], corner_basis=rival) != pair["output"]
        for pair in episode["train"]
    )
    assert set(public) == {"schema", "train", "test"}
    assert set(public["test"][0]) == {"input"}
    serialized = json.dumps(public, sort_keys=True)
    assert "corner_basis" not in serialized
    assert "program" not in serialized


def test_racket_executes_both_exact_programs_on_cross_setting_witness():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    episode = p.build_episode(91, corner_basis="elbow")
    grid = episode["train"][0]["input"]
    with RacketBridge(max_calls_before_restart=32) as bridge:
        outputs = {
            basis: p.execute(bridge, p.racket_program(basis), grid)
            for basis in p.ALLOWED_CORNER_BASES
        }
    assert outputs["elbow"] == p.python_reference(grid, corner_basis="elbow")
    assert outputs["missing"] == p.python_reference(grid, corner_basis="missing")
    assert outputs["elbow"] != outputs["missing"]
