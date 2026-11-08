from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAMETRIC = HOME / "workspace/parametric"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return load(PARAMETRIC / "adapter.py", "_6e4_adapter_protected")


@pytest.fixture(scope="module")
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator

    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    assert identity["backend"] == "racket" and identity["protected"] is True
    try:
        yield apply
    finally:
        bridge.close()


def official_pairs():
    raw = ROOT / "shared/data/raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["6e4f6532"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["6e4f6532"]
    return task["train"] + [
        {"input": pair["input"], "output": output}
        for pair, output in zip(task["test"], gold)
    ]


def test_all_official_labels_execute_through_protected_racket(evaluator):
    program = (HOME / "reference.rkt").read_text()
    assert [evaluator(program, pair["input"]) for pair in official_pairs()] == [
        pair["output"] for pair in official_pairs()
    ]
    # Positive control: the complementary setting is not an accidental alias.
    away = program.replace("(define toward #t)", "(define toward #f)", 1)
    assert any(evaluator(away, pair["input"]) != pair["output"] for pair in official_pairs())


@pytest.mark.parametrize("mode", ["toward", "away"])
@pytest.mark.parametrize("seed", [17, 43])
def test_generated_labels_execute_through_protected_racket(adapter, evaluator, mode, seed):
    episode = adapter.generate(seed, {"orientation_mode": mode}, 2, 4)
    for pair in episode["train"] + episode["test"]:
        assert evaluator(episode["program_solution"], pair["input"]) == pair["output"]


def test_selected_generator_identity_hash_and_self_check():
    tree = ast.parse((HOME / "generator.py").read_text())
    ids = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "RULE_TASK_ID" for target in node.targets)
        and isinstance(node.value, ast.Constant)
    ]
    assert ids == ["ee_6e4f6532"]
    generator = load(HOME / "generator.py", "_6e4_selected_generator")
    normalized = " ".join((HOME / "reference.rkt").read_text().split())
    assert generator.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    grid = generator.generate(seed=17, sample_index=0, difficulty="hard")
    assert generator.self_check(grid) == []
    assert grid == generator.generate(seed=17, sample_index=0, difficulty="hard")
    assert grid != generator.generate(seed=17, sample_index=1, difficulty="hard")
    with pytest.raises(ValueError):
        generator.generate(seed=17, unknown=1)
