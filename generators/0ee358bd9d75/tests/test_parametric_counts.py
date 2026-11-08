"""Native count, teaching, and per-turn export contracts for this prototype."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


ROOT = find_root(__file__)
HOME = ROOT / "generators/0ee358bd9d75/workspace/parametric"


def load(name):
    path = HOME / (name + ".py")
    spec = importlib.util.spec_from_file_location("_frequency_counts_" + name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def pixel_answers(grid):
    """Independent pixel readout; no sampler section metadata or predictions."""
    rows = [-1] + [r for r, row in enumerate(grid) if not any(row)] + [len(grid)]
    cols = [-1] + [c for c in range(len(grid[0])) if not any(row[c] for row in grid)] + [len(grid[0])]
    answers = {key: [] for key in ("most_frequent", "least_frequent", "first", "last", "min", "max")}
    for top, bottom in zip(rows, rows[1:]):
        out = {key: [] for key in answers}
        for left, right in zip(cols, cols[1:]):
            cells = [grid[r][c] for r in range(top + 1, bottom)
                     for c in range(left + 1, right) if grid[r][c]]
            counts = Counter(cells)
            most = [color for color in counts if counts[color] == max(counts.values())]
            least = [color for color in counts if counts[color] == min(counts.values())]
            if len(most) != 1 or len(least) != 1:
                raise AssertionError("frequency tie in generated support")
            values = {"most_frequent": most[0], "least_frequent": least[0],
                      "first": cells[0], "last": cells[-1], "min": min(cells), "max": max(cells)}
            for key in out:
                out[key].append(values[key])
        for key in answers:
            answers[key].append(out[key])
    return answers


class ParametricCountsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = load("prototype")

    def inputs(self, seed, demos, queries):
        try:
            return self.prototype.sample_inputs(seed, demos=demos, queries=queries)
        except TypeError as error:
            self.fail(f"independent demo/query requests are unsupported: {error}")

    def test_independent_counts_preserve_prefixes_and_distinct_inputs(self):
        for seed in (0, 17, 50001):
            full = self.inputs(seed, 6, 4)
            self.assertEqual(len(full), 10)
            self.assertEqual(len({json.dumps(grid) for grid in full}), 10)
            for demos, queries in ((2, 1), (2, 4), (3, 1), (3, 4), (6, 1)):
                actual = self.inputs(seed, demos, queries)
                self.assertEqual(len(actual), demos + queries)
                self.assertEqual(actual[:demos], full[:demos])
                self.assertEqual(actual[demos:], full[6:6 + queries])
            self.assertEqual(self.prototype.sample_inputs(seed), self.inputs(seed, 3, 1))

    def test_each_demo_refutes_shortcuts_for_both_settings(self):
        for seed in (*range(12), 306, 413, *range(50000, 50012)):
            for grid in self.inputs(seed, 6, 4)[:6]:
                answers = pixel_answers(grid)
                for setting in ("most_frequent", "least_frequent"):
                    rivals = [key for key in answers if key != setting]
                    self.assertTrue(all(answers[setting] != answers[rival] for rival in rivals),
                                    (seed, setting, answers))

    def test_minimum_support_and_full_canvas_query_are_substantive(self):
        for seed in (0, 1, 17, 50001):
            inputs = self.inputs(seed, 2, 4)
            self.assertEqual((len(inputs[0]), len(inputs[0][0])), (8, 8))
            query = inputs[2]
            self.assertEqual((len(query), len(query[0])), (30, 30))
            self.assertGreaterEqual(sum(cell != 0 for row in query for cell in row), 280)
            info = self.prototype.validate_input(query, require_mixed=True)
            self.assertGreaterEqual(len(info["sections"]), 4)
            for section in info["sections"]:
                self.assertGreaterEqual(len(section["counts"]), 2)

    def test_invalid_counts_reject_exact_type_and_bounds(self):
        for field, values in (("demos", (True, False, 1, 7, 3.0, "3")),
                              ("queries", (True, False, 0, 5, 1.0, "1"))):
            for value in values:
                controls = {"demos": 3, "queries": 1, field: value}
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        self.prototype.sample_inputs(17, **controls)


class ParametricCountsRacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = load("prototype")
        cls.bridge = RacketBridge()

    @classmethod
    def tearDownClass(cls):
        cls.bridge.close()

    def episode(self, seed, selection, demos, queries):
        try:
            return self.prototype.generate_episode(seed, selection=selection, demos=demos,
                                                   queries=queries, bridge=self.bridge)
        except TypeError as error:
            self.fail(f"independent labeled demo/query requests are unsupported: {error}")

    def test_racket_labels_cover_both_settings_and_count_boundaries(self):
        for seed, demos, queries in ((0, 2, 4), (17, 6, 4)):
            episodes = [self.episode(seed, selection, demos, queries)
                        for selection in ("most_frequent", "least_frequent")]
            self.assertEqual([p["input"] for p in episodes[0]["train"] + episodes[0]["test"]],
                             [p["input"] for p in episodes[1]["train"] + episodes[1]["test"]])
            for episode in episodes:
                self.assertEqual(len(episode["train"]), demos)
                self.assertEqual(len(episode["test"]), queries)
                for pair in episode["train"] + episode["test"]:
                    self.assertEqual(pair["output"], pixel_answers(pair["input"])[episode["selection"]])

    def test_per_turn_projection_has_no_future_queries_or_private_fields(self):
        for selection in ("most_frequent", "least_frequent"):
            full = self.episode(17, selection, 2, 4)
            stopped = self.episode(17, selection, 2, 1)
            before = deepcopy(full)
            self.assertTrue(callable(getattr(self.prototype, "public_turn", None)),
                            "a one-query public projection is required")
            first = self.prototype.public_turn(full, 0)
            self.assertEqual(public_challenge_bytes(first),
                             public_challenge_bytes(self.prototype.public_turn(stopped, 0)))
            self.assertEqual(public_challenge_id(first),
                             public_challenge_id(self.prototype.public_turn(stopped, 0)))
            for index in range(4):
                turn = self.prototype.public_turn(full, index)
                self.assertEqual(set(turn), {"train", "test"})
                self.assertEqual(turn["train"], full["train"])
                self.assertEqual(turn["test"], [{"input": full["test"][index]["input"]}])
                self.assertEqual(hashlib.sha256(public_challenge_bytes(turn)).hexdigest(),
                                 public_challenge_id(turn))
            first["train"][0]["input"][0][0] = 99
            self.assertEqual(full, before)
            for invalid in (-1, 4, True, 0.0):
                with self.assertRaises(ValueError):
                    self.prototype.public_turn(full, invalid)

    def test_public_writer_only_publishes_first_turn_under_visible_hash(self):
        episode = self.episode(50001, "least_frequent", 3, 4)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "export"
            self.assertTrue(callable(getattr(self.prototype, "write_episode", None)),
                            "a strict public/private writer is required")
            self.prototype.write_episode(episode, output)
            visible = self.prototype.public_turn(episode, 0)
            public_files = list((output / "public").iterdir())
            self.assertEqual([path.name for path in public_files], [public_challenge_id(visible) + ".json"])
            self.assertEqual(public_files[0].read_bytes(), public_challenge_bytes(visible))
            private = json.loads((output / "private" / "episode.json").read_text())
            self.assertEqual(private, episode)
            self.assertEqual((output / "private" / "program.rkt").read_text(), episode["program"])
            self.assertEqual(set(path.name for path in output.iterdir()), {"public", "private"})
            with self.assertRaises(FileExistsError):
                self.prototype.write_episode(episode, output)


class NativeAdapterTests(unittest.TestCase):
    def adapter(self):
        try:
            return load("adapter")
        except FileNotFoundError as error:
            self.fail(f"native exact-adjacent adapter is missing: {error}")

    def test_adapter_ignores_an_unrelated_cached_prototype(self):
        with patch.dict("sys.modules", {"prototype": object()}):
            adapter = self.adapter()
            emitted = adapter.generate(306, {"selection": "least_frequent"}, 2, 4)
        self.assertEqual(len(emitted["train"]), 2)
        self.assertEqual(len(emitted["test"]), 4)
        self.assertEqual(emitted["program_solution"], (HOME / "programs/least_frequent.rkt").read_text())
        for pair in emitted["train"] + emitted["test"]:
            self.assertEqual(pair["output"], pixel_answers(pair["input"])["least_frequent"])

    def test_adapter_rejects_undeclared_settings_and_count_coercion(self):
        adapter = self.adapter()
        for settings in (None, {}, {"selection": True}, {"selection": "auto"},
                         {"selection": "most_frequent", "extra": 1}):
            with self.assertRaises(ValueError):
                adapter.program(settings)
        for demos, queries in ((1, 1), (7, 1), (3, 0), (3, 5), (True, 4), (2, 1.0)):
            with self.assertRaises(ValueError):
                adapter.generate(17, {"selection": "most_frequent"}, demos, queries)


if __name__ == "__main__":
    unittest.main()
