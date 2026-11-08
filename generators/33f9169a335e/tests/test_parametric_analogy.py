"""Behavioral tests for the separately proposed Boolean analogy family."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "analogy.py"
A = [[1, 0, 0], [0, 1, 1], [0, 0, 0]]
B = [[0, 1, 1], [1, 0, 0], [1, 1, 1]]
C = [[1, 1, 0], [0, 1, 0], [1, 0, 0]]
ZERO = [[0, 0, 0] for _ in range(3)]
WANT_IDENTITY = [[2, 2, 0], [0, 2, 0], [2, 0, 0]]
WANT_COMPLEMENT = [[0, 0, 2], [2, 0, 2], [0, 2, 2]]


def group(left, right, color):
    n = len(left)
    edge = [color] * (2 * n + 3)
    middle = [[color] + [color * v for v in a] + [color]
              + [color * v for v in b] + [color]
              for a, b in zip(left, right)]
    return [edge[:]] + middle + [edge[:]]


def fixture(operation="complement", swap_groups=False, swap_ref=False, swap_target=False):
    ref = [A, B] if operation == "complement" else [B, B]
    target = [C, ZERO]
    if swap_ref:
        ref.reverse()
    if swap_target:
        target.reverse()
    groups = [group(*ref, 7), group(*target, 2)]
    if swap_groups:
        groups.reverse()
    return groups[0] + [[0] * 9] + groups[1]


class AnalogyTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(), "proposed analogy module has not been implemented")
        spec = importlib.util.spec_from_file_location("proposed_analogy", MODULE)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_hand_complement_uses_target_palette(self):
        self.assertEqual(self.mod.python_transform(fixture(), "target"), WANT_COMPLEMENT)

    def test_hand_identity_uses_target_palette(self):
        self.assertEqual(self.mod.python_transform(fixture("identity"), "target"), WANT_IDENTITY)

    def test_comparing_source_pair_is_necessary(self):
        identity, complement = fixture("identity"), fixture("complement")
        # Only the first reference panel changes: B, target C, frames and layout stay fixed.
        changed = {(r, c) for r in range(11) for c in range(9)
                   if identity[r][c] != complement[r][c]}
        self.assertEqual(changed, {(r, c) for r in range(1, 4) for c in range(1, 4)})
        self.assertEqual(self.mod.python_transform(identity, "target"), WANT_IDENTITY)
        self.assertEqual(self.mod.python_transform(complement, "target"), WANT_COMPLEMENT)

    def test_all_group_and_panel_orderings(self):
        for swap_groups in (False, True):
            for swap_ref in (False, True):
                for swap_target in (False, True):
                    with self.subTest(g=swap_groups, r=swap_ref, t=swap_target):
                        self.assertEqual(self.mod.python_transform(
                            fixture(swap_groups=swap_groups, swap_ref=swap_ref,
                                    swap_target=swap_target), "target"), WANT_COMPLEMENT)

    def test_reference_role_changes_only_foreground_palette(self):
        self.assertEqual(self.mod.python_transform(fixture(), "reference"),
                         [[0, 0, 7], [7, 0, 7], [0, 7, 7]])
        self.assertEqual(self.mod.python_transform(fixture("identity"), "reference"),
                         [[7, 7, 0], [0, 7, 0], [7, 0, 0]])

    def test_transform_does_not_mutate_input(self):
        grid = fixture()
        before = copy.deepcopy(grid)
        self.mod.python_transform(grid, "target")
        self.assertEqual(grid, before)

    def test_malformed_geometry_cells_and_frames_are_rejected(self):
        bad = []
        g = fixture(); g.pop(); bad.append(g)
        g = fixture(); g[1].pop(); bad.append(g)
        g = fixture(); g[5][0] = 1; bad.append(g)
        g = fixture(); g[0][0] = 0; bad.append(g)
        g = fixture(); g[1][4] = 0; bad.append(g)
        g = fixture(); g[1][1] = True; bad.append(g)
        g = fixture(); g[1][1] = 7.0; bad.append(g)
        g = fixture(); g[1][1] = 4; bad.append(g)
        g = fixture(); g[1][1] = 10; bad.append(g)
        for grid in bad:
            with self.subTest(grid=grid):
                with self.assertRaises((ValueError, TypeError)):
                    self.mod.python_transform(grid, "target")

    def test_invalid_pair_roles_and_relations_are_rejected(self):
        full = [[1] * 3 for _ in range(3)]
        malformed = [
            group(A, C, 7) + [[0] * 9] + group(C, ZERO, 2),
            group(A, B, 7) + [[0] * 9] + group(C, A, 2),
            group(A, ZERO, 7) + [[0] * 9] + group(C, ZERO, 2),
            group(A, B, 7) + [[0] * 9] + group(ZERO, ZERO, 2),
            group(A, B, 7) + [[0] * 9] + group(full, ZERO, 2),
            group(A, B, 7) + [[0] * 9] + group(C, ZERO, 7),
        ]
        for grid in malformed:
            with self.subTest(grid=grid):
                with self.assertRaises((ValueError, TypeError)):
                    self.mod.python_transform(grid, "target")

    def test_sampler_counterfactual_changes_one_panel_only(self):
        left, right = self.mod.context_counterfactual()
        self.assertEqual(left, self.mod.sample_grid(17, 0, cue_mode="identity"))
        self.assertEqual(right, self.mod.sample_grid(17, 0, cue_mode="complement"))
        n = (len(left[0]) - 3) // 2
        changes = {(r, c) for r in range(len(left)) for c in range(len(left[0]))
                   if left[r][c] != right[r][c]}
        self.assertEqual(len(changes), n * n)
        self.assertEqual(len({r for r, _ in changes}), n)
        self.assertEqual(len({c for _, c in changes}), n)
        a = self.mod.python_transform(left, "target")
        b = self.mod.python_transform(right, "target")
        self.assertTrue(all(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb)))

    def test_episode_determinism_uniqueness_and_parameter_isolation(self):
        episode = self.mod.sample_episode(17)
        self.assertEqual(episode, self.mod.sample_episode(17))
        self.assertEqual(len(episode["train"]), 2)
        self.assertEqual(len(episode["test"]), 4)
        pairs = episode["train"] + episode["test"]
        self.assertEqual(len({json.dumps(p["input"]) for p in pairs}), 6)
        other = self.mod.sample_episode(900, role="reference", input_seed=17)
        self.assertEqual([p["input"] for p in pairs],
                         [p["input"] for p in other["train"] + other["test"]])
        self.assertEqual(episode["parameters"], {"output_color_role": "target"})
        self.assertEqual(other["parameters"], {"output_color_role": "reference"})
        self.assertEqual(episode["status"], "proposed")
        self.assertFalse(episode["lineage"]["relationship_verified"])

    def test_count_bounds_and_integer_validation(self):
        for name in ("demo_count", "query_count"):
            for bad in (True, False, 0, 9, 1.5, "2"):
                with self.subTest(name=name, bad=bad):
                    with self.assertRaises((ValueError, TypeError)):
                        self.mod.sample_episode(1, **{name: bad})
        for bad in (True, 1.5, "1"):
            with self.assertRaises((ValueError, TypeError)):
                self.mod.sample_episode(bad)
            with self.assertRaises((ValueError, TypeError)):
                self.mod.sample_episode(1, input_seed=bad)
        for bad in (None, "source", 1):
            with self.assertRaises((ValueError, TypeError)):
                self.mod.sample_episode(1, role=bad)
        for bad in (True, -1, 1.5):
            with self.assertRaises((ValueError, TypeError)):
                self.mod.sample_grid(1, bad)
        with self.assertRaises((ValueError, TypeError)):
            self.mod.sample_grid(1, 0, cue_mode="rotate")

    def test_demo_and_query_counts_are_independent(self):
        a = self.mod.sample_episode(3, demo_count=1, query_count=8)
        b = self.mod.sample_episode(3, demo_count=8, query_count=1)
        self.assertEqual((len(a["train"]), len(a["test"])), (1, 8))
        self.assertEqual((len(b["train"]), len(b["test"])), (8, 1))
        for episode in (a, b):
            pairs = episode["train"] + episode["test"]
            self.assertEqual(len({json.dumps(p["input"]) for p in pairs}), 9)
            self.assertTrue(all(len(p["input"]) <= 30 and len(p["input"][0]) <= 30
                                for p in pairs))


if __name__ == "__main__":
    unittest.main()
