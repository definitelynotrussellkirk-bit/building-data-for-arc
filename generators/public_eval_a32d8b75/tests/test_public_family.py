from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import unittest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SidebarStampFamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = load(HOME / 'generator.py', 'test_sidebar_generator')
        cls.a = load(HOME / 'workspace/parametric/adapter.py', 'test_sidebar_adapter')
        challenges = json.loads((ROOT / 'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())
        solutions = json.loads((ROOT / 'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())
        cls.parent = challenges['a32d8b75']
        cls.solutions = solutions['a32d8b75']

    def test_official_pairs_match_python_rule(self):
        for pair in self.parent['train']:
            self.assertEqual(self.g.solve(pair['input'], 'all'), pair['output'])
        for pair, output in zip(self.parent['test'], self.solutions):
            self.assertEqual(self.g.solve(pair['input'], 'all'), output)

    def test_default_program_is_exact_reference(self):
        self.assertEqual(self.a.program({'scope': 'all'}), (HOME / 'reference.rkt').read_text())
        self.assertEqual((HOME / 'workspace/parametric/canonical.rkt').read_text(), (HOME / 'reference.rkt').read_text())

    def test_generated_bank_is_matched_distinct_and_prefix_stable(self):
        for seed in range(20):
            bank = self.g.inputs(seed)
            self.assertEqual(len(bank), 10)
            self.assertEqual(len({repr(grid) for grid in bank}), 10)
            self.assertTrue(any(len(grid) == 30 and len(grid[0]) == 30 for grid in bank[6:]))
            all_ep = self.a.generate(seed, {'scope': 'all'}, 2, 4)
            selected_ep = self.a.generate(seed, {'scope': 'texture_indexed_component'}, 2, 4)
            self.assertEqual(
                [p['input'] for split in ('train', 'test') for p in all_ep[split]],
                [p['input'] for split in ('train', 'test') for p in selected_ep[split]],
            )
            one = self.a.generate(seed, {'scope': 'all'}, 2, 1)
            self.assertEqual(one['test'][0], all_ep['test'][0])
            self.assertTrue(all(
                self.g.solve(grid, 'all') != self.g.solve(grid, 'texture_indexed_component')
                for grid in bank
            ))

    def test_two_demo_lessons_reject_declared_rivals(self):
        for seed in range(20):
            demos = self.g.inputs(seed)[:2]
            for scope in self.g.SETTINGS:
                correct = [self.g.solve(grid, scope) for grid in demos]
                for rival in self.g.RIVALS:
                    self.assertTrue(
                        any(self.g.solve(grid, scope, rival) != want for grid, want in zip(demos, correct)),
                        (seed, scope, rival),
                    )


    def test_protected_racket_variant_tightly_crops_selected_component(self):
        """Catches rotating a selected component inside the full glyph canvas."""
        episode = self.a.generate(17, {'scope': 'texture_indexed_component'}, 2, 4)
        pair = episode['test'][0]
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in pair['input']
        ) + ")"
        with RacketBridge(timeout=30) as bridge:
            actual = bridge.eval_text(f"({wrap_rule(episode['program_solution'])} {literal})")
        self.assertEqual(actual, pair['output'])

    def test_controls_and_copy_isolation(self):
        bad = [
            (True, {'scope': 'all'}, 2, 4),
            (0, {'scope': 'all'}, 1, 4),
            (0, {'scope': 'all'}, 2, 5),
            (0, {'scope': 'bad'}, 2, 4),
            (0, None, 2, 4),
        ]
        for args in bad:
            with self.assertRaises(ValueError):
                self.a.generate(*args)
        episode = self.a.generate(3, {'scope': 'all'}, 2, 4)
        original = episode['train'][0]['input'][0][0]
        episode['train'][0]['input'][0][0] = (original + 1) % 10
        fresh = self.a.generate(3, {'scope': 'all'}, 2, 4)
        self.assertEqual(fresh['train'][0]['input'][0][0], original)


if __name__ == '__main__':
    unittest.main()
