"""Task-local proposed metric variant; distinct from canonical generator tests."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import unittest

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
TASK = "2e663d812b7a"
PROTOTYPE = ROOT / "generators" / TASK / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "The runnable task-local parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("metric_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_prototype_exists():
    assert PROTOTYPE.is_file(), "The runnable task-local parametric prototype is missing"


def check_default_program_is_exact_canonical_text(proto):
    original = proto.canonical_program()
    assert proto.materialize_program("chebyshev") == original
    assert proto.materialize_program("manhattan") == original.replace(
        "(max (abs (- r seed-r)) (abs (- c seed-c)))",
        "(+ (abs (- r seed-r)) (abs (- c seed-c)))",
    )
    with unittest.TestCase().assertRaisesRegex(ValueError, "ring_metric"):
        proto.materialize_program("euclidean")


def check_metric_changes_body_but_preserves_boundary_reporting(proto, runner):
    grid = proto.make_input(16, 16, [2, 3, 3, 0, 4, 6], (3, 8))
    square = runner.run(proto.materialize_program("chebyshev"), grid)
    diamond = runner.run(proto.materialize_program("manhattan"), grid)
    assert square != diamond
    assert square[5][9] == 3 and diamond[5][9] == 0
    assert square[0] == diamond[0] == [2, 3, 5, 0, 5, 5] + [0] * 10
    assert square[1] == diamond[1] == [5] * 16
    assert square[3][8] == diamond[3][8] == 2
    assert square[7][8] == diamond[7][8] == 4


def check_default_matches_actual_racket_and_stored_canonical_answers(proto, runner):
    canonical = proto.canonical_program()
    default = proto.materialize_program("chebyshev")
    pairs = canonical_pairs(TASK, root=ROOT)
    assert pairs
    for pair in pairs:
        actual = runner.run(canonical, pair["input"])
        assert actual == pair["output"]
        assert runner.run(default, pair["input"]) == actual


def check_episode_uses_one_setting_and_distinguishes_declared_rivals(proto, runner, seed, metric):
    episode = proto.build_episode(seed, runner)
    assert episode["ring_metric"] == metric
    assert len(episode["pairs"]) == 4
    assert episode["identifiability"]["status"] == "pass"
    assert episode["identifiability"]["query_changing_survivors"] == []
    assert episode["identifiability"]["refuted_rival_count"] == 10
    for pair in episode["pairs"]:
        assert pair["output"] == runner.run(proto.materialize_program(metric), pair["input"])
    query = episode["pairs"][-1]
    assert (len(query["input"]), len(query["input"][0])) == (30, 30)
    assert len(proto.parse_input(query["input"])["key"]) >= 16
    assert max(len(p["input"]) for p in episode["pairs"][:-1]) < 30
    assert episode == proto.build_episode(seed, runner)


def check_explicit_setting_keeps_seeded_inputs_identical(proto, runner):
    a = proto.build_episode(204, runner, ring_metric="chebyshev")
    b = proto.build_episode(204, runner, ring_metric="manhattan")
    assert [p["input"] for p in a["pairs"]] == [p["input"] for p in b["pairs"]]
    assert any(x["output"] != y["output"] for x, y in zip(a["pairs"], b["pairs"]))
    assert a["ring_metric"] == "chebyshev" and b["ring_metric"] == "manhattan"


def check_public_challenge_excludes_hidden_fields_and_query_answers(proto, runner):
    episode = proto.build_episode(20, runner)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    assert public["test"][0]["input"] == episode["pairs"][-1]["input"]
    serialized = json.dumps(public)
    for forbidden in ("ring_metric", "program", "seed", "rivals", "reference"):
        assert forbidden not in serialized


def check_identity_demos_fail_to_identify_a_metric_sensitive_query(proto, runner):
    identity = proto.make_input(9, 9, [2], (5, 4))
    query = proto.make_input(16, 16, [2, 3, 3, 0, 4, 6], (3, 8))
    inputs = [identity, identity, identity, query]
    by_metric = {
        metric: [runner.run(proto.materialize_program(metric), grid) for grid in inputs]
        for metric in proto.ALLOWED_METRICS
    }
    report = proto.identifiability(inputs, by_metric, "chebyshev")
    assert report["status"] == "ambiguous"
    assert "setting:manhattan" in report["query_changing_survivors"]


def check_boundary_inputs_are_lawful_and_authority_preserving(proto, runner, height, width, seed):
    grid = proto.make_input(height, width, [2, 3, 0, 4, 6], seed)
    parts = proto.parse_input(grid)
    assert (parts["height"], parts["width"]) == (height, width)
    default = runner.run(proto.materialize_program("chebyshev"), grid)
    assert default == runner.run(proto.canonical_program(), grid)
    for metric in proto.ALLOWED_METRICS:
        assert runner.run(proto.materialize_program(metric), grid) == proto.rival_model(grid, metric)


def check_bad_episode_seed_is_rejected(proto, bad):
    with unittest.TestCase().assertRaisesRegex(ValueError, "seed"):
        proto.episode_inputs(bad)



class PrototypePresenceTests(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(PROTOTYPE.is_file(), "The runnable task-local parametric prototype is missing")


class ParametricPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proto = load_prototype()
        cls.runner = cls.proto.ReferenceRunner()

    @classmethod
    def tearDownClass(cls):
        cls.runner.close()

    def test_program(self):
        check_default_program_is_exact_canonical_text(self.proto)

    def test_metric_effect(self):
        check_metric_changes_body_but_preserves_boundary_reporting(self.proto, self.runner)

    def test_canonical_authority(self):
        check_default_matches_actual_racket_and_stored_canonical_answers(self.proto, self.runner)

    def test_episodes(self):
        for seed, metric in [(2026102300, "chebyshev"), (2026102301, "manhattan")]:
            with self.subTest(seed=seed, metric=metric):
                check_episode_uses_one_setting_and_distinguishes_declared_rivals(self.proto, self.runner, seed, metric)

    def test_setting_independent_inputs(self):
        check_explicit_setting_keeps_seeded_inputs_identical(self.proto, self.runner)

    def test_public_separation(self):
        check_public_challenge_excludes_hidden_fields_and_query_answers(self.proto, self.runner)

    def test_ambiguity_detection(self):
        check_identity_demos_fail_to_identify_a_metric_sensitive_query(self.proto, self.runner)

    def test_domain_boundaries(self):
        for height, width, seed in [(9, 9, (2, 0)), (30, 30, (29, 29)), (30, 9, (15, 4))]:
            with self.subTest(height=height, width=width, seed=seed):
                check_boundary_inputs_are_lawful_and_authority_preserving(self.proto, self.runner, height, width, seed)

    def test_invalid_seeds(self):
        for bad in [True, -1, "21", 1.5]:
            with self.subTest(seed=bad):
                check_bad_episode_seed_is_rejected(self.proto, bad)

    def test_existing_output_is_refused_without_changing_any_bytes(self):
        with TemporaryDirectory(prefix="arc-parametric-existing-") as directory:
            destination = Path(directory) / "prior-evidence"
            (destination / "public").mkdir(parents=True)
            (destination / "public/episode-0001.json").write_bytes(b'{"prior_episode":true}\n')
            (destination / "report.json").write_bytes(b'prior report\n')
            before = {str(p.relative_to(destination)): p.read_bytes()
                      for p in destination.rglob("*") if p.is_file()}
            before_directories = {str(p.relative_to(destination))
                                  for p in destination.rglob("*") if p.is_dir()}
            with self.assertRaisesRegex(FileExistsError, "not empty"):
                self.proto.build_bundle(destination, [2026102300])
            after = {str(p.relative_to(destination)): p.read_bytes()
                     for p in destination.rglob("*") if p.is_file()}
            after_directories = {str(p.relative_to(destination))
                                 for p in destination.rglob("*") if p.is_dir()}
            self.assertEqual(after, before)
            self.assertEqual(after_directories, before_directories)


if __name__ == "__main__":
    unittest.main(verbosity=2)
