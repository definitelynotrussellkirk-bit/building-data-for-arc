"""Contract tests for the proposed arm-rotation parametric prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "08f1d9bdd2ef"
ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)
TASK_HOME = ROOT / "generators" / TASK_ID
PROTOTYPE_DIR = TASK_HOME / "workspace" / "parametric"
MODULE_PATH = PROTOTYPE_DIR / "arm_rotation.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "_review_arm_rotation_prototype", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return str(row["program_solution"])
    raise AssertionError("canonical program not found")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_prototype_has_runnable_module_verifier_and_documented_command():
    assert MODULE_PATH.is_file()
    assert (PROTOTYPE_DIR / "verify.py").is_file()
    readme = (PROTOTYPE_DIR / "README.md").read_text(encoding="utf-8")
    assert "python3 verify.py" in readme
    assert "proposed" in readme.lower()
    assert "unapproved" in readme.lower()


def test_parameter_contract_and_default_racket_source_are_canonical():
    prototype = _load_prototype()
    assert prototype.PROTOTYPE_STATUS == "proposed_unapproved"
    assert prototype.PARAMETER_NAME == "arm_rotation"
    assert prototype.SETTINGS == (0, 1, 2, 3)
    assert prototype.DEFAULT_SETTING == 0
    assert prototype.arm_colors(0) == (2, 3, 1, 4)
    assert prototype.arm_colors(1) == (4, 2, 3, 1)
    assert _normalized_hash(prototype.racket_program(0)) == GENERATOR.RULE_HASH
    assert prototype.racket_program(0) == _canonical_program()


def test_python_variant_preserves_geometry_and_rotates_only_arm_colors():
    prototype = _load_prototype()
    grid = GENERATOR.generate(
        13, 17, difficulty="hard", scene_family="generalized"
    )
    outputs = [prototype.apply_python(grid, setting) for setting in prototype.SETTINGS]
    assert outputs[0] == GENERATOR.rule_mirror(grid)
    assert len({json.dumps(output, separators=(",", ":")) for output in outputs}) == 4

    facts = GENERATOR._analyze(grid)["facts"]
    row_sizes = facts["row_band_sizes"]
    col_sizes = facts["col_band_sizes"]
    sample_cells = (
        (row_sizes[0] // 2, facts["sep_cols"][0] + 1 + col_sizes[1] // 2),
        (facts["sep_rows"][0] + 1 + row_sizes[1] // 2,
         facts["sep_cols"][1] + 1 + col_sizes[2] // 2),
        (facts["sep_rows"][1] + 1 + row_sizes[2] // 2,
         facts["sep_cols"][0] + 1 + col_sizes[1] // 2),
        (facts["sep_rows"][0] + 1 + row_sizes[1] // 2, col_sizes[0] // 2),
    )
    center = (
        facts["sep_rows"][0] + 1 + row_sizes[1] // 2,
        facts["sep_cols"][0] + 1 + col_sizes[1] // 2,
    )
    for setting, output in zip(prototype.SETTINGS, outputs):
        assert tuple(output[row][col] for row, col in sample_cells) == prototype.arm_colors(setting)
        assert output[center[0]][center[1]] == 6


def test_episode_chooses_one_setting_and_demos_refute_every_other_setting():
    prototype = _load_prototype()
    episode = prototype.build_episode(9137, setting=2, difficulty="medium")
    assert episode["parameter"] == {"arm_rotation": 2}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert prototype.episode_identifiability_errors(episode) == []

    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == prototype.apply_python(pair["input"], 2)
    for rival in (0, 1, 3):
        assert any(
            prototype.apply_python(pair["input"], rival) != pair["output"]
            for pair in episode["train"]
        )

    public = prototype.public_challenge(episode)
    assert "parameter" not in public
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])


def test_verifier_does_not_double_wrap_an_already_callable_racket_rule():
    import sys
    from puzzle_generators.rule_wrap import strip_rule_wrapper

    prototype = _load_prototype()
    verify_path = PROTOTYPE_DIR / "verify.py"
    spec = importlib.util.spec_from_file_location(
        "_review_arm_rotation_verifier", verify_path
    )
    assert spec is not None and spec.loader is not None
    before = list(sys.path)
    try:
        sys.path.insert(0, str(PROTOTYPE_DIR))
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
    finally:
        sys.path[:] = before

    program = prototype.racket_program(0)
    assert verifier._callable_rule_text(program) == strip_rule_wrapper(program)


def test_verifier_reuses_one_racket_session_for_all_programs_and_episodes(monkeypatch):
    """The evidence verifier should not pay one Racket startup per comparison."""
    import sys

    verify_path = PROTOTYPE_DIR / "verify.py"
    spec = importlib.util.spec_from_file_location(
        "_review_arm_rotation_verifier_reuse", verify_path
    )
    assert spec is not None and spec.loader is not None
    before = list(sys.path)
    try:
        sys.path.insert(0, str(PROTOTYPE_DIR))
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
    finally:
        sys.path[:] = before

    class FakeBridge:
        created = 0
        shutdowns = 0

        def __init__(self):
            type(self).created += 1
            self.grids = {}

        def eval_text(self, expression):
            if expression.startswith("(define __arm_rotation_rule_"):
                return None
            prefix = "(__arm_rotation_rule_"
            assert expression.startswith(prefix) and expression.endswith(")")
            body = expression[len(prefix):-1]
            setting_text, grid_name = body.split(" ", 1)
            return {"program": int(setting_text), "grid": self.grids[grid_name]}

        def define_grid(self, name, grid):
            self.grids[name] = grid

        def shutdown(self):
            type(self).shutdowns += 1

    monkeypatch.setattr(verifier, "RacketBridge", FakeBridge)
    matrix = verifier._execute_matrix(
        {0: "(rule! (lambda (g) g))", 1: "(rule! (lambda (g) g))"},
        {7: [[[0]], [[1]]], 9: [[[2]]]},
    )

    assert FakeBridge.created == 1
    assert FakeBridge.shutdowns == 1
    assert matrix[7][0] == [
        {"program": 0, "grid": [[0]]},
        {"program": 0, "grid": [[1]]},
    ]
    assert matrix[9][1] == [{"program": 1, "grid": [[2]]}]
