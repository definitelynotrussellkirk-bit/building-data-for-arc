"""Contract tests for the task-local orientation-scope prototype."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "d09fae8197f6"
TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / "workspace" / "parametric" / "prototype.py"
BUILDER = TASK_HOME / "workspace" / "parametric" / "build_evidence.py"
ROOT = find_root(__file__)


def _load_module(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_prototype():
    return _load_module(PROTOTYPE, "parametric_orientation_scope_d09fae8197f6")


def _canonical_program() -> str:
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                programs.append(record["program_solution"])
    assert programs, f"missing canonical record for {TASK_ID}"
    assert len(set(programs)) == 1, "canonical descendants disagree on rule text"
    return programs[0]


def _all_pairs(episode):
    return [*episode["train"], *episode["test"]]


def test_declares_one_bounded_episode_level_parameter():
    """Catches a renamed, widened, or per-pair parameter contract."""
    proto = _load_prototype()
    assert proto.TASK_ID == TASK_ID
    assert proto.PARAMETERS == {
        "orientation_scope": {
            "allowed": ("dihedral", "rotations"),
            "default": "dihedral",
            "selected_once_per_episode": True,
        }
    }


def test_default_program_is_exact_canonical_and_rotations_changes_only_scope():
    """Catches canonical drift or an alternative that changes another rule clause."""
    proto = _load_prototype()
    canonical = _canonical_program()
    anchor = "(orientations (list t0 t1 t2 t3 t4 t5 t6 t7))"
    replacement = "(orientations (list t0 t1 t2 t3))"
    assert canonical.count(anchor) == 1
    assert proto.racket_program("dihedral", root=ROOT) == canonical
    assert proto.racket_program("rotations", root=ROOT) == canonical.replace(
        anchor, replacement, 1
    )


@pytest.mark.parametrize("bad_scope", [None, True, 0, "", "DIHEDRAL", "all"])
def test_orientation_scope_is_strictly_bounded(bad_scope):
    """Catches permissive aliases or Python-bool acceptance."""
    proto = _load_prototype()
    with pytest.raises(ValueError, match="orientation_scope"):
        proto.racket_program(bad_scope, root=ROOT)
    with pytest.raises(ValueError, match="orientation_scope"):
        proto.apply_python([[4]], bad_scope)
    with pytest.raises(ValueError, match="orientation_scope"):
        proto.generate_episode(7, orientation_scope=bad_scope, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, -1, 1.0, "1"])
def test_episode_seed_is_a_nonnegative_python_integer(bad_seed):
    """Catches bool coercion, negative seeds, and implicit numeric conversion."""
    proto = _load_prototype()
    with pytest.raises(ValueError, match="seed"):
        proto.generate_episode(bad_seed, root=ROOT)


@pytest.mark.parametrize(
    ("demo_count", "query_count"),
    [(True, 4), (0, 4), (9, 4), (3, True), (3, 0), (3, 5)],
)
def test_demo_and_query_counts_are_separate_and_bounded(demo_count, query_count):
    """Catches cloned/padded episodes and accidental bool count acceptance."""
    proto = _load_prototype()
    with pytest.raises(ValueError, match="count"):
        proto.generate_episode(
            17,
            root=ROOT,
            demo_count=demo_count,
            query_count=query_count,
        )


@pytest.mark.parametrize("scope", ["dihedral", "rotations"])
def test_each_setting_builds_a_deterministic_four_query_identifiable_episode(scope):
    """Catches per-pair resampling, duplicate inputs, weak rivals, or fewer queries."""
    proto = _load_prototype()
    first = proto.generate_episode(
        2026102301,
        orientation_scope=scope,
        root=ROOT,
        demo_count=3,
        query_count=4,
    )
    second = proto.generate_episode(
        2026102301,
        orientation_scope=scope,
        root=ROOT,
        demo_count=3,
        query_count=4,
    )
    assert first == second
    assert first["parameter_draw_count"] == 1
    assert first["parameter"] == {"orientation_scope": scope}
    assert len(first["train"]) == 3
    assert len(first["test"]) == 4

    pairs = _all_pairs(first)
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    opposite = "rotations" if scope == "dihedral" else "dihedral"
    visible_inputs = {json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}
    assert len(visible_inputs) == 7

    for pair in pairs:
        grid = pair["input"]
        assert generator.self_check(grid) == []
        assert proto.apply_python(grid, scope) == pair["output"]
        assert proto.apply_python(grid, opposite) != pair["output"]
        assert proto.apply_python(grid, "rotations") != grid
        assert proto.apply_python(grid, "dihedral") != grid
        assert proto.apply_python(grid, "dihedral") == generator._rule_output(grid)


def test_generate_episode_accepts_a_relative_repo_root():
    """Catches absolute/relative path mixing in private source provenance."""
    proto = _load_prototype()
    relative_root = Path(os.path.relpath(ROOT, Path.cwd()))
    episode = proto.generate_episode(19, root=relative_root, demo_count=1, query_count=1)
    assert episode["source"]["generator_path"] == (
        "generators/d09fae8197f6/generator.py"
    )


def test_materialized_programs_execute_in_the_bundled_racket_runtime():
    """Catches a Python-only prototype or malformed Racket materialization."""
    proto = _load_prototype()
    builder = _load_module(BUILDER, "orientation_scope_evidence_d09fae8197f6")
    episode = proto.generate_episode(
        314159,
        orientation_scope="dihedral",
        root=ROOT,
        demo_count=1,
        query_count=1,
    )
    grid = episode["train"][0]["input"]
    outputs = {}
    runtime_identity = None
    for scope in ("dihedral", "rotations"):
        actual, runtime = builder.execute_program(
            proto.racket_program(scope, root=ROOT), [grid]
        )
        runtime_identity = runtime_identity or runtime
        assert runtime == runtime_identity
        assert actual == [proto.apply_python(grid, scope)]
        outputs[scope] = actual[0]
    assert outputs["dihedral"] != outputs["rotations"]
