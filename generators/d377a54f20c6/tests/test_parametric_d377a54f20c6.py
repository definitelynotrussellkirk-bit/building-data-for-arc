"""Focused tests for the proposed prototype; not canonical production coverage."""
from __future__ import annotations

import copy
from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/d377a54f20c6/workspace/parametric/episode.py"
_MODULE = None


def prototype():
    global _MODULE
    assert PROTOTYPE.is_file(), "parametric episode implementation has not been written"
    if _MODULE is None:
        spec = importlib.util.spec_from_file_location("parametric_d377a54f20c6", PROTOTYPE)
        _MODULE = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _MODULE
        spec.loader.exec_module(_MODULE)
    return _MODULE


def rectangle(height=7, width=13):
    grid = [[0] * (width + 2) for _ in range(height + 2)]
    for row in range(1, height + 1):
        grid[row][1:width + 1] = [2] * width
    grid[1][1] = 5  # A border marker must become the majority-color frame.
    return grid


def expected_rectangle(interior_rows):
    rows = ["000000000000000", "022222222222220"]
    rows += ["02" + row + "20" for row in interior_rows]
    rows += ["022222222222220", "000000000000000"]
    return [[int(value) for value in row] for row in rows]


class ParametricTests(unittest.TestCase):
    def test_four_settings_have_independent_literal_racket_outputs(self):
        m = prototype()
        rows = {
            (True, 1): ["50000000005", "05000000050", "00555555500", "05000000050", "50000000005"],
            (False, 1): ["50000000005", "05000000050", "00500000500", "05000000050", "50000000005"],
            (True, 2): ["55000000055", "55500000555", "05555555550", "55500000555", "55000000055"],
            (False, 2): ["55000000055", "55500000555", "05550005550", "55500000555", "55000000055"],
        }
        with m.RacketBridge() as bridge:
            for key, expected_rows in rows.items():
                got = m.apply_rule(bridge, [rectangle()], m.Parameters(*key))[0]
                self.assertEqual(got, expected_rectangle(expected_rows), key)

    def test_original_setting_is_exact_official_source_and_all_canonical_pairs(self):
        m = prototype()
        records = []
        with canonical_path(ROOT).open() as handle:
            for line in handle:
                if '"d377a54f20c6"' in line:
                    row = json.loads(line)
                    if row.get("task_id") == "d377a54f20c6":
                        records.append(row)
        self.assertTrue(records)
        pairs = canonical_pairs("d377a54f20c6", root=ROOT)
        for record in records:
            self.assertEqual(m.rule_source(), record["program_solution"])
        with m.RacketBridge() as bridge:
            actual = m.apply_rule(bridge, [pair["input"] for pair in pairs])
        self.assertEqual(actual, [pair["output"] for pair in pairs])

    def test_each_episode_has_identified_rule_distinct_queries_and_fixed_parameters(self):
        m = prototype()
        with m.RacketBridge() as bridge:
            for parameters in m.ALL_SETTINGS:
                episode = m.generate_episode(17, parameters=parameters, bridge=bridge)
                self.assertEqual(len(episode["train"]), 3)
                self.assertEqual(len(episode["test"]), 4)
                self.assertEqual(episode["parameters"], parameters.as_dict())
                pairs = episode["train"] + episode["test"]
                inputs = [json.dumps(pair["input"]) for pair in pairs]
                self.assertEqual(len(set(inputs)), 7)
                self.assertEqual(m.infer_settings(bridge, episode["train"]), [parameters])
                self.assertEqual(m.apply_rule(bridge, [p["input"] for p in pairs], parameters),
                                 [p["output"] for p in pairs])
                self.assertEqual(episode["identifiability"]["survivors"], [parameters.as_dict()])
                self.assertEqual(len(episode["identifiability"]["eliminations"]), 3)
                self.assertTrue(all(q["identified_from_demonstrations"] for q in episode["identifiability"]["queries"]))
                self.assertIn((30, 30), [(len(p["input"]), len(p["input"][0])) for p in episode["test"]])

    def test_square_demonstration_does_not_falsely_identify_center_extension(self):
        m = prototype()
        grid = rectangle(7, 7)
        with m.RacketBridge() as bridge:
            label = m.apply_rule(bridge, [grid])[0]
            survivors = m.infer_settings(bridge, [{"input": grid, "output": label}])
        self.assertEqual(set(survivors), {m.Parameters(False, 1), m.Parameters(True, 1)})

    def test_seed_reproducibility_count_controls_and_no_global_random_mutation(self):
        m = prototype()
        import random
        state = random.getstate()
        with m.RacketBridge() as bridge:
            first = m.generate_episode(91, demo_count=1, query_count=2, bridge=bridge)
            second = m.generate_episode(91, demo_count=1, query_count=2, bridge=bridge)
            different = m.generate_episode(92, demo_count=1, query_count=2, bridge=bridge)
        self.assertEqual(first, second)
        self.assertNotEqual(first["train"], different["train"])
        self.assertEqual((len(first["train"]), len(first["test"])), (1, 2))
        self.assertEqual(random.getstate(), state)

    def test_invalid_parameters_counts_and_inputs_fail_before_execution(self):
        m = prototype()
        for values in [(1, 1), (True, True), (False, 0), (True, 3)]:
            with self.assertRaises(ValueError):
                m.Parameters(*values)
        for values in [{"demo_count": 0}, {"query_count": 0}, {"query_count": 17}, {"demo_count": True}]:
            with self.assertRaises(ValueError):
                m.generate_episode(17, **values)
        for grid in [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 7 for _ in range(7)], [[2] * 7 for _ in range(7)]]:
            with self.assertRaises(ValueError):
                m.validate_input(grid)
        hole = rectangle()
        hole[3][3] = 0
        with self.assertRaises(ValueError):
            m.validate_input(hole)

    def test_public_payload_and_identity_ignore_all_private_metadata_and_query_answers(self):
        m = prototype()
        with m.RacketBridge() as bridge:
            episode = m.generate_episode(23, bridge=bridge)
        expected = {
            "train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(p["input"])} for p in episode["test"]],
        }
        self.assertEqual(m.public_challenge(episode), expected)
        name = m.public_identifier(episode)
        changed = copy.deepcopy(episode)
        changed["seed"] = -123
        changed["parameters"] = {"invented": "private"}
        changed["reference"] = {"source": "private mutation"}
        changed["source_hashes"] = {"private": "changed"}
        changed["identifiability"] = {"private": "changed"}
        changed["test"][0]["output"][0][0] = 9
        self.assertEqual(m.public_identifier(changed), name)
        self.assertEqual(m.public_challenge(changed), expected)
        changed["train"][0]["output"][0][0] = 9
        self.assertNotEqual(m.public_identifier(changed), name)
        self.assertRegex(name, r"^challenge_[0-9a-f]{24}$")

    def test_cli_rejects_nonempty_output_directory_before_racket(self):
        m = prototype()
        with tempfile.TemporaryDirectory(prefix="arc-parametric-guard-") as directory:
            output = Path(directory)
            original = {
                "private/manifest.json": b'{"previous_export":true}\n',
                "private/witness.json": b'{"previous_witness":true}\n',
                "public/challenge_0123456789abcdef01234567.json": b'{"train":[],"test":[]}\n',
            }
            for relative, contents in original.items():
                path = output / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)
            stderr = io.StringIO()
            with mock.patch.object(m, "RacketBridge", side_effect=AssertionError("Racket started before output-directory rejection")) as bridge:
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
                    m.main(["--out", str(output)])
                self.assertEqual(error.exception.code, 2)
                bridge.assert_not_called()
            self.assertIn("new or empty directory", stderr.getvalue())
            retained = {str(path.relative_to(output)): path.read_bytes()
                        for path in output.rglob("*") if path.is_file()}
            self.assertEqual(retained, original)

    def test_cli_accepts_new_or_empty_output_directory(self):
        m = prototype()
        with tempfile.TemporaryDirectory(prefix="arc-parametric-guard-") as directory:
            for name, existing in (("new", False), ("empty", True)):
                with self.subTest(existing=existing):
                    output = Path(directory) / name
                    if existing:
                        output.mkdir()
                    with mock.patch.object(m, "RacketBridge", side_effect=RuntimeError("stopped at runtime boundary")) as bridge:
                        with self.assertRaisesRegex(RuntimeError, "stopped at runtime boundary"):
                            m.main(["--out", str(output)])
                        bridge.assert_called_once_with()
                    self.assertEqual(output.exists(), existing)
                    if existing:
                        self.assertEqual(list(output.iterdir()), [])

    def test_cli_exports_four_settings_with_opaque_public_paths(self):
        prototype()
        with tempfile.TemporaryDirectory(prefix="arc-parametric-test-") as directory:
            result = subprocess.run(
                [sys.executable, str(PROTOTYPE), "--seed", "17", "--all-settings", "--demos", "2", "--queries", "4", "--out", directory],
                cwd=ROOT, env=os.environ.copy(), text=True, capture_output=True, timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["episode_count"], 4)
            public_paths = sorted((Path(directory) / "public").glob("*.json"))
            self.assertEqual(len(public_paths), 4)
            for path in public_paths:
                self.assertRegex(path.name, r"^challenge_[0-9a-f]{24}\.json$")
                public = json.loads(path.read_text())
                self.assertEqual(set(public), {"train", "test"})
                self.assertEqual((len(public["train"]), len(public["test"])), (2, 4))
                self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
                private = json.loads((Path(directory) / "private" / path.name).read_text())
                self.assertEqual(private["reference"]["sha256"], hashlib.sha256(private["reference"]["source"].encode()).hexdigest())
            witness = json.loads((Path(directory) / "private/witness.json").read_text())
            self.assertEqual(len(witness["pairwise_differences"]), 6)
            self.assertTrue(all(row["different_cells"] > 0 for row in witness["pairwise_differences"]))


if __name__ == "__main__":
    unittest.main()
