"""Focused tests of the proposed edb79dae-inspired family, not production."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODULE = Path(__file__).resolve().parents[1] / "workspace/parametric/legend_templates.py"


def load():
    if not MODULE.exists():
        return None
    spec = importlib.util.spec_from_file_location("legend_templates", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LegendTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load()
        cls.source = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["edb79dae"]

    def m(self):
        self.assertIsNotNone(self.module, "proposed template family has not been implemented")
        return self.module

    def test_original_demos_match_both_policies(self):
        m = self.m()
        for pair in self.source["train"]:
            for policy in m.POLICIES:
                self.assertEqual(m.predict(pair["input"], policy), pair["output"])

    def test_query_disconnected_template_is_complete(self):
        parsed = self.m().parse_grid(self.source["test"][0]["input"])
        self.assertEqual(len(parsed["templates"][8]), 15)
        self.assertIn((0, 4), parsed["templates"][8])
        self.assertIn((1, 4), parsed["templates"][8])
        self.assertEqual(parsed["frame"], (9, 0, 29, 20))

    def test_public_demos_do_not_identify_chain_policy(self):
        m = self.m()
        fit = m.fit_rivals(self.source["train"])
        self.assertIn("once", fit)
        self.assertIn("terminal", fit)
        grid = self.source["test"][0]["input"]
        self.assertNotEqual(m.predict(grid, "once"), m.predict(grid, "terminal"))

    def test_generated_chain_teaches_parallel_original_template_lookup(self):
        m = self.m()
        grid = m.sample_input(17, 0)
        p = m.parse_grid(grid)
        self.assertEqual(len(p["mapping"]), 4)
        direct = m.predict(grid, "once")
        terminal = m.predict(grid, "terminal")
        self.assertNotEqual(direct, terminal)
        self.assertNotEqual(direct, m.predict(grid, "destination_template"))
        self.assertNotEqual(direct, m.predict(grid, "largest_component"))
        self.assertEqual(m.sample_input(17, 0), grid)

    def test_all_emitted_inputs_are_well_formed_and_vary_active_size(self):
        m = self.m()
        sizes = set()
        layouts = set()
        seen = set()
        for index in range(12):
            grid = m.sample_input(29, index)
            p = m.parse_grid(grid)
            self.assertTrue(1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30)
            self.assertTrue(all(type(v) is int and 0 <= v <= 9 for row in grid for v in row))
            sizes.add(p["tile_size"])
            layouts.add(p["frame"][1] < 3)
            seen.add(json.dumps(grid))
        self.assertEqual(sizes, {3, 4, 5})
        self.assertEqual(layouts, {False, True})
        self.assertEqual(len(seen), 12)

    def test_numeric_and_shape_validation_is_strict(self):
        m = self.m()
        for invalid in (True, 1.0, -1, 2**63):
            with self.subTest(seed=invalid), self.assertRaises(ValueError):
                m.sample_input(invalid, 0)
        for invalid in (True, -1, 1.0):
            with self.subTest(index=invalid), self.assertRaises(ValueError):
                m.sample_input(0, invalid)
        for bad in ([], [[True]], [[1, 2], [1]], [[10]]):
            with self.subTest(grid=bad), self.assertRaises(ValueError):
                m.parse_grid(bad)
        with self.assertRaises(ValueError):
            m.predict(m.sample_input(0, 0), "unknown")

    def test_cycle_is_rejected_in_shared_parameter_domain(self):
        m = self.m()
        grid = m.sample_input(17, 0)
        parsed = m.parse_grid(grid)
        last_source = next(s for s, t in parsed["mapping"].items() if t not in parsed["mapping"])
        first_source = next(s for s in parsed["mapping"] if s not in parsed["mapping"].values())
        changed = copy.deepcopy(grid)
        r, c = next((r, c) for r, c, s, t in parsed["arrows"] if s == last_source)
        for dr, dc in ((0, 2), (0, 3), (1, 3), (2, 2), (2, 3)):
            changed[r + dr][c + dc] = first_source
        with self.assertRaisesRegex(ValueError, "cycle"):
            m.parse_grid(changed)

    def test_public_identity_ignores_hidden_settings_seed_and_answers(self):
        m = self.m()
        g1, g2 = m.sample_input(17, 0), m.sample_input(17, 1)
        episode = {"train": [{"input": g1, "output": m.predict(g1, "once")}],
                   "test": [{"input": g2, "output": m.predict(g2, "once")}],
                   "settings": {"mapping_policy": "once"}, "seed": 17}
        before = m.public_challenge_bytes(episode), m.public_challenge_id(episode)
        changed = copy.deepcopy(episode)
        changed["settings"] = {"mapping_policy": "terminal"}
        changed["seed"] = 99
        changed["test"][0]["output"] = [[0]]
        self.assertEqual(before, (m.public_challenge_bytes(changed), m.public_challenge_id(changed)))
        public = json.loads(before[0])
        self.assertEqual(set(public), {"train", "test"})
        self.assertEqual(set(public["test"][0]), {"input"})

    def proposal(self):
        m = self.m()
        grids = [m.sample_input(17, i) for i in range(2)]
        e = {"train": [{"input": grids[0], "output": m.predict(grids[0], "once")}],
             "test": [{"input": grids[1], "output": m.predict(grids[1], "once")}],
             "settings": {"mapping_policy": "once"}, "seed": 17,
             "demo_count": 1, "query_count": 1,
             "program_solution": m.program("once"),
             "program_sha256": m.digest(m.program("once").encode()),
             "source_sha256": m.source_hashes()}
        e["certificate"] = m.certify(e)
        return e

    def test_writer_rejects_numeric_certificate_substitution(self):
        m = self.m()
        episode = self.proposal()
        episode["certificate"]["queries"][0]["all_demo_survivors_agree"] = 1
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "export"
            with self.assertRaises(ValueError):
                m.export_batch([episode], out)
            self.assertFalse(out.exists())

    def test_verifier_rejects_empty_export_before_runtime(self):
        m = self.m()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "public").mkdir()
            (root / "private.jsonl").write_text("")
            (root / "manifest.json").write_bytes(m.canonical({
                "schema": "edb79dae-inspired-export-v1", "status": "proposed",
                "source_sha256": m.source_hashes(), "files_sha256": {},
                "episode_count": 0, "public_ids": []}))
            with self.assertRaises(ValueError):
                m.verify_export(root, bridge=None)

    def test_certifier_rejects_boolean_and_float_count_metadata(self):
        m = self.m()
        for key, bad in (("demo_count", True), ("query_count", 1.0)):
            episode = self.proposal()
            episode[key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.certify(episode)


class LegendRacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load()
        from arc_repl.racket_bridge import RacketBridge
        cls.bridge = RacketBridge(timeout=20.0)

    @classmethod
    def tearDownClass(cls):
        cls.bridge.close()

    def test_live_labels_four_distinct_queries_and_export_replay(self):
        m = self.module
        episodes = [m.generate_episode(41, policy, 1, 4, bridge=self.bridge) for policy in m.POLICIES]
        for e in episodes:
            self.assertEqual((len(e['train']), len(e['test'])), (1, 4))
            self.assertEqual(e['certificate']['survivors'], [e['settings']['mapping_policy']])
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "export"
            m.export_batch(episodes, out)
            self.assertEqual(m.verify_export(out, bridge=self.bridge)['racket_labels_replayed'], 10)
            manifest = json.loads((out / 'manifest.json').read_text())
            del manifest['files_sha256']['private.jsonl']
            (out / 'manifest.json').write_bytes(m.canonical(manifest))
            with self.assertRaises(ValueError):
                m.verify_export(out, bridge=self.bridge)

    def test_counts_fail_without_silent_shortfall(self):
        m = self.module
        for key, bad in (("demos", 0), ("demos", True), ("queries", 0), ("queries", 4.0), ("max_attempts", 0)):
            args = dict(seed=17, policy='once', demos=2, queries=4, max_attempts=32, bridge=self.bridge)
            args[key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.generate_episode(**args)


if __name__ == "__main__":
    unittest.main()
