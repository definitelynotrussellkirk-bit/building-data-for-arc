"""Bounded tests of the task-local proposed prototype, not production approval.

Run from a repository/runtime with its included Racket wrapper.  The independent
oracle enumerates rectangles through summed-area tables, rather than using the
prototype's winner-selection or output-rendering helpers.
"""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

TASK_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = TASK_DIR / "workspace" / "parametric" / "rectangle_modes.py"


def load_prototype():
    if not MODULE_PATH.is_file():
        raise AssertionError("missing task-local parametric prototype: " + str(MODULE_PATH))
    for ancestor in TASK_DIR.parents:
        helper = ancestor / "shared" / "runtime" / "reviewer_support.py"
        if helper.is_file():
            sys.path.insert(0, str(helper.parent))
            break
        if (ancestor / "reviewer_support.py").is_file():
            sys.path.insert(0, str(ancestor))
            break
    spec = importlib.util.spec_from_file_location("_test_rectangle_modes_061566027b67", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def repository_root():
    for ancestor in TASK_DIR.parents:
        for relative in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
            if (ancestor / relative).is_file():
                return ancestor
    raise AssertionError("canonical ledger absent from the test's own tree")


def independent_rectangle(grid):
    """Find the unique maximum by independent exhaustive prefix-sum queries."""
    prefixes = {}
    for color in range(1, 10):
        prefix = [[0] * 17 for _ in range(17)]
        for row in range(16):
            for col in range(16):
                prefix[row + 1][col + 1] = (int(grid[row][col] == color)
                    + prefix[row][col + 1] + prefix[row + 1][col] - prefix[row][col])
        prefixes[color] = prefix
    best_area, winners = 0, []
    for top in range(16):
        for left in range(16):
            color = grid[top][left]
            if color == 0:
                continue
            prefix = prefixes[color]
            for bottom in range(top, 16):
                for right in range(left, 16):
                    area = (bottom - top + 1) * (right - left + 1)
                    if area < best_area:
                        continue
                    total = (prefix[bottom + 1][right + 1] - prefix[top][right + 1]
                             - prefix[bottom + 1][left] + prefix[top][left])
                    if total != area:
                        continue
                    candidate = (top, left, bottom, right, color)
                    if area > best_area:
                        best_area, winners = area, [candidate]
                    else:
                        winners.append(candidate)
    if len(winners) != 1:
        raise AssertionError("test input lacks a unique maximum rectangle: " + repr(winners))
    return winners[0]


def independent_output(grid, shape_mode="solid", paint_color=None):
    top, left, bottom, right, source_color = independent_rectangle(grid)
    color = source_color if paint_color is None else paint_color
    result = [[0] * 16 for _ in range(16)]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if shape_mode == "solid" or row in (top, bottom) or col in (left, right):
                result[row][col] = color
    return result


def visible_key(grid):
    return tuple(tuple(row) for row in grid)


def parameter_key(value):
    return value["shape_mode"], value["paint_color"]


class Parametric061566027b67Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = load_prototype()
        from reviewer_support import canonical_pairs, public_challenge_bytes
        cls.public_bytes = staticmethod(public_challenge_bytes)
        cls.root = repository_root()
        cls.canonical = canonical_pairs("061566027b67", root=cls.root)
        cls.default = cls.prototype.Parameters()
        cls.alternate = cls.prototype.Parameters(shape_mode="outline", paint_color=8)
        # Fourteen Racket-labeled pairs in total; the rest of this suite is local.
        cls.episode = cls.prototype.build_episode(5166027, cls.default)
        cls.outlined = cls.prototype.build_episode(5166028, cls.alternate, train_count=3, test_count=4)

    def test_exact_canonical_authority_and_canonical_labels_are_preserved(self):
        solution = self.root / "shared/data/base/solutions/training/91714a58__061566027b67.json"
        if not solution.is_file():
            solution = self.root / "data/base/solutions/training/91714a58__061566027b67.json"
        authority = json.loads(solution.read_text())["racket_target"]["raw_code"]
        self.assertEqual(self.prototype.canonical_program(), authority)
        self.assertEqual(self.prototype.materialize_program(self.default), authority)
        for pair in self.canonical:
            with self.subTest(pair=pair.get("pair_index"), split=pair.get("split")):
                original = copy.deepcopy(pair["input"])
                self.assertEqual(self.prototype.solve_python(original, self.default), pair["output"])
                self.assertEqual(independent_output(original), pair["output"])
                self.assertEqual(original, pair["input"])

    def test_all_twenty_settings_execute_distinct_bounded_rules(self):
        self.assertTrue(dataclasses.is_dataclass(self.default))
        expected = {(shape, paint) for shape in ("solid", "outline") for paint in (None, *range(1, 10))}
        actual = {(p.shape_mode, p.paint_color) for p in self.prototype.SETTINGS}
        self.assertEqual(len(self.prototype.SETTINGS), 20)
        self.assertEqual(actual, expected)
        grids = [pair["input"] for pair in self.episode["train"][:2]]
        programs = set()
        behaviors = set()
        for params in self.prototype.SETTINGS:
            programs.add(self.prototype.materialize_program(params))
            outputs = []
            for grid in grids:
                got = self.prototype.solve_python(grid, params)
                self.assertEqual(got, independent_output(grid, params.shape_mode, params.paint_color))
                outputs.append(visible_key(got))
            behaviors.add(tuple(outputs))
        self.assertEqual(len(programs), 20)
        self.assertEqual(len(behaviors), 20, "two differently colored thick demos identify all settings")
        for bad in ("", "border", "SOLID", None, True, 1):
            with self.subTest(shape=bad), self.assertRaises((TypeError, ValueError)):
                self.prototype.Parameters(shape_mode=bad)
        for bad in (True, False, 0, 10, -1, 1.0, "1", [], {}):
            with self.subTest(paint=bad), self.assertRaises((TypeError, ValueError)):
                self.prototype.Parameters(paint_color=bad)

    def test_thick_outline_clears_interior_and_attached_tabs(self):
        for pair in self.outlined["train"][:2]:
            grid, output = pair["input"], pair["output"]
            top, left, bottom, right, color = independent_rectangle(grid)
            self.assertGreaterEqual(bottom - top + 1, 3)
            self.assertGreaterEqual(right - left + 1, 3)
            self.assertEqual(output, independent_output(grid, "outline", 8))
            self.assertEqual(output[top + 1][left + 1], 0)
            self.assertNotEqual(output, independent_output(grid, "solid", 8))
            attached = [(r, c) for r in range(16) for c in range(16)
                        if grid[r][c] == color and not (top <= r <= bottom and left <= c <= right)
                        and any(top <= r + dr <= bottom and left <= c + dc <= right
                                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))]
            self.assertEqual(len(attached), 1)
            for row, col in attached:
                self.assertEqual(output[row][col], 0)

    def test_episode_labels_queries_and_private_program_receipt(self):
        for episode, params in ((self.episode, self.default), (self.outlined, self.alternate)):
            self.assertEqual(len(episode["train"]), 3)
            self.assertEqual(len(episode["test"]), 4)
            self.assertEqual(episode["parameters"], dataclasses.asdict(params))
            self.assertEqual(episode["program"], self.prototype.materialize_program(params))
            self.assertEqual(episode["program_sha256"], hashlib.sha256(episode["program"].encode()).hexdigest())
            self.assertIn("seed", episode)
            self.assertIn("certificate", episode)
            self.assertEqual(episode["source_hashes"]["prototype"], hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest())
            self.assertEqual(episode["source_hashes"]["selected_generator"], hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest())
            self.assertTrue(all(len(digest) == 64 and int(digest, 16) >= 0 for digest in episode["source_hashes"].values()))
            keys = [visible_key(pair["input"]) for split in ("train", "test") for pair in episode[split]]
            self.assertEqual(len(keys), len(set(keys)))
            demo_rects = [independent_rectangle(pair["input"]) for pair in episode["train"][:2]]
            self.assertEqual([tuple(sorted((r[2] - r[0] + 1, r[3] - r[1] + 1))) for r in demo_rects], [(3, 3), (3, 4)])
            self.assertNotEqual(demo_rects[0][-1], demo_rects[1][-1])
            query_profiles = []
            for pair in episode["test"]:
                r = independent_rectangle(pair["input"])
                query_profiles.append(tuple(sorted((r[2] - r[0] + 1, r[3] - r[1] + 1))))
            self.assertEqual(set(query_profiles), {(2, 7), (3, 4), (3, 3), (2, 6)})
            for split in ("train", "test"):
                for pair in episode[split]:
                    self.assertEqual(pair["output"], independent_output(pair["input"], params.shape_mode, params.paint_color))

    def test_certificate_eliminates_with_demo_outputs_only(self):
        for episode, params in ((self.episode, self.default), (self.outlined, self.alternate)):
            train = episode["train"]
            query_inputs = [pair["input"] for pair in episode["test"]]
            expected = [dataclasses.asdict(p) for p in self.prototype.SETTINGS
                        if all(self.prototype.solve_python(d["input"], p) == d["output"] for d in train)]
            self.assertEqual(expected, [dataclasses.asdict(params)])
            certificate = self.prototype.demo_certificate(train, query_inputs, params)
            self.assertEqual({parameter_key(p) for p in certificate["survivors"]}, {parameter_key(p) for p in expected})
            self.assertEqual(len(certificate["per_query"]), 4)
            self.assertTrue(all(type(q["identified"]) is bool and q["identified"] for q in certificate["per_query"]))
        # One source-colored demo cannot distinguish source color from that fixed color.
        one_demo = self.episode["train"][:1]
        color = independent_rectangle(one_demo[0]["input"])[-1]
        queries = [self.episode["train"][1]["input"]]
        ambiguous = self.prototype.demo_certificate(one_demo, queries, self.default)
        self.assertEqual({parameter_key(p) for p in ambiguous["survivors"]}, {("solid", None), ("solid", color)})
        self.assertIs(ambiguous["per_query"][0]["identified"], False)

    def test_invalid_original_domain_and_boolean_cells_are_rejected(self):
        grid = self.episode["train"][0]["input"]
        bad_cell = copy.deepcopy(grid)
        bad_cell[0][0] = True
        bad_float = copy.deepcopy(grid)
        bad_float[0][0] = 1.0
        bad_color = copy.deepcopy(grid)
        bad_color[0][0] = 10
        missing_palette = [[8 if value == 9 else value for value in row] for row in grid]
        for malformed in (None, [], grid[:15], grid + [grid[0]], [row[:15] for row in grid],
                          bad_cell, bad_float, bad_color, missing_palette, [[0] * 16 for _ in range(16)]):
            with self.subTest(grid=repr(malformed)[:60]), self.assertRaises((TypeError, ValueError)):
                self.prototype.solve_python(malformed, self.default)
        for count_name, invalid in (("train_count", 1), ("train_count", 17), ("test_count", 0),
                                    ("test_count", 17), ("train_count", True), ("test_count", False),
                                    ("train_count", 3.0), ("test_count", "4")):
            with self.subTest(count=count_name, value=invalid), self.assertRaises((TypeError, ValueError)):
                self.prototype.build_episode(17, self.default, **{count_name: invalid})

    def test_public_identity_and_writer_are_visible_only_and_hash_sorted(self):
        episodes = [self.outlined, self.episode]
        expected = {hashlib.sha256(self.public_bytes(e)).hexdigest(): self.public_bytes(e) for e in episodes}
        changed = copy.deepcopy(self.episode)
        changed["seed"] = -9999
        changed["parameters"] = {"shape_mode": "outline", "paint_color": 1}
        changed["program"] = "private alternative source"
        changed["program_sha256"] = "0" * 64
        changed["certificate"] = {"private": "changed"}
        changed["extra_private_metadata"] = [1, 2, 3]
        for pair in changed["test"]:
            pair["output"] = [[9] * 16 for _ in range(16)]
        self.assertEqual(self.public_bytes(changed), self.public_bytes(self.episode))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "batch"
            receipt = self.prototype.write_batch(episodes, out)
            self.assertIsInstance(receipt, dict)
            public_files = list((out / "public").glob("*.json"))
            self.assertEqual({p.stem for p in public_files}, set(expected))
            self.assertEqual([entry["id"] for entry in receipt["public"]], sorted(expected))
            self.assertEqual(len(public_files), 2)
            for path in public_files:
                data = path.read_bytes()
                self.assertEqual(data, expected[path.stem])
                self.assertEqual(hashlib.sha256(data).hexdigest(), path.stem)
                public = json.loads(data)
                self.assertEqual(set(public), {"train", "test"})
                self.assertTrue(all(set(p) == {"input", "output"} for p in public["train"]))
                self.assertTrue(all(set(p) == {"input"} for p in public["test"]))
            private = [p for p in out.rglob("*.json") if "public" not in p.relative_to(out).parts]
            self.assertTrue(private, "private episode metadata must be written separately")
            before = {str(p.relative_to(out)): p.read_bytes() for p in out.rglob("*") if p.is_file()}
            with self.assertRaises((FileExistsError, ValueError)):
                self.prototype.write_batch(episodes, out)
            self.assertEqual(before, {str(p.relative_to(out)): p.read_bytes() for p in out.rglob("*") if p.is_file()})
            changed_out = Path(directory) / "changed-private"
            self.prototype.write_batch([changed], changed_out)
            original_id = hashlib.sha256(self.public_bytes(self.episode)).hexdigest()
            self.assertEqual((changed_out / "public" / (original_id + ".json")).read_bytes(), self.public_bytes(self.episode))
            duplicate_out = Path(directory) / "duplicates"
            with self.assertRaises(ValueError):
                self.prototype.write_batch([self.episode, changed], duplicate_out)
            self.assertFalse(duplicate_out.exists(), "duplicate-visible validation must precede writing")


if __name__ == "__main__":
    unittest.main()
