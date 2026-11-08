"""Focused tests for the separate checkerboard-phase prototype, not approval."""
from pathlib import Path
import importlib.util
import json

import unittest
from reviewer_support import canonical_pairs, canonical_path, find_root
from arc_repl.racket_bridge import RacketBridge

ROOT = find_root(__file__)


def prototype():
    path = ROOT / "generators/18bd3cd2985e/workspace/parametric/prototype.py"
    assert path.is_file(), "The task-local phase prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("phase_prototype_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_grid(odd=False):
    g = [[0] * 9 for _ in range(7)]
    side = 5 if odd else 4
    for r in range(side):
        for c in range(side):
            if r in (0, side - 1) or c in (0, side - 1):
                g[r][c] = 2
    for r in (0, 2, 4, 6) if odd else (0, 2):
        g[r][6] = 6
    clean = [[v if c < side else 0 for c, v in enumerate(row)] for row in g]
    return g, clean



class TestPhasePrototype(unittest.TestCase):
    def test_default_is_exact_canonical_program_and_executes_canonical_labels(self):
        mod = prototype()
        sources = set()
        for line in canonical_path(ROOT).open():
            row = json.loads(line)
            if row.get("task_id") == mod.TASK_ID:
                sources.add(row["program_solution"])
        assert sources == {mod.render_program(0, root=ROOT)}
        with RacketBridge() as bridge:
            for pair in canonical_pairs(mod.TASK_ID, root=ROOT, labeled_only=True):
                assert mod.execute(bridge, mod.render_program(0, root=ROOT), pair["input"]) == pair["output"]


    def test_both_phases_execute_distinct_even_area_checkerboards(self):
        mod = prototype()
        grid, clean = fixture_grid()
        expected = [[row[:] for row in clean] for _ in range(2)]
        expected[0][1][1] = expected[0][2][2] = 6
        expected[1][1][2] = expected[1][2][1] = 6
        with RacketBridge() as bridge:
            for phase in (0, 1):
                assert mod.execute(bridge, mod.render_program(phase, root=ROOT), grid) == expected[phase]
        assert expected[0] != expected[1]


    def test_alternative_uses_floor_capacity_for_odd_area(self):
        mod = prototype()
        grid, clean = fixture_grid(odd=True)
        alternative = [row[:] for row in clean]
        for r, c in ((1, 2), (2, 1), (2, 3), (3, 2)):
            alternative[r][c] = 6
        with RacketBridge() as bridge:
            assert mod.execute(bridge, mod.render_program(0, root=ROOT), grid) == clean
            assert mod.execute(bridge, mod.render_program(1, root=ROOT), grid) == alternative


    def test_complete_episodes_refute_alternative_phase_and_separate_public_data(self):
        mod = prototype()
        assert {mod.choose_phase(seed) for seed in (0, 1)} == {0, 1}
        with RacketBridge() as bridge:
            for seed in (0, 1):
                phase = mod.choose_phase(seed)
                assert mod.episode_inputs(seed, phase) == mod.episode_inputs(seed, phase)
                episode = mod.generate_episode(seed, bridge=bridge, root=ROOT)
                assert episode["parameters"] == {"checkerboard_phase": phase}
                assert len(episode["train"]) == 3 and len(episode["test"]) == 1
                assert episode["parameter_rivals"]["status"] == "refuted_on_demonstrations"
                assert episode["parameter_rivals"]["refuting_demonstrations"]
                public = mod.public_episode(episode)
                assert set(public) == {"train", "test"}
                assert all(set(pair) == {"input", "output"} for pair in public["train"])
                assert all(set(pair) == {"input"} for pair in public["test"])
                assert all(not mod.input_issues(pair["input"], phase) for pair in episode["train"] + episode["test"])


    def test_phase_parameter_rejects_unsupported_and_coerced_values(self):
        mod = prototype()
        for value in (-1, 2, True, 0.0, "0", None):
            with self.assertRaises(ValueError):
                mod.render_program(value, root=ROOT)


if __name__ == "__main__":
    unittest.main()
