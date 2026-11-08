"""Tests of the separate proposed reflection-axis prototype, not canonical approval."""
from pathlib import Path
import importlib.util
import json

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def prototype():
    assert PROTOTYPE.is_file(), "episode-level reflection-axis prototype must exist"
    spec = importlib.util.spec_from_file_location("parametric_reflection", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_materialized_axis_rules_execute_different_expected_outputs():
    p = prototype()
    grid = [[0, 7, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    with p.RacketBridge() as bridge:
        main = p.execute(grid, p.render_program("main_diagonal"), bridge)
        anti = p.execute(grid, p.render_program("anti_diagonal"), bridge)
    assert main == [[0, 7, 0, 0], [7, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert anti == [[0, 7, 0, 0], [0, 0, 0, 0], [0, 0, 0, 7], [0, 0, 0, 0]]


@pytest.mark.parametrize("axis", ["main_diagonal", "anti_diagonal"])
def test_episode_rule_is_fixed_and_demos_refute_declared_parameter_rival(axis):
    p = prototype()
    with p.RacketBridge() as bridge:
        episode = p.generate_episode(23, reflection_axis=axis, bridge=bridge)
        assert episode == p.generate_episode(23, reflection_axis=axis, bridge=bridge)
        assert episode["parameters"] == {"reflection_axis": axis}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 2
        rival = next(value for value in p.ALLOWED_AXES if value != axis)
        assert any(p.execute(pair["input"], p.render_program(rival), bridge) != pair["output"]
                   for pair in episode["train"])
        for pair in episode["train"] + episode["test"]:
            assert p.execute(pair["input"], episode["program"], bridge) == pair["output"]
            size = len(pair["input"])
            assert 4 <= size <= 10
            for r, row in enumerate(pair["input"]):
                for c, value in enumerate(row):
                    if value:
                        assert pair["input"][c][r] == 0
                        assert pair["input"][size - 1 - c][size - 1 - r] == 0
        public = p.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert public["train"] == episode["train"]
        assert public["test"] == [{"input": pair["input"]} for pair in episode["test"]]
        assert "program" not in json.dumps(public)


def test_seeded_parameter_choice_is_episode_level_and_reproducible():
    p = prototype()
    with p.RacketBridge() as bridge:
        first = p.generate_episode(5, bridge=bridge)
        assert first == p.generate_episode(5, bridge=bridge)
        assert first["parameters"]["reflection_axis"] in p.ALLOWED_AXES


def test_invalid_parameter_and_counts_fail_explicitly():
    p = prototype()
    with pytest.raises(ValueError):
        p.render_program("horizontal")
    with pytest.raises(ValueError):
        p.generate_episode(0, reflection_axis="horizontal")
    with pytest.raises(ValueError):
        p.generate_episode(0, n_train=0)


def test_cli_retains_two_complete_public_and_private_episodes(tmp_path):
    import subprocess
    import sys
    result = subprocess.run([sys.executable, str(PROTOTYPE), "--seed", "23", "--out", str(tmp_path / "evidence")],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    receipt = json.loads((tmp_path / "evidence/receipt.json").read_text())
    assert receipt["complete_episodes"] == 2
    assert receipt["all_labels_and_rivals_executed_in_racket"] is True
    for index in range(2):
        public = json.loads((tmp_path / f"evidence/public-{index}.json").read_text())
        private = json.loads((tmp_path / f"evidence/private-{index}.json").read_text())
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3
        assert len(public["test"]) == 2
        assert all(set(query) == {"input"} for query in public["test"])
        assert (tmp_path / f"evidence/program-{index}.rkt").read_text() == private["program"]


def test_import_and_selected_generator_share_manifest_runtime_dependencies(tmp_path):
    """A copied repo mirror must not shadow a staged runtime's selected packages."""
    import shutil
    import subprocess
    import sys

    root = PROTOTYPE.parents[4]
    dependencies = root if (root / "RUNTIME_MANIFEST.json").is_file() else root / "shared/runtime"
    stage = tmp_path / "stage"
    stage.mkdir()
    for package in ("puzzle_generators", "arc_repl"):
        shutil.copytree(dependencies / package, stage / package,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(dependencies / "reviewer_support.py", stage / "reviewer_support.py")
    mirror = stage / "shared/runtime"
    for package, files in {"puzzle_generators": ("__init__.py", "base.py", "rule_wrap.py"),
                           "arc_repl": ("__init__.py", "racket_bridge.py")}.items():
        (mirror / package).mkdir(parents=True)
        for name in files:
            shutil.copy2(dependencies / package / name, mirror / package / name)
    copied_prototype = stage / "generators/e58027e9749f/workspace/parametric/prototype.py"
    copied_prototype.parent.mkdir(parents=True)
    shutil.copy2(PROTOTYPE, copied_prototype)
    selected = stage / "puzzle_generators/per_puzzle/e58027e9749f/generator.py"
    selected.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HOME / "generator.py", selected)
    (stage / "data/canonical").mkdir(parents=True)
    (stage / "data/canonical/puzzles.jsonl").write_text("")
    (stage / "RUNTIME_MANIFEST.json").write_text(json.dumps({"files": [{
        "library_path": "generators/e58027e9749f/generator.py",
        "runtime_path": "puzzle_generators/per_puzzle/e58027e9749f/generator.py"}]}))
    script = '''
from pathlib import Path
import importlib.util
import sys
stage = Path(sys.argv[1])
sys.path.insert(0, str(stage))
path = stage / 'generators/e58027e9749f/workspace/parametric/prototype.py'
spec = importlib.util.spec_from_file_location('staged_prototype', path)
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)
from reviewer_support import load_selected_generator
module, source, digest = load_selected_generator('e58027e9749f', root=stage)
import puzzle_generators.base
assert Path(puzzle_generators.base.__file__).is_relative_to(stage / 'puzzle_generators')
assert source == stage / 'puzzle_generators/per_puzzle/e58027e9749f/generator.py'
assert module.self_check(module.generate(3, 0, size=5, cell_count=2)) == []
print('prototype and selected generator use the same manifest-selected runtime')
'''
    result = subprocess.run([sys.executable, "-I", "-c", script, str(stage)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
