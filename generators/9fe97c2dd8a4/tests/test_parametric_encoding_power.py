from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge

TASK_ID = "9fe97c2dd8a4"
HERE = Path(__file__).resolve()


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load(HERE.parents[1] / "generator.py", "parametric_selected_generator")
prototype = _load(
    HERE.parents[1] / "workspace" / "parametric" / "prototype.py",
    "parametric_encoding_power_prototype",
)


def test_default_program_is_canonical_and_alternative_changes_executed_labels():
    assert prototype.ALLOWED_POWERS == (1, 2)
    assert prototype.DEFAULT_POWER == 2
    assert prototype.render_program(2) == prototype.canonical_program()

    grid = [
        [0, 0, 0, 0, 5, 0],
        [0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [3, 3, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert gen.self_check(grid) == []

    with RacketBridge() as bridge:
        linear = prototype.execute(grid, prototype.render_program(1), bridge)
        squared = prototype.execute(grid, prototype.render_program(2), bridge)

    assert squared == gen.rule_mirror(grid)
    assert linear != squared


def test_complete_episodes_fix_one_power_and_refute_the_other_setting():
    with RacketBridge() as bridge:
        episodes = [
            prototype.generate_episode(
                17,
                encoding_power=power,
                difficulty="medium",
                n_train=3,
                n_test=2,
                bridge=bridge,
            )
            for power in prototype.ALLOWED_POWERS
        ]

    for episode, power in zip(episodes, prototype.ALLOWED_POWERS, strict=True):
        assert episode["parameters"] == {"encoding_power": power}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 2
        assert episode["demonstrations_refute"] == [3 - power]
        assert all(pair["settings_disagree"] for pair in episode["train"])
        assert all(pair["settings_disagree"] for pair in episode["test"])

        public = prototype.public_challenge(episode)
        assert len(public["train"]) == 3
        assert len(public["test"]) == 2
        assert all("output" not in pair for pair in public["test"])
        assert "parameters" not in public
        assert "program" not in public
        assert "rival_outputs" not in public
